## MODIFIED Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `mcp`, `tesouro`, `tesouro-resgates`, `tesouro-estoque`, `gui` e `criar-atalho`.

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

### Requirement: Subcomando tesouro-resgates

A CLI SHALL aceitar o subcomando `tesouro-resgates`, que consulta recompras, cupons e vencimentos do Tesouro Direto.

O subcomando SHALL aceitar `--tipo recompra|cupom|vencimento`, `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json` e `--no-cache`.

- `--tipo` SHALL filtrar pelo tipo de resgate; sem ele, todos os tipos SHALL ser consultados.
- `--titulo` SHALL filtrar por correspondência parcial, sem distinção de caixa ou acentuação.
- `--inicio` e `--fim` SHALL filtrar por período inclusivo sobre `data_resgate`, no formato `AAAA-MM-DD`.
- Sem `--inicio`/`--fim`, o período SHALL ser de 30 dias até a maior `data_resgate` disponível.
- `--agregar` SHALL agrupar por tipo de resgate e título.
- `--json` SHALL produzir o envelope estruturado com `dataset: "resgates"`.
- Sem `--json`, a saída SHALL ser CSV com delimitador `;`, datas ISO e separador decimal `.`.
- `--no-cache` SHALL forçar uma verificação condicional na rede; `304` SHALL reutilizar o cache.

#### Scenario: Ajuda lista o subcomando
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro-resgates`
- **THEN** a ajuda do subcomando SHALL listar `--tipo`, `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json` e `--no-cache`

#### Scenario: Consulta por tipo

- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --tipo recompra`
- **THEN** a saída SHALL conter apenas recompras

#### Scenario: Período padrão

- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates` sem `--inicio` e `--fim`
- **THEN** a saída SHALL cobrir os últimos 30 dias até a maior `data_resgate` disponível

#### Scenario: Saída CSV

- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates` sem `--json`
- **THEN** o cabeçalho SHALL ser `TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;PU;QUANTIDADE;VALOR`

#### Scenario: Saída agregada

- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --agregar`
- **THEN** o cabeçalho SHALL ser `TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`

#### Scenario: Saída JSON

- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --json`
- **THEN** o payload SHALL conter `dataset: "resgates"` e `registros` ou `agregados`

#### Scenario: Erro de dados

- **WHEN** um recurso tem colunas ausentes ou valores inválidos
- **THEN** a CLI SHALL imprimir uma mensagem de dados em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

### Requirement: Subcomando tesouro-estoque

A CLI SHALL aceitar o subcomando `tesouro-estoque`, que consulta o estoque mensal do Tesouro Direto.

O subcomando SHALL aceitar `--titulo`, `--inicio`, `--fim`, `--mes`, `--agregar`, `--json` e `--no-cache`.

- `--inicio` e `--fim` SHALL usar o formato `AAAA-MM` e SHALL ser inclusivos.
- `--mes` SHALL selecionar um único mês `AAAA-MM`.
- Sem filtros, o subcomando SHALL retornar o último mês disponível.
- `--agregar` SHALL exigir um único mês e SHALL agrupar por título.
- `--json` SHALL produzir o envelope estruturado com `dataset: "estoque"`.
- Sem `--json`, a saída SHALL ser CSV com delimitador `;`, mês `AAAA-MM` e separador decimal `.`.
- `--no-cache` SHALL forçar uma verificação condicional na rede; `304` SHALL reutilizar o cache.

#### Scenario: Ajuda lista o subcomando
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro-estoque`
- **THEN** a ajuda do subcomando SHALL listar `--titulo`, `--inicio`, `--fim`, `--mes`, `--agregar`, `--json` e `--no-cache`

#### Scenario: Último mês é o padrão

- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque` sem filtros
- **THEN** a saída SHALL conter apenas o último mês disponível

#### Scenario: Intervalo de meses

- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --inicio 2025-01 --fim 2025-12`
- **THEN** a saída SHALL conter os meses do intervalo inclusivo

#### Scenario: Saída CSV

- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque` sem `--json`
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE`

#### Scenario: Agregação exige um mês

- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --agregar` com `--inicio`/`--fim` cobrindo mais de um mês
- **THEN** a CLI SHALL encerrar com código `2`

#### Scenario: Saída agregada

- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --mes 2026-08 --agregar`
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO`

#### Scenario: Saída JSON

- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --json`
- **THEN** o payload SHALL conter `dataset: "estoque"` e `registros` ou `agregados`

#### Scenario: Erro de dados

- **WHEN** o recurso tem colunas ausentes ou valores inválidos
- **THEN** a CLI SHALL imprimir uma mensagem de dados em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`
