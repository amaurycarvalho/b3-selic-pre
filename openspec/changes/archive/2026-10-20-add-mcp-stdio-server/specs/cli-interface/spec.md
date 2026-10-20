## ADDED Requirements

### Requirement: Subcomando mcp

A CLI SHALL aceitar o subcomando `mcp`, que inicia o servidor MCP via `stdio`. O subcomando SHALL aceitar os parâmetros opcionais `--atualizar` e `--data AAAA-MM-DD`.

O subcomando `mcp` NÃO SHALL aceitar `--no-cache`, `--curva`, `--analise`, `--log` ou `--saida`. A ajuda da CLI SHALL listar o subcomando e seus parâmetros.

#### Scenario: Ajuda lista o subcomando mcp

- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `mcp`
- **THEN** a ajuda do subcomando SHALL listar `--atualizar` e `--data`

#### Scenario: Parâmetro não suportado é rejeitado

- **WHEN** o usuário executa `b3-selic-pre mcp --no-cache`
- **THEN** a CLI SHALL encerrar com código de uso `2`

#### Scenario: Preparação com data

- **WHEN** o usuário executa `b3-selic-pre mcp --data 2026-06-10`
- **THEN** a CLI SHALL preparar os dados de 2026-06-10 antes de iniciar o servidor

### Requirement: Seleção da representação da análise no exportar

O subcomando `exportar` SHALL aceitar `--analise-curva curta|longa`, com `curta` como valor efetivo padrão. A opção SHALL selecionar a representação usada no texto da análise e NÃO SHALL alterar a seleção de artefatos de `--curva`.

`--analise-curva` SHALL ser válido apenas junto com `--analise`. Quando informado sem `--analise`, a CLI SHALL encerrar com código de uso `2`.

A análise da curva longa SHALL usar a taxa média por ano. A análise da curva curta SHALL usar os registros brutos. A opção NÃO SHALL alterar o formato dos CSVs de `--curva`.

#### Scenario: Análise longa

- **WHEN** o usuário executa `b3-selic-pre exportar --analise --analise-curva longa`
- **THEN** o artefato `analise.txt` SHALL conter a análise calculada sobre a taxa média por ano

#### Scenario: Análise curta é o padrão

- **WHEN** o usuário executa `b3-selic-pre exportar --analise`
- **THEN** o artefato `analise.txt` SHALL conter a análise calculada sobre os registros brutos

#### Scenario: Opção sem análise é rejeitada

- **WHEN** o usuário executa `b3-selic-pre exportar --curva curta --analise-curva longa` sem `--analise`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum arquivo SHALL ser gravado

#### Scenario: Curva e análise são independentes

- **WHEN** o usuário executa `b3-selic-pre exportar --curva longa --analise --analise-curva curta`
- **THEN** o CSV SHALL conter a evolução consolidada
- **THEN** a análise SHALL usar os registros brutos
