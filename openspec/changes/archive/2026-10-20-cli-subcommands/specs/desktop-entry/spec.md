## MODIFIED Requirements

### Requirement: Desktop entry properties

The `.desktop` file SHALL define the application name, icon, and the `gui` subcommand as its launch command.

#### Scenario: Desktop entry contains mandatory fields
- **WHEN** the user inspects the `.desktop` file
- **THEN** it contains valid `Name`, `Exec`, `Icon`, `Type`, and `Categories` fields

#### Scenario: Desktop entry launches the GUI command
- **WHEN** the user inspects the `Exec` field
- **THEN** it invokes `b3-selic-pre gui` (or `python3 <script> gui` when running from source)

#### Scenario: Desktop entry uses the PNG as its icon
- **WHEN** the `.desktop` file is installed and displayed in the application menu
- **THEN** the menu entry shows `b3_selic_pre.png` as its icon

### Requirement: Programmatic shortcut creation

The system SHALL support creating the `.desktop` file programmatically via the CLI subcommand `criar-atalho` and via a GUI button, targeting the user's Desktop directory and `~/.local/share/applications/`.

#### Scenario: Create shortcut via CLI
- **WHEN** the user runs `b3-selic-pre criar-atalho`
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`

#### Scenario: Create shortcut via GUI button
- **WHEN** the user clicks "Criar Atalho Desktop" in the GUI
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
