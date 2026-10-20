## Context

O RFC-001 propõe extrair dados de vendas do Tesouro Direto do portal Tesouro Transparente (CKAN). A versão original descrevia uma classe monolítica com `requests`, `BeautifulSoup`, `pandas` e scraping HTML, incompatível com o estado atual do projeto.

O `b3-selic-pre` hoje:

- usa Clean Architecture em 4 camadas, com guardas automáticas de dependência (`tests/test_architecture.py`);
- usa apenas `urllib` para HTTP e `csv`/`json` da biblioteca padrão;
- tem cache em disco com escrita atômica, validação de completude e leitura somente leitura (`DiskCache`, `cache_payload.write_atomic`);
- tem contrato `CommunicationError` para falhas de rede/HTTP e logging compartilhado;
- tem CLI baseada em subcomandos de verbo, sem flags legadas no nível raiz;
- tem GUI em janela única, com gráfico, sidebar, statusbar, escudo de inicialização e orçamento de testes de UI;
- tem servidor MCP somente leitura, sem rede durante o atendimento.

O spike de descoberta foi concluído em 2026-10-20. O dataset `vendas-do-tesouro-direto` contém apenas vendas, com seis colunas e formato confirmado. Resgates e estoque são datasets separados e ficam fora desta change.

## Spike Results

Resumo; evidências completas no RFC-001 renomeado:

- dataset: `vendas-do-tesouro-direto` (`f0468ecc-ae97-4287-89c2-6d8139fb4343`);
- CSV: `e5f90e3a-8f8d-4895-9c56-4bb2f7877920`, 7.488.603 bytes;
- cabeçalho: `Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;PU;Quantidade;Valor`;
- ASCII/UTF-8 sem BOM, delimitador `;`, decimal vírgula, datas `DD/MM/YYYY`, LF;
- 101.331 registros, 6.129 datas, 9 títulos, 2002-01-04 a 2026-10-14;
- `ETag`, `Last-Modified` e `304` funcionam; sem `Content-Length`, com `Content-Range`;
- download de ~29 s; portal instável, retry obrigatório;
- dados não ordenados, duplicatas legítimas, revisões possíveis, defasagem de até dois dias úteis.

## Goals / Non-Goals

**Goals:**

- Reestruturar a feature em capabilities comportamentais, não em camadas.
- Usar a API CKAN JSON para descoberta do dataset, sem scraping HTML.
- Usar `urllib`, `csv`, `json`, `decimal`, `unicodedata` e `hashlib`.
- Implementar cache cumulativo com escrita atômica em bytes, TTL de 6 horas e validação antes de substituir a versão anterior.
- Implementar o subcomando `tesouro` na CLI, com período padrão de 30 dias, `--agregar` e `--json`.
- Implementar uma janela separada "Tesouro Direto" na GUI, com período padrão de 12 meses e limite de 5.000 linhas.
- Reutilizar os padrões existentes de XDG, retry, logging, erros e formatação.
- Manter testes headless para as regras e testes de UI apenas para montagem/wiring.

**Non-Goals:**

- Resgates e estoque nesta change.
- Investidores, operações e taxas dos títulos.
- Tools MCP para Tesouro.
- Exportação Tesouro no subcomando `exportar` ou botão de cópia dedicado.
- Gráficos de movimentação.
- Banco de dados (PostgreSQL/SQLite).
- Agendamento/cron.
- Cruzamento com a curva SELIC.
- Atualização do PRD antes da implementação.
- Outros datasets do Tesouro Transparente.

## Decisions

### 1. CKAN JSON em vez de scraping HTML

**Decisão:** usar `GET /api/3/action/package_show?id=vendas-do-tesouro-direto` para obter metadados e a URL do recurso CSV.

- Validar `success: true`.
- Exigir exatamente um recurso com `format == "CSV"`.
- Levantar `TesouroDataError` se o CSV não existir.
- Não consumir o PDF de metadados.

**Alternativa rejeitada:** scraping com `BeautifulSoup`. É frágil, exige dependência externa e foi a fonte dos problemas da proposta original.

**Racional:** a API CKAN retorna JSON estruturado e é o caminho documentado do portal. O parsing usa `json.loads()`, já usado na infraestrutura.

### 2. `urllib` + `csv` + `json` nativos

**Decisão:** download com `urllib.request`, leitura em chunks, parsing com `csv`, `Decimal` para valores e `json` para metadados.

**Alternativa rejeitada:** `requests`, `pandas` e `lxml`. Aumentam o binário e não são usados pelo projeto.

**Racional:** reduz dependências, mantém o padrão de injeção de `opener` e permite testar sem rede.

### 3. Cache cumulativo de arquivo único

**Decisão:** manter um CSV cumulativo (`vendastesourodireto.csv`) e um arquivo de metadados no diretório `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`.

- TTL de 6 horas baseado em `checked_at`.
- Download condicional com `ETag`/`If-Modified-Since`; `304` reutiliza o cache e atualiza apenas `checked_at`.
- Download para arquivo temporário, validação e substituição atômica em **bytes** via `write_atomic_bytes` (ou generalização de `cache_payload.write_atomic`).
- Se o download falhar, a versão válida anterior é preservada.
- Metadados incluem `schema_version`, `dataset_name`, `dataset_id`, `resource_id`, `resource_url`, `etag`, `last_modified`, `downloaded_at`, `checked_at`, `size_bytes`, `sha256`, `row_count`, `first_data_date` e `last_data_date`.
- Sem housekeeping: o dataset é cumulativo e basta a última versão.
- Leitura somente leitura para consumidores que não devem alterar o cache.
- Um novo arquivo com menos linhas é aceito, mas gera aviso de revisão.

**Alternativa rejeitada:** cache por data de download e housekeeping copiados do `DiskCache`. Não fazem sentido para um arquivo cumulativo.

### 4. Modelo de domínio confirmado

**Decisão:** definir um frozen dataclass `VendaTesouroDireto` com:

| Campo | Tipo |
| --- | --- |
| `tipo_titulo` | `str` |
| `vencimento` | `str` ISO |
| `data_liquidacao` | `str` ISO |
| `pu` | `Decimal` |
| `quantidade` | `Decimal` |
| `valor` | `Decimal` |

- `data_liquidacao` é a data de liquidação (D+1 da operação), não a data da venda.
- Não há `venda`, `resgate` ou `saldo` neste dataset.
- Não há chave natural única; duplicatas são preservadas.

**Racional:** segue o padrão de `RateRecord`, mas usa `Decimal` para evitar erro de arredondamento em somas financeiras. Datas em ISO mantêm ordenação lexical e serialização simples.

**Trade-off:** `Decimal` exige conversão explícita na formatação, mas é o tipo adequado para valores monetários e quantidades.

### 5. Parsing e validação

**Decisão:**

- Decodificar `utf-8-sig`, depois `utf-8` e, por fim, `latin-1`.
- Usar `;` como delimitador; não usar `csv.Sniffer` porque o decimal com vírgula confunde a detecção.
- Exigir o cabeçalho confirmado, mapeando nomes sem caixa/acentos.
- Exigir as seis colunas; ignorar colunas extras com aviso.
- Converter datas `DD/MM/YYYY` para ISO.
- Converter decimais com vírgula para `Decimal`; aceitar ponto como separador de milhar quando houver vírgula.
- Reportar linha e coluna em erros.
- CSV vazio ou sem registros gera `TesouroDataError` e não é cacheado.
- Validar o CSV completo antes de substituir o cache.

**Racional:** o schema é estável e conhecido; validar cedo evita cachear arquivo truncado ou incompatível.

### 6. Filtros, agregação e ordenação

**Decisão:**

- `filtrar_por_titulo`: parcial, sem caixa/acentos, sobre `tipo_titulo`.
- `filtrar_por_periodo`: inclusivo, sobre `data_liquidacao`.
- `agregar_por_titulo`: somar `quantidade` e `valor`; calcular `PU` médio ponderado por `valor / quantidade`.
- Ordenação determinística: `data_liquidacao` desc, `tipo_titulo` asc, `vencimento` asc, `pu` asc.
- `PU` não é aditivo; nunca somar `PU`.

**Racional:** os dados não estão ordenados e há duplicatas legítimas; a ordenação e a agregação precisam ser explícitas.

### 7. CLI: subcomando `tesouro`

**Decisão:**

```text
b3-selic-pre tesouro [--titulo T] [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD]
                     [--agregar] [--json] [--no-cache]
```

- `--inicio`/`--fim`: datas ISO exatas, inclusivas, sem `nearest_business_day`.
- Sem filtros: últimos 30 dias relativos à maior `data_liquidacao` disponível.
- `--inicio > --fim`: erro de uso, código `2`.
- `--agregar`: CSV/JSON agregado por título.
- `--json`: metadados e registros/agregados.
- `--no-cache`: força verificação na rede; `304` reutiliza o cache.
- Saída padrão em CSV com delimitador `;` e separador decimal `.`.
- Período vazio: cabeçalho apenas, código `0`.
- Códigos: `0` sucesso, `1` falha de comunicação/dados, `2` uso/validação.
- Nenhuma flag no nível raiz.

**Alternativa rejeitada:** `--tesouro` como flag raiz. Contradiz `cli-interface`.

### 8. GUI: janela separada

**Decisão:** adicionar um botão "Tesouro Direto" na barra superior e abrir uma janela `Toplevel` independente, com tabela, filtros, botão de atualização e status próprio.

- Botão com ícone e tooltip; incluído nos widgets bloqueados pelo escudo de inicialização.
- Janela única: segundo clique foca a existente.
- Ao abrir, carrega o cache válido; se não houver, orienta "clique em Atualizar", sem download automático.
- Tabela `ttk.Treeview` com colunas `Tipo`, `Vencimento`, `Liquidação`, `PU`, `Quantidade`, `Valor`.
- Datas `DD/MM/YYYY`; números com vírgula.
- Período padrão de 12 meses; limite de 5.000 linhas exibidas.
- Progresso indeterminado; sem percentual, pois não há `Content-Length`.
- "Atualizar" usa cache; "Ignorar cache" faz requisição condicional.
- Fechar durante download não pode gerar exceção.
- Status com origem, instante da extração, maior `data_liquidacao` e contagem.

**Alternativa rejeitada:** aba em `ttk.Notebook` na janela principal. Introduzir abas na janela principal exigiria reestruturar o gráfico e arriscaria o escudo de inicialização. Um `Notebook` dentro do `Toplevel` do Tesouro seria aceitável no futuro, para resgates/estoque.

### 9. Erros e logging

**Decisão:**

- `CommunicationError` para rede, HTTP, timeout, corpo vazio/parcial e resposta cujo `Content-Type` não comece por `text/csv`.
- `TesouroDataError` para CSV malformado, colunas ausentes, datas/valores inválidos e CSV vazio.
- Erro de validação de período é erro de uso (`ValueError`/`PeriodoInvalidoError`), código `2`.
- Falhas esperadas em linha única no log; exceções inesperadas com traceback.
- CLI em `stderr` com código `1` ou `2`; GUI mostra a mensagem na janela e permanece utilizável.

### 10. Reuso de infraestrutura existente

- `xdg.cache_base()` para o diretório base.
- `cache_payload.write_atomic_bytes()` (novo) ou generalização de `write_atomic` para bytes.
- `b3_retry.retry_transient()` (novo) para rede/5xx/429/corpo parcial.
- `application/formatting.py` para padrões de CSV e formatação; helpers específicos em `application/tesouro/_formatting.py`.
- `ActionLock` com caminho dedicado `.../tesouro.lock` para não bloquear atualizações da B3.
- `application/errors.CommunicationError`.
- `GuiDependencies` e `gui/launch.py` para composição.

### 11. Testes e governança

- Testes headless para cliente, cache, parsing, filtros, agregação, ordenação e formatação.
- Testes de UI apenas para montagem/wiring, marcados `@pytest.mark.ui`.
- Não aumentar o orçamento atual de 5 testes de UI.
- Rodar `make lint`, `make complexity` e a suíte completa, por envolver `domain`, CLI, GUI e cache.
- Manter as guardas de arquitetura: `domain` puro, `application` sem UI/rede.

## Risks / Trade-offs

- **[Portal instável]** → retry transitório com backoff/jitter; mensagens claras; cache anterior preservado.
- **[CSV grande (~7,5 MB)]** → download em chunks, timeout de 60 s, progresso indeterminado e parsing em memória.
- **[Tabela com 101 mil linhas]** → filtro de 12 meses e limite de 5.000 linhas exibidas na GUI.
- **[Defasagem e revisões]** → exibir maior `data_liquidacao`; aceitar revisões; não prometer dados de hoje.
- **[Duplicatas legítimas]** → não deduplicar; agregar por soma de `quantidade`/`valor`.
- **[Ordem não cronológica]** → ordenar na apresentação.
- **[Cache corrompido]** → tratar como miss, baixar novamente e substituir atomicamente.
- **[Download truncado]** → validar `Content-Range` e parsing completo antes de substituir.
- **[Schema futuro diferente]** → validar cabeçalho e falhar como `TesouroDataError`.
- **[Orçamento de testes de UI]** → preferir view-model headless e limitar testes de janela ao wiring.

## Decisões aprovadas

- Escopo: somente vendas; resgates/estoque na change `add-tesouro-direto-resgates-estoque`.
- `--agregar` por título: incluído.
- CLI: últimos 30 dias por padrão, relativos à maior data disponível.
- GUI: 12 meses e limite de 5.000 linhas.
- CLI/JSON: ISO + ponto; GUI: `DD/MM/YYYY` + vírgula.
- `--no-cache`: requisição condicional; `304` reutiliza o cache.
- Timeout: 60 s por recurso, com retry.
- Evidências do spike: somente no RFC-001 renomeado.
