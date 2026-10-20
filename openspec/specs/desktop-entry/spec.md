## Purpose

Provide a FreeDesktop-compatible `.desktop` entry file so the application can be launched from the system application menu on Linux desktop environments.

## Requirements

### Requirement: Desktop entry file
The project SHALL include a `b3-selic-pre.desktop` file at the project root following the FreeDesktop Desktop Entry Specification.

#### Scenario: Desktop file exists at project root
- **WHEN** the user checks the project root directory
- **THEN** a file named `b3-selic-pre.desktop` is present

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

### Requirement: Shortcut existence detection
The system SHALL detect whether the application shortcut is already installed in `~/.local/share/applications/b3-selic-pre.desktop`.

#### Scenario: Detect existing shortcut
- **WHEN** the file `~/.local/share/applications/b3-selic-pre.desktop` exists
- **THEN** the system reports the shortcut as installed

#### Scenario: Detect missing shortcut
- **WHEN** the file `~/.local/share/applications/b3-selic-pre.desktop` does not exist
- **THEN** the system reports the shortcut as not installed

### Requirement: Programmatic shortcut creation

The system SHALL support creating the `.desktop` file programmatically via the CLI subcommand `criar-atalho` and via a GUI button, targeting the user's Desktop directory and `~/.local/share/applications/`.

#### Scenario: Create shortcut via CLI
- **WHEN** the user runs `b3-selic-pre criar-atalho`
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`

#### Scenario: Create shortcut via GUI button
- **WHEN** the user clicks "Criar Atalho Desktop" in the GUI
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
