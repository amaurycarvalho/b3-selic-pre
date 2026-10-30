# Persistence

## Purpose
Persist user preferences to an XDG-compliant JSON settings file with graceful fallback. TBD.

## Requirements

### Requirement: XDG-compliant settings persistence
The system SHALL persist user preferences to an XDG-compliant JSON settings file.

#### Scenario: Settings saved to XDG path
- **WHEN** the user changes a preference or loads data
- **THEN** settings SHALL be saved to `~/.config/b3-selic-pre/settings.json` on Linux

#### Scenario: Last used date restored
- **WHEN** the application starts
- **THEN** the date entry SHALL be pre-filled with the last used date from settings

#### Scenario: View mode persisted
- **WHEN** the application starts
- **THEN** the view mode (raw/consolidated) SHALL be restored from settings

#### Scenario: Evolution toggle persisted
- **WHEN** the application starts
- **THEN** the evolution checkbox state SHALL be restored from settings

#### Scenario: 3D toggle persisted
- **WHEN** the application starts
- **THEN** the 3D checkbox state SHALL be restored from settings

#### Scenario: Sidebar toggle persisted
- **WHEN** the application starts
- **THEN** the analysis sidebar state SHALL be restored from settings

#### Scenario: Settings saved on preference change
- **WHEN** the user toggles any preference (view mode, evolution, 3D, sidebar)
- **THEN** the current state SHALL be persisted to the settings file

### Requirement: Graceful fallback
The system SHALL handle settings file errors gracefully.

#### Scenario: Missing file uses defaults
- **WHEN** the settings file does not exist on startup
- **THEN** the system SHALL use the first-run defaults (date=today, view=consolidated, evolution=on, 3D=off, sidebar=on)

#### Scenario: Corrupt file uses defaults
- **WHEN** the settings file contains invalid JSON or does not contain a valid settings object
- **THEN** the system SHALL use the compatibility defaults (date=today, view=raw, evolution=off, 3D=off, sidebar=off)

#### Scenario: Existing file without a preference key uses compatibility defaults
- **WHEN** the settings file exists and is valid but omits a preference key
- **THEN** the system SHALL use the compatibility default for that key (view=raw, evolution=off, 3D=off, sidebar=off)

### Requirement: Log retention days setting

The system SHALL read the log retention period from the `log_retention_days` key in the settings file.

#### Scenario: Missing key uses default

- **WHEN** the settings file does not contain `log_retention_days`
- **THEN** the system SHALL use `7` as the retention period

#### Scenario: Valid integer is used

- **WHEN** `log_retention_days` is an integer greater than or equal to `1`
- **THEN** the system SHALL use that value as the retention period

#### Scenario: Non-integer value falls back to default

- **WHEN** `log_retention_days` is a string, float, boolean, null, or another non-integer value
- **THEN** the system SHALL use `7` as the retention period

#### Scenario: Value below one falls back to default

- **WHEN** `log_retention_days` is an integer smaller than `1`
- **THEN** the system SHALL use `7` as the retention period

#### Scenario: Retention setting is read from the settings file

- **WHEN** the application starts in GUI mode
- **THEN** the effective retention value SHALL be read from `~/.config/b3-selic-pre/settings.json` (or the equivalent XDG/platform path)

### Requirement: Data de referência da última carga

As configurações SHALL persistir `data_referencia` com a data resolvida da última carga bem-sucedida. A chave SHALL ser atualizada por `atualizar`, pela preparação do `mcp` e por carga bem-sucedida da GUI; `consultar` e `exportar` NÃO SHALL alterá-la. A preparação do `mcp` SHALL atualizar mesmo com dados vindos do cache; carga sem dados NÃO SHALL atualizar.

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
