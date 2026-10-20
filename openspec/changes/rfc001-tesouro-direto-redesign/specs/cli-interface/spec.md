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

A CLI SHALL aceitar o subcomando `tesouro`, que consulta as movimentações do Tesouro Direto a partir do cache local ou de um download.

O subcomando SHALL aceitar `--titulo`, `--inicio`, `--fim`, `--json` e `--no-cache`.

- `--titulo` SHALL filtrar por correspondência parcial, sem distinção de caixa ou acentuação.
- `--inicio` e `--fim` SHALL filtrar por período inclusivo no formato `AAAA-MM-DD`.
- `--json` SHALL produzir um payload estruturado com `fonte`, `data_extracao`, `total_registros`, `periodo` e `registros`.
- Sem `--json`, a saída SHALL ser CSV com delimitador `;` e separador decimal `.`.
- `--no-cache` SHALL forçar o download.

O subcomando NÃO SHALL aceitar flags no nível raiz. Os códigos de retorno SHALL ser `0` para sucesso, `1` para falha de comunicação ou de dados e `2` para erro de uso ou validação.

#### Scenario: Ajuda lista o subcomando tesouro
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro`
- **THEN** a ajuda do subcomando SHALL listar `--titulo`, `--inicio`, `--fim`, `--json` e `--no-cache`

#### Scenario: Consulta com filtros
- **WHEN** o usuário executa `b3-selic-pre tesouro --titulo "Selic" --inicio 2026-01-01 --fim 2026-06-30`
- **THEN** a saída SHALL conter apenas os registros correspondentes ao título e ao período

#### Scenario: Saída CSV
- **WHEN** o usuário executa `b3-selic-pre tesouro` sem `--json`
- **THEN** a saída SHALL ser CSV com delimitador `;`
- **THEN** os valores numéricos SHALL usar separador decimal `.`

#### Scenario: Saída JSON
- **WHEN** o usuário executa `b3-selic-pre tesouro --json`
- **THEN** a saída SHALL ser um objeto JSON com metadados e `registros`

#### Scenario: Forçar download
- **WHEN** o usuário executa `b3-selic-pre tesouro --no-cache`
- **THEN** a CLI SHALL baixar o CSV mesmo que exista cache válido

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
