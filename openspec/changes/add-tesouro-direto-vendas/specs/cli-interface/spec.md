## MODIFIED Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `mcp`, `tesouro`, `gui` e `criar-atalho`.

#### Scenario: Execução sem argumentos abre a GUI
- **WHEN** o usuário executa `b3-selic-pre` sem argumentos
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Subcomando gui abre a GUI
- **WHEN** o usuário executa `b3-selic-pre gui`
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Ajuda lista os subcomandos
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar os subcomandos disponíveis e seus parâmetros

## ADDED Requirements

### Requirement: Subcomando tesouro

A CLI SHALL aceitar o subcomando `tesouro`, que consulta as vendas do Tesouro Direto a partir do cache local ou de um download.

O subcomando SHALL aceitar `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json` e `--no-cache`.

- `--titulo` SHALL filtrar por correspondência parcial, sem distinção de caixa ou acentuação.
- `--inicio` e `--fim` SHALL filtrar por período inclusivo sobre `data_liquidacao`, no formato `AAAA-MM-DD`.
- Sem `--inicio`/`--fim`, o período SHALL ser de 30 dias até a maior `data_liquidacao` disponível.
- `--inicio` maior que `--fim` SHALL ser erro de uso.
- `--agregar` SHALL agrupar por título.
- `--json` SHALL produzir um payload estruturado com `fonte`, `origem`, `dataset`, `resource_id`, `data_extracao`, `publicado_em`, `data_maxima_liquidacao`, `total_registros`, `periodo` e `registros` ou `agregados`; com `--agregar`, SHALL incluir também `total_agregados`.
- Sem `--json`, a saída SHALL ser CSV com delimitador `;`, datas ISO e separador decimal `.`.
- `--no-cache` SHALL forçar uma verificação condicional na rede; `304` SHALL reutilizar o cache.

O subcomando NÃO SHALL aceitar flags no nível raiz. Os códigos de retorno SHALL ser `0` para sucesso (inclusive resultado vazio), `1` para falha de comunicação ou de dados e `2` para erro de uso ou validação.

#### Scenario: Ajuda lista o subcomando tesouro
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro`
- **THEN** a ajuda do subcomando SHALL listar `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json` e `--no-cache`

#### Scenario: Consulta com filtros
- **WHEN** o usuário executa `b3-selic-pre tesouro --titulo "Selic" --inicio 2026-01-01 --fim 2026-06-30`
- **THEN** a saída SHALL conter apenas as vendas correspondentes ao título e ao período de liquidação

#### Scenario: Período padrão
- **WHEN** o usuário executa `b3-selic-pre tesouro` sem `--inicio` e `--fim`
- **THEN** a saída SHALL cobrir os últimos 30 dias até a maior `data_liquidacao` disponível

#### Scenario: Datas são exatas
- **WHEN** o usuário informa `--inicio` ou `--fim` em um fim de semana ou feriado
- **THEN** a CLI SHALL usar a data exatamente como informada
- **THEN** a CLI NÃO SHALL ajustar para o dia útil mais próximo

#### Scenario: Período invertido
- **WHEN** o usuário informa `--inicio` maior que `--fim`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Saída CSV
- **WHEN** o usuário executa `b3-selic-pre tesouro` sem `--json`
- **THEN** a saída SHALL ser CSV com delimitador `;`
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR`
- **THEN** os valores numéricos SHALL usar separador decimal `.`

#### Scenario: Saída agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro --agregar`
- **THEN** a saída SHALL ser agregada por título
- **THEN** o cabeçalho CSV SHALL ser `TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`

#### Scenario: Saída JSON
- **WHEN** o usuário executa `b3-selic-pre tesouro --json`
- **THEN** a saída SHALL ser um objeto JSON com metadados e `registros`
- **THEN** os valores monetários SHALL ser strings com ponto decimal

#### Scenario: Saída JSON agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro --json --agregar`
- **THEN** o objeto JSON SHALL conter `agregados` no lugar de `registros`

#### Scenario: Período sem registros
- **WHEN** o filtro não encontra registros
- **THEN** a CLI SHALL imprimir o cabeçalho CSV (ou lista vazia no JSON)
- **THEN** a CLI SHALL encerrar com código `0`

#### Scenario: Forçar download
- **WHEN** o usuário executa `b3-selic-pre tesouro --no-cache`
- **THEN** a CLI SHALL fazer uma verificação condicional na rede mesmo que exista cache válido
- **THEN** uma resposta `304` SHALL reutilizar o cache

#### Scenario: Data inválida
- **WHEN** o usuário informa uma data fora do formato `AAAA-MM-DD`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Falha de comunicação
- **WHEN** o download falha por rede ou HTTP
- **THEN** a CLI SHALL imprimir uma mensagem em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

#### Scenario: Erro de dados
- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** a CLI SHALL imprimir uma mensagem de dados em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

#### Scenario: Flag raiz legada é rejeitada
- **WHEN** o usuário executa `b3-selic-pre --tesouro`
- **THEN** a CLI SHALL encerrar com código de uso `2`
- **THEN** a CLI SHALL exibir a mensagem de ajuda
