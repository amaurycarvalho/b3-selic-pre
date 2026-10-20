## Context

O RFC-001 propõe extrair dados de vendas do Tesouro Direto do portal Tesouro Transparente (CKAN). A versão original descreve uma classe monolítica com `requests`, `BeautifulSoup`, `pandas` e scraping HTML, incompatível com o estado atual do projeto.

O `b3-selic-pre` hoje:
- usa Clean Architecture em 4 camadas, com guardas automáticas de dependência (`tests/test_architecture.py`);
- usa apenas `urllib` para HTTP e `csv`/`json` da biblioteca padrão;
- tem cache em disco com escrita atômica, validação de completude e leitura somente leitura (`DiskCache`, `cache_payload.write_atomic`);
- tem contrato `CommunicationError` para falhas de rede/HTTP e logging compartilhado;
- tem CLI baseada em subcomandos de verbo, sem flags legadas no nível raiz;
- tem GUI em janela única, com gráfico, sidebar, statusbar, escudo de inicialização e orçamento de testes de UI;
- tem servidor MCP somente leitura, sem rede durante o atendimento.

Este design é **preliminar**. O schema real do CSV não foi verificado com sucesso neste ambiente (as requisições ao CKAN expiraram), e o RFC original admite que a estrutura deve ser confirmada após o download.

## Blocking Discovery Spike

Antes de qualquer implementação, um spike deve responder:

1. Qual é o endpoint CKAN correto e o identificador real do dataset (`package_show`)?
2. Quais são as colunas reais do CSV, com nomes exatos, acentos, tipos e obrigatoriedade?
3. O dataset contém apenas vendas ou também resgates/saldo?
4. Qual é o encoding (UTF-8, UTF-8 com BOM, Latin-1), o delimitador e o tamanho do arquivo?
5. O servidor oferece `ETag`/`Last-Modified` e responde `304 Not Modified`?
6. Qual é a periodicidade de atualização e a defasagem real?

Até a conclusão do spike:
- o modelo de domínio é provisório;
- a lista de colunas, filtros e agregações é provisória;
- a change não pode ser implementada;
- as specs devem ser revisadas com o schema verificado.

## Goals / Non-Goals

**Goals:**
- Reestruturar a feature em capabilities comportamentais, não em camadas.
- Usar a API CKAN JSON para descoberta do dataset, sem scraping HTML.
- Usar `urllib`, `csv` e `json` da biblioteca padrão.
- Implementar cache cumulativo com escrita atômica, TTL de 6 horas e validação antes de substituir a versão anterior.
- Implementar o subcomando `tesouro` na CLI, alinhado ao contrato de subcomandos.
- Implementar uma janela separada "Tesouro Direto" na GUI, sem alterar o gráfico principal.
- Reutilizar os padrões existentes de XDG, retry, logging, erros e formatação.
- Manter testes headless para as regras e testes de UI apenas para montagem/wiring.

**Non-Goals:**
- Tools MCP para Tesouro.
- Exportação Tesouro no subcomando `exportar` ou botão de cópia dedicado.
- Gráficos de movimentação.
- Banco de dados (PostgreSQL/SQLite).
- Agendamento/cron.
- Cruzamento com a curva SELIC.
- Atualização do PRD antes do spike e da aprovação de implementação.
- Suporte a outros datasets do Tesouro Transparente.

## Decisions

### 1. CKAN JSON em vez de scraping HTML

**Decisão:** usar `GET /api/3/action/package_show` para obter metadados e a URL do recurso CSV.

**Alternativa rejeitada:** scraping com `BeautifulSoup`. É frágil, exige dependência externa e foi a fonte dos problemas da proposta original.

**Racional:** a API CKAN retorna JSON estruturado e é o caminho documentado do portal. O parsing usa `json.loads()`, já usado na infraestrutura.

### 2. `urllib` + `csv` + `json` nativos

**Decisão:** download com `urllib.request`, leitura em chunks, parsing com `csv` e serialização com `json`.

**Alternativa rejeitada:** `requests`, `pandas` e `lxml`. Aumentam o binário e não são usados pelo projeto.

**Racional:** reduz dependências, mantém o padrão de injeção de `opener` e permite testar sem rede.

### 3. Cache cumulativo de arquivo único

**Decisão:** manter um único CSV cumulativo (`vendastesourodireto.csv`) e um arquivo de metadados no diretório `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`.

- TTL de 6 horas.
- Download condicional com `ETag`/`If-Modified-Since`; `304` reutiliza o cache.
- Download para arquivo temporário, validação e substituição atômica via `cache_payload.write_atomic`.
- Se o download falhar, a versão válida anterior é preservada.
- Sem housekeeping: o dataset é cumulativo e o RFC confirma que basta a última versão.
- Leitura somente leitura para consumidores que não devem alterar o cache.

**Alternativa rejeitada:** cache por data de download e housekeeping copiados do `DiskCache`. Não fazem sentido para um arquivo cumulativo.

### 4. Modelo de domínio provisório

**Decisão:** definir um frozen dataclass `RegistroTesouroDireto` com os campos provisórios `data`, `titulo`, `venda`, `resgate`, `saldo` e `vencimento`.

**Racional:** segue o padrão de `RateRecord`. O nome e os campos finais dependem do spike; se o dataset for apenas de vendas, o modelo pode ser renomeado para `VendaTesouroDireto` e os campos ajustados.

**Trade-off:** valores monetários como `float` são suficientes para exibição e agregações simples. Se o spike revelar necessidade de precisão exata, avaliar `Decimal` ou preservar o texto original.

### 5. CLI: subcomando `tesouro`

**Decisão:**

```text
b3-selic-pre tesouro [--titulo T] [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD]
                     [--json] [--no-cache]
```

- Saída padrão em CSV com delimitador `;` e separador decimal `.`.
- `--json` retorna metadados e registros estruturados.
- `--no-cache` força o download.
- Códigos: `0` sucesso, `1` falha de comunicação/dados, `2` uso/validação.
- Nenhuma flag no nível raiz; a CLI continua baseada em subcomandos.

**Alternativa rejeitada:** `--tesouro` como flag raiz. Contradiz `cli-interface`.

### 6. GUI: janela separada

**Decisão:** adicionar um botão "Tesouro Direto" na barra superior e abrir uma janela `Toplevel` independente, com tabela, filtros, botão de atualização e status próprio.

**Alternativa rejeitada:** aba em `ttk.Notebook`. A GUI não usa Notebook; introduzir abas exigiria reestruturar a janela principal e arriscaria o escudo de inicialização, o gráfico e as specs atuais.

**Racional:** preserva a janela principal e o gráfico, reutiliza `GuiDependencies` e permite um view-model headless.

### 7. Erros e logging

**Decisão:**

- `CommunicationError` para falhas de rede, HTTP, timeout e corpo vazio após retries.
- Erros de dados (`ValueError` ou erro de domínio) para CSV malformado, colunas ausentes e valores inválidos.
- Falhas de comunicação em linha única no log; exceções inesperadas com traceback.
- CLI em `stderr` com código `1` ou `2`; GUI mostra a mensagem na janela e permanece utilizável.

### 8. Reuso de infraestrutura existente

- `xdg.cache_base()` para o diretório base.
- `cache_payload.write_atomic()` para escrita atômica.
- `b3_retry` para retry com backoff e jitter.
- `application/formatting.py` para CSV e formatação numérica.
- `ActionLock` para serializar downloads, se CLI e GUI puderem disparar ao mesmo tempo.
- `application/errors.CommunicationError`.
- `GuiDependencies` e `gui/launch.py` para composição.

### 9. Testes e governança

- Testes headless para cliente, cache, parsing, filtros, agregação e formatação.
- Testes de UI apenas para montagem/wiring, marcados `@pytest.mark.ui`.
- Respeitar o orçamento atual de 5 testes de UI; reduzir outro teste ou obter aprovação explícita se for necessário ampliar.
- Rodar `make lint`, `make complexity` e a suíte completa, por envolver `domain`, CLI, GUI e cache.
- Manter as guardas de arquitetura: `domain` puro, `application` sem UI/rede.

## Risks / Trade-offs

- **[Schema real divergente]** → o spike é bloqueante; as specs e o modelo serão revisados antes da implementação.
- **[CKAN indisponível ou instável]** → o MCP continua sem rede; o Tesouro falha com `CommunicationError` e a GUI permanece utilizável.
- **[CSV grande (~7 MB)]** → download em chunks, timeout de 60s e progresso na GUI; parsing em streaming quando possível.
- **[Encoding/delimitador imprevisíveis]** → tentar UTF-8 com BOM, UTF-8 e Latin-1; validar o delimitador e as colunas antes de cachear.
- **[Cache corrompido]** → tratar como miss, baixar novamente e substituir atomicamente.
- **[Duplicação com a B3]** → manter adaptadores separados; extrair um cliente HTTP genérico só se surgir uma terceira fonte.
- **[Orçamento de testes de UI]** → preferir view-model headless e limitar testes de janela ao wiring.

## Open Questions

Estas questões devem ser resolvidas pelo spike bloqueante:

- O identificador do dataset é `vendas-do-tesouro-direto` ou um UUID?
- O dataset é de vendas ou de movimentações completas?
- Quais são os nomes reais das colunas e os tipos?
- O CSV usa `;` ou `,`? UTF-8 ou Latin-1?
- Há `ETag` e `Last-Modified` utilizáveis?
- Qual é a defasagem real entre a data dos dados e a publicação?
