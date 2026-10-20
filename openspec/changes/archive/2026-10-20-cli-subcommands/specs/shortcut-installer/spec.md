## MODIFIED Requirements

### Requirement: CLI shortcut creation

The system SHALL provide a `criar-atalho` CLI subcommand that creates a `.desktop` shortcut and exits.

#### Scenario: Create shortcut via CLI
- **WHEN** the user runs `b3-selic-pre criar-atalho` (or the compiled binary equivalent)
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
- **AND** the program prints "Atalho criado em ~/Desktop/ e ~/.local/share/applications/" and exits

### Requirement: GUI shortcut button

When running in GUI mode, the system SHALL detect whether shortcuts exist in both `~/Desktop/` and `~/.local/share/applications/` and, if either is missing, show a "Criar Atalho Desktop" button.

#### Scenario: Button appears when no shortcut exists
- **WHEN** the user launches the GUI via `gui` or without arguments
- **AND** no `.desktop` file exists at either `~/Desktop/b3-selic-pre.desktop` or `~/.local/share/applications/b3-selic-pre.desktop`
- **THEN** a button labeled "Criar Atalho Desktop" is visible in the top frame

#### Scenario: Button appears when only applications entry exists
- **WHEN** the user launches the GUI via `gui` or without arguments
- **AND** a `.desktop` file exists at `~/.local/share/applications/b3-selic-pre.desktop`
- **AND** no `.desktop` file exists at `~/Desktop/b3-selic-pre.desktop`
- **THEN** a button labeled "Criar Atalho Desktop" is visible in the top frame

#### Scenario: Button is absent when both shortcuts exist
- **WHEN** the user launches the GUI via `gui` or without arguments
- **AND** `.desktop` files exist at both `~/Desktop/b3-selic-pre.desktop` and `~/.local/share/applications/b3-selic-pre.desktop`
- **THEN** the "Criar Atalho Desktop" button is NOT shown

#### Scenario: Button creates shortcut and disappears
- **WHEN** the user clicks "Criar Atalho Desktop"
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
- **AND** the button is removed from the GUI

### Requirement: Executable resolution

The system SHALL resolve the executable path correctly whether running as a Python script or a compiled PyInstaller binary.

#### Scenario: Running as Python script
- **WHEN** the script is run as `python3 /path/to/b3_selic_pre.py criar-atalho`
- **THEN** the `Exec` field in the generated `.desktop` SHALL be `python3 /path/to/b3_selic_pre.py gui`

#### Scenario: Running as compiled binary
- **WHEN** the compiled binary `/path/to/b3-selic-pre` is run with `criar-atalho`
- **THEN** the `Exec` field in the generated `.desktop` SHALL be `/path/to/b3-selic-pre gui`
