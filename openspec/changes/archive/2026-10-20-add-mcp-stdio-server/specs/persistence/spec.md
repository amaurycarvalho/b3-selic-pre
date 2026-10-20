## ADDED Requirements

### Requirement: Data de referência da última carga

As configurações da aplicação SHALL persistir a chave `data_referencia`, contendo a data resolvida da última carga de dados bem-sucedida.

A chave SHALL ser atualizada pelo subcomando `atualizar`, pela preparação do subcomando `mcp` e por uma carga bem-sucedida da GUI. Os subcomandos `consultar` e `exportar` NÃO SHALL alterar `data_referencia`.

A preparação do `mcp` SHALL atualizar a chave mesmo quando os dados forem obtidos integralmente do cache. Uma carga sem dados NÃO SHALL atualizar a chave.

#### Scenario: Atualizar persiste a referência

- **WHEN** `b3-selic-pre atualizar --data 2026-06-10` conclui com dados
- **THEN** `data_referencia` SHALL ser persistida como `2026-06-10`

#### Scenario: Preparação do MCP persiste a referência

- **WHEN** `b3-selic-pre mcp --data 2026-06-10` conclui a preparação com dados
- **THEN** `data_referencia` SHALL ser persistida como `2026-06-10`

#### Scenario: GUI persiste a referência

- **WHEN** a GUI conclui uma carga de dados com sucesso para uma data resolvida
- **THEN** `data_referencia` SHALL ser persistida com essa data

#### Scenario: Consultar e exportar não alteram a referência

- **WHEN** o usuário executa `consultar` ou `exportar` para outra data
- **THEN** `data_referencia` SHALL permanecer inalterada

#### Scenario: Carga sem dados não altera a referência

- **WHEN** uma carga termina sem registros
- **THEN** `data_referencia` NÃO SHALL ser atualizada

### Requirement: Escrita atômica e leitura tolerante das configurações

A gravação do arquivo de configurações SHALL ser atômica, de modo que um leitor concorrente veja o conteúdo antigo ou o novo, nunca um arquivo parcial.

Um arquivo de configurações ausente, corrompido ou sem a chave `data_referencia` NÃO SHALL impedir a inicialização da aplicação. Nesses casos, os consumidores SHALL usar os padrões existentes ou o fallback definido para a data de referência.

#### Scenario: Leitor não vê arquivo parcial

- **WHEN** uma escrita de configurações está em andamento
- **THEN** um leitor concorrente SHALL ver o conteúdo anterior ou o novo
- **THEN** o leitor NÃO SHALL falhar por JSON inválido causado pela escrita

#### Scenario: Configuração sem a chave

- **WHEN** o arquivo de configurações existe mas não contém `data_referencia`
- **THEN** a aplicação SHALL iniciar normalmente
- **THEN** o consumidor SHALL aplicar o fallback previsto

#### Scenario: Configuração corrompida

- **WHEN** o arquivo de configurações contém JSON inválido
- **THEN** a aplicação SHALL usar os padrões
- **THEN** a aplicação NÃO SHALL encerrar por causa disso
