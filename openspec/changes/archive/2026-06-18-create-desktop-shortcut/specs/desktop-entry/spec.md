## ADDED Requirements

### Requirement: Shortcut existence detection
The system SHALL detect whether the application shortcut is already installed in `~/.local/share/applications/b3-selic-pre.desktop`.

#### Scenario: Detect existing shortcut
- **WHEN** the file `~/.local/share/applications/b3-selic-pre.desktop` exists
- **THEN** the system reports the shortcut as installed

#### Scenario: Detect missing shortcut
- **WHEN** the file `~/.local/share/applications/b3-selic-pre.desktop` does not exist
- **THEN** the system reports the shortcut as not installed

### Requirement: Programmatic shortcut creation
The system SHALL support creating the `.desktop` file programmatically via CLI (`--create-shortcut`) and GUI button, targeting the user's Desktop directory and `~/.local/share/applications/`.

#### Scenario: Create shortcut via CLI
- **WHEN** the user runs `b3_selic_pre.py --create-shortcut`
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`

#### Scenario: Create shortcut via GUI button
- **WHEN** the user clicks "Criar Atalho Desktop" in the GUI
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
