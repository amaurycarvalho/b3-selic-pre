# RFC-001 - Vendas do Tesouro Direto

**Status:** spike concluído em 2026-10-20; decisões aprovadas; aguardando implementação
**Última revisão:** 2026-10-20
**Escopo:** vendas do Tesouro Direto (dataset `vendas-do-tesouro-direto`)

---

## 1. Status e escopo

Esta RFC nasceu como "Movimentações do Tesouro Direto". O spike de descoberta mostrou que o portal publica vendas, resgates e estoque em **datasets separados**, com schemas, granularidades e periodicidades diferentes:

- vendas: diária, um CSV;
- resgates: diária/eventual, quatro recursos CSV (recompras, cupom, vencimentos e um cupom duplicado);
- estoque: mensal, um CSV.

Para manter a change coesa e reduzir risco, esta RFC cobre **somente vendas**. Resgates e estoque ficam para a change `add-tesouro-direto-resgates-estoque`, reutilizando o cliente, o cache, a CLI e a GUI aqui definidos.

O spike está concluído e o schema real foi incorporado a esta RFC no dia 2026-10-20. Nenhum código de implementação foi escrito nesta etapa.

---

## 2. Objetivo

Disponibilizar, para a CLI e para a GUI do `b3-selic-pre`, uma consulta às **vendas do Tesouro Direto** publicadas no portal Tesouro Transparente, com:

- descoberta do dataset via API CKAN JSON;
- download, cache e validação do CSV cumulativo;
- parsing e formatação com a biblioteca padrão;
- filtros por título e período de liquidação;
- agregação opcional por título;
- saída CSV/JSON na CLI;
- janela separada na GUI.

A feature é aditiva e não altera a consulta da curva SELIC Pré.

---

## 3. Decisões de arquitetura

### 3.1 Clean Architecture

| Camada | Responsabilidade |
| --- | --- |
| `domain` | `VendaTesouroDireto`, constantes puras e tipos de valor |
| `application` | Parsing, validação, filtros, agregação, ordenação e formatação |
| `infrastructure` | Cliente CKAN, download do CSV, cache e metadados |
| `presentation` | CLI (`tesouro`) e janela da GUI |

As guardas de `tests/test_architecture.py` continuam válidas: `domain` é puro; `application` não importa UI, rede ou `presentation`; `infrastructure` não importa UI.

### 3.2 Dependências

Nenhuma dependência externa nova. Usar apenas:

- `urllib` para HTTP;
- `csv` para parsing;
- `json` para metadados;
- `decimal` para valores monetários e quantidades;
- `unicodedata` para normalização de título;
- `hashlib` para o hash do CSV em cache.

`requests`, `BeautifulSoup` e `pandas` continuam descartados.

---

## 4. Fonte de dados

### 4.1 Dataset e descoberta via CKAN

Dataset confirmado:

| Item | Valor |
| --- | --- |
| Nome | `vendas-do-tesouro-direto` |
| UUID | `f0468ecc-ae97-4287-89c2-6d8139fb4343` |
| Título | Vendas do Tesouro Direto |
| Organização | COTED |
| Frequência | Diária |
| Início dos dados | Janeiro/2002 |
| Recursos | 1 CSV + 1 PDF de metadados |
| CSV resource UUID | `e5f90e3a-8f8d-4895-9c56-4bb2f7877920` |
| CSV URL | `https://www.tesourotransparente.gov.br/ckan/dataset/f0468ecc-ae97-4287-89c2-6d8139fb4343/resource/e5f90e3a-8f8d-4895-9c56-4bb2f7877920/download/vendastesourodireto.csv` |
| Tamanho | 7.488.603 bytes |
| `resource.last_modified` | `2026-10-16T10:29:05.555425` |
| `resource.hash` | vazio |

A descoberta usa:

```text
GET https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=vendas-do-tesouro-direto
```

Regras:

- validar `success: true`;
- exigir exatamente um recurso com `format == "CSV"`;
- extrair a URL do recurso;
- não interpretar HTML nem extrair o PDF de metadados;
- se o CSV não existir, levantar `TesouroDataError`.

O UUID do recurso **não** é um package: `package_show` com ele retorna `404`.

### 4.2 Download

O download usa `urllib.request` com:

- leitura em chunks;
- timeout padrão de **60 segundos** por recurso;
- retry transitório com backoff/jitter para erros de rede, timeouts, HTTP 5xx/429 e corpo vazio/parcial;
- `ETag`/`If-None-Match` e `Last-Modified`/`If-Modified-Since` quando disponíveis;
- tratamento explícito de `304 Not Modified`;
- `User-Agent` padrão do `urllib`.

Cabeçalhos confirmados no spike:

```text
HTTP/1.1 200 OK
Content-Type: text/csv
Transfer-Encoding: chunked
Content-Range: bytes 0-7488602/7488603
Accept-Ranges: bytes
ETag: "1792146545.96-7488603"
Last-Modified: Fri, 16 Oct 2026 10:29:05 GMT
Cache-Control: no-cache
```

Observações:

- não há `Content-Length`; o total pode ser validado por `Content-Range`;
- `If-None-Match` e `If-Modified-Since` retornam `304`;
- o portal fecha conexões e dá timeout de forma intermitente; retry é obrigatório;
- uma resposta `200` com `Content-Type` que não comece por `text/csv` deve ser tratada como falha transitória de comunicação, não como CSV válido.

Falhas de rede, HTTP, timeout, corpo vazio e corpo parcial após os retries são `CommunicationError`.

### 4.3 Dataset cumulativo, revisões e ordenação

O dataset é cumulativo desde 2002 e atualizado diariamente, com defasagem de até dois dias úteis em relação à extração. Além disso:

- os valores podem ser **revisados** por estornos ou correções;
- a ordem do CSV **não é cronológica**;
- existem duplicatas legítimas por `(tipo_titulo, vencimento, data_liquidacao)`, com `PU` e `quantidade` diferentes;
- não há chave natural única; não deduplicar.

A aplicação deve exibir a maior `data_liquidacao` disponível e não prometer dados de "hoje".

---

## 5. Cache

### 5.1 Localização

```text
$XDG_CACHE_HOME/b3-selic-pre/tesouro/
├── vendastesourodireto.csv
└── metadata.json
```

No Linux, `$XDG_CACHE_HOME` tem fallback para `~/.cache`. O caminho é resolvido por `infrastructure/xdg.py`.

### 5.2 Metadados

`metadata.json` deve conter, no mínimo:

- `schema_version`;
- `dataset_name` e `dataset_id`;
- `resource_id` e `resource_url`;
- `etag` e `last_modified`;
- `downloaded_at` (instante do download);
- `checked_at` (última verificação condicional, inclusive `304`);
- `size_bytes` e `sha256`;
- `row_count`;
- `first_data_date` e `last_data_date`.

### 5.3 Regras

- TTL de **6 horas** baseado em `checked_at`.
- Download para arquivo temporário, validação e substituição atômica em **bytes**.
- Se o download falhar, a versão válida anterior é preservada.
- Cache ausente, vencido, vazio, corrompido, incompleto ou com `schema_version` antigo é tratado como miss.
- Em `304`, o CSV não é regravado; apenas `checked_at` é atualizado atomicamente.
- Leitura somente leitura não remove, renomeia nem altera arquivos.
- Não há housekeeping de arquivos datados, pois o dataset é cumulativo.
- Um novo arquivo com menos linhas que o anterior é aceito, mas gera aviso de revisão.

---

## 6. Processamento

### 6.1 Modelo

Frozen dataclass `VendaTesouroDireto`:

| Campo | Tipo | Observação |
| --- | --- | --- |
| `tipo_titulo` | `str` | valor da coluna `Tipo Titulo` |
| `vencimento` | `str` | data ISO `AAAA-MM-DD` |
| `data_liquidacao` | `str` | data ISO; liquidação D+1 da operação |
| `pu` | `Decimal` | preço unitário médio |
| `quantidade` | `Decimal` | quantidade de títulos |
| `valor` | `Decimal` | volume financeiro; `PU × Quantidade` |

Não existe campo `venda`, `resgate` ou `saldo` neste dataset.

### 6.2 Parsing

- Decodificar `utf-8-sig`, depois `utf-8` e, por fim, `latin-1`.
- Usar `;` como delimitador; não usar `csv.Sniffer`, pois o decimal com vírgula confunde a detecção.
- Exigir o cabeçalho real:

```text
Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;PU;Quantidade;Valor
```

- Mapear colunas sem distinção de caixa/acentos.
- Exigir todas as colunas obrigatórias; ignorar colunas desconhecidas com aviso.
- Converter datas `DD/MM/YYYY` para ISO.
- Converter decimais com vírgula para `Decimal` (aceitar ponto como separador de milhar quando houver vírgula).
- Reportar erros com linha e coluna.
- CSV vazio ou sem registros gera `TesouroDataError` e não é cacheado.
- Preservar duplicatas.

### 6.3 Filtros, agregação e ordenação

- `filtrar_por_titulo`: parcial, sem caixa/acentos, sobre `tipo_titulo`.
- `filtrar_por_periodo`: inclusivo, sobre `data_liquidacao`.
- `agregar_por_titulo`: somar `quantidade` e `valor`; calcular `PU` médio ponderado por `valor / quantidade`.
- Ordenação determinística: `data_liquidacao` desc, `tipo_titulo` asc, `vencimento` asc, `pu` asc.

### 6.4 Formatação

- CLI/JSON usam datas ISO e ponto decimal.
- GUI usa `DD/MM/YYYY` e vírgula decimal.
- CSV de vendas:

```text
TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR
```

- CSV agregado:

```text
TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO
```

- Precisão: `PU` com 6 casas, `quantidade` e `valor` com 2 casas.
- JSON:

```json
{
  "fonte": "Tesouro Transparente",
  "origem": "cache",
  "dataset": "vendas-do-tesouro-direto",
  "resource_id": "e5f90e3a-8f8d-4895-9c56-4bb2f7877920",
  "data_extracao": "2026-10-20T15:11:44-03:00",
  "publicado_em": "2026-10-16T10:29:05.555425",
  "data_maxima_liquidacao": "2026-10-14",
  "total_registros": 101331,
  "periodo": {"inicio": "2026-09-20", "fim": "2026-10-20"},
  "registros": []
}
```

- Valores monetários no JSON são strings com ponto decimal, para preservar precisão.
- Com `--agregar`, o payload usa `agregados` no lugar de `registros` e inclui `total_agregados`.

---

## 7. CLI

### 7.1 Subcomando

```text
b3-selic-pre tesouro [--titulo T] [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD]
                     [--agregar] [--json] [--no-cache]
```

### 7.2 Filtros e padrões

- `--titulo`: parcial, sem caixa/acentos.
- `--inicio`/`--fim`: datas ISO de calendário, exatas, inclusivas, sem ajuste para dia útil.
- Sem `--inicio`/`--fim`: **últimos 30 dias** relativos à maior `data_liquidacao` disponível, não a "hoje".
- `--inicio` maior que `--fim` é erro de uso.
- `--agregar`: agrupa por título e usa o CSV/JSON agregado.
- `--no-cache`: força uma verificação na rede; `304` reutiliza o cache.
- `--json`: payload estruturado.

### 7.3 Saída e códigos

- Sem `--json`: CSV no stdout.
- Com `--json`: objeto JSON no stdout.
- Período sem registros: cabeçalho CSV apenas (ou lista vazia no JSON), saída `0`.
- Erros em `stderr`.

| Código | Significado |
| --- | --- |
| `0` | Sucesso, inclusive resultado vazio |
| `1` | Falha de comunicação ou de dados |
| `2` | Erro de uso ou validação |

Nenhuma flag no nível raiz. `b3-selic-pre --tesouro` é inválido e retorna `2`.

### 7.4 Integração

O subcomando é adicionado em `presentation/cli_parser.py` e implementado em `presentation/cli_commands.py`; o cliente é montado no composition root em `presentation/cli.py`.

---

## 8. GUI

### 8.1 Janela separada

A GUI ganha um botão "Tesouro Direto" na barra superior, com ícone, tooltip e respeito ao escudo de inicialização. O botão:

- abre uma janela `Toplevel` independente;
- não altera o gráfico principal;
- se a janela já estiver aberta, apenas a traz para frente;
- ao abrir, carrega o cache válido, se existir;
- se não houver cache, orienta "clique em Atualizar", sem baixar automaticamente.

### 8.2 Tabela e filtros

- `ttk.Treeview` rolável com colunas `Tipo`, `Vencimento`, `Liquidação`, `PU`, `Quantidade`, `Valor`.
- Datas exibidas em `DD/MM/YYYY`; números com vírgula decimal.
- Filtro por título e período; período inclusivo; `inicio <= fim`.
- Período padrão: **12 meses** relativos à maior `data_liquidacao`.
- Limite de **5.000 linhas exibidas**, com status "mostrando X de Y; refine os filtros".
- Data inválida exibe mensagem e não inicia download.

### 8.3 Atualização, cache e status

- "Atualizar" usa o cache válido.
- "Ignorar cache" força uma verificação condicional; `304` reutiliza o cache.
- Progresso **indeterminado**, pois não há `Content-Length`.
- A ação de atualização fica desabilitada durante a carga; a janela principal permanece responsiva.
- Fechar a janela durante o download não pode gerar exceção.
- Status com `Fonte: Cache` ou `Fonte: Tesouro Transparente`, instante da extração, maior `data_liquidacao` e contagem de registros.
- Erros de comunicação e de dados aparecem na área de status; a janela permanece utilizável.

### 8.4 Threading e view-model

O download e o parsing rodam em thread; a UI é atualizada via `root.after`. O estado da janela (linhas, filtros, controles, limite e status) é calculado por um view-model headless em `presentation/tesouro_view_model.py`.

### 8.5 Testes de UI

Testes que importam Tkinter ou a GUI são marcados com `@pytest.mark.ui` e respeitam o orçamento atual de 5 testes. A preferência é testar o view-model headless; o orçamento não aumenta.

---

## 9. Erros e logging

- `CommunicationError` para rede, HTTP, timeout, corpo vazio/parcial e resposta que não seja CSV.
- `TesouroDataError` para CSV malformado, colunas ausentes, datas/valores inválidos e CSV vazio.
- Erro de validação de período (`--inicio`/`--fim`) é erro de uso, com código `2`.
- Falhas esperadas são registradas em uma linha, sem traceback.
- Exceções inesperadas são registradas com traceback completo.
- CLI em `stderr` com código `1`/`2`; GUI mostra a mensagem e permanece utilizável.

---

## 10. Testes e qualidade

- Testes headless de cliente, cache, parsing, filtros, agregação, ordenação e formatação.
- Testes de UI apenas para montagem/wiring, sem aumentar o orçamento.
- `make lint`, `make complexity` e suíte completa, por envolver `domain`, CLI, GUI e cache compartilhado.
- Teste manual opcional da CLI e da janela.

---

## 11. Non-goals

- Resgates e estoque nesta change; serão tratados na change `add-tesouro-direto-resgates-estoque`.
- Investidores, operações e taxas dos títulos.
- Tools MCP para Tesouro.
- Exportação Tesouro no `exportar` ou botão de cópia dedicado.
- Gráficos de movimentação.
- Banco de dados.
- Agendamento/cron.
- Cruzamento com a curva SELIC.
- Atualização do PRD antes da implementação.
- Outros datasets do Tesouro Transparente.

---

## 12. Spike: evidências

### 12.1 Dataset

- `package_show?id=vendas-do-tesouro-direto` retorna `success: true` e 5.088 bytes.
- `metadata_modified`: `2026-10-16T10:29:05Z`.
- Recursos: CSV (`7.488.603` bytes) e PDF (`572.418` bytes).
- O UUID do recurso não funciona como package (`404`).
- O portal apresentou conexões fechadas e timeouts intermitentes; retries resolveram.

### 12.2 Schema e volume

```text
Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;PU;Quantidade;Valor
```

| Métrica | Valor |
| --- | --- |
| Registros | 101.331 |
| Datas distintas de liquidação | 6.129 |
| Intervalo | 2002-01-04 a 2026-10-14 |
| Títulos distintos | 9 |
| Encoding | ASCII/UTF-8, sem BOM |
| Delimitador | `;` |
| Quebra de linha | LF |
| Decimal | vírgula |
| Datas | `DD/MM/YYYY` |

### 12.3 Qualidade

- 110 chaves `(tipo, vencimento, data)` com mais de uma linha; máximo 3.
- 8 chaves repetem também o `PU`; nenhuma linha é idêntica.
- Duas divergências `Valor != PU × Quantidade` acima de 0,1%, por truncamento.
- O CSV não está ordenado por data.
- O PDF diz quantidade com 1 casa, mas o CSV traz 2; preservar o CSV.

### 12.4 HTTP e cache

- `ETag`: `"1792146545.96-7488603"`.
- `Last-Modified`: `Fri, 16 Oct 2026 10:29:05 GMT`.
- `304` funciona com `If-None-Match` e `If-Modified-Since`.
- `Content-Range: bytes 0-7488602/7488603`; sem `Content-Length`.
- Download de 7,5 MB em ~29 s nesta máquina.
- Timeout aprovado: 60 s, com retry.

### 12.5 Defasagem e revisões

- Publicação de 16/10/2026 continha dados até 14/10/2026.
- Em 20/10/2026, o recurso ainda era o de 16/10; defasagem aparente de 4 dias úteis.
- O PDF confirma defasagem de até dois dias e política de revisão.
- A aplicação deve exibir a maior `data_liquidacao`, não prometer dados de hoje.

### 12.6 Checklist

- [x] Confirmar endpoint e identificador do dataset.
- [x] Baixar amostra do CSV e registrar tamanho, encoding, BOM e delimitador.
- [x] Registrar cabeçalho, tipos, volume, duplicatas e ordenação.
- [x] Confirmar que o dataset é apenas de vendas.
- [x] Confirmar `ETag`/`Last-Modified`/`304`.
- [x] Confirmar periodicidade e defasagem.
- [x] Incorporar o schema verificado nesta RFC, nas specs e nas tarefas.

---

## 13. Decisões aprovadas

- Escopo desta change: somente vendas.
- Resgates e estoque: change `add-tesouro-direto-resgates-estoque`.
- `--agregar` por título: incluído.
- Período padrão da CLI: últimos 30 dias relativos à maior data disponível.
- Período padrão da GUI: 12 meses; limite de 5.000 linhas exibidas.
- CLI/JSON: ISO e ponto decimal; GUI: `DD/MM/YYYY` e vírgula.
- `--no-cache`: requisição condicional; `304` reutiliza o cache.
- Timeout: 60 s por recurso, com retry.
- Evidências do spike: somente nesta RFC, sem arquivo `spike.md`.
- Nome desta RFC: "Vendas do Tesouro Direto".

---

## 14. Referências

- `docs/adrs/ADR-001.md` — Clean Architecture.
- `openspec/specs/architecture-governance/spec.md`.
- `openspec/specs/cli-interface/spec.md`.
- `openspec/specs/disk-cache/spec.md`.
- `openspec/specs/application-logging/spec.md`.
- `openspec/specs/test-suite-performance/spec.md`.
- `docs/misc/datasources.md` — atualizar na implementação para incluir o Tesouro Transparente.
