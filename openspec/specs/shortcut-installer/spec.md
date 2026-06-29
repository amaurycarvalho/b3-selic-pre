## Purpose

Provide a programmatic mechanism to install a FreeDesktop-compatible `.desktop` shortcut on the user's desktop and application menu, so the application can be launched conveniently without manual setup.

## Requirements

### Requirement: CLI shortcut creation
The system SHALL provide a `--create-shortcut` CLI argument that creates a `.desktop` shortcut and exits.

#### Scenario: Create shortcut via CLI
- **WHEN** the user runs `b3_selic_pre.py --create-shortcut` (or the compiled binary equivalent)
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
- **AND** the program prints "Atalho criado em ~/Desktop/ e ~/.local/share/applications/" and exits

### Requirement: GUI shortcut button
When running in GUI mode, the system SHALL detect whether shortcuts exist in both `~/Desktop/` and `~/.local/share/applications/` and, if either is missing, show a "Criar Atalho Desktop" button.

#### Scenario: Button appears when no shortcut exists
- **WHEN** the user launches the GUI via `--gui`
- **AND** no `.desktop` file exists at either `~/Desktop/b3-selic-pre.desktop` or `~/.local/share/applications/b3-selic-pre.desktop`
- **THEN** a button labeled "Criar Atalho Desktop" is visible in the top frame

#### Scenario: Button appears when only applications entry exists
- **WHEN** the user launches the GUI via `--gui`
- **AND** a `.desktop` file exists at `~/.local/share/applications/b3-selic-pre.desktop`
- **AND** no `.desktop` file exists at `~/Desktop/b3-selic-pre.desktop`
- **THEN** a button labeled "Criar Atalho Desktop" is visible in the top frame

#### Scenario: Button is absent when both shortcuts exist
- **WHEN** the user launches the GUI via `--gui`
- **AND** `.desktop` files exist at both `~/Desktop/b3-selic-pre.desktop` and `~/.local/share/applications/b3-selic-pre.desktop`
- **THEN** the "Criar Atalho Desktop" button is NOT shown

#### Scenario: Button creates shortcut and disappears
- **WHEN** the user clicks "Criar Atalho Desktop"
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
- **AND** the button is removed from the GUI

### Requirement: Shortcut display name
The generated `.desktop` file SHALL set `Name=Taxas Referenciais SELIC (B3)`.

#### Scenario: Name set correctly
- **WHEN** the user inspects the generated `.desktop` file
- **THEN** the `Name` field reads "Taxas Referenciais SELIC (B3)"

### Requirement: Shortcut categories
The generated `.desktop` file SHALL set `Categories=Finance;Office;`.

#### Scenario: Categories set correctly
- **WHEN** the user inspects the generated `.desktop` file
- **THEN** the `Categories` field includes both "Finance" and "Office"

### Requirement: Executable resolution
The system SHALL resolve the executable path correctly whether running as a Python script or a compiled PyInstaller binary.

#### Scenario: Running as Python script
- **WHEN** the script is run as `python3 /path/to/b3_selic_pre.py --create-shortcut`
- **THEN** the `Exec` field in the generated `.desktop` SHALL be `python3 /path/to/b3_selic_pre.py --gui`

#### Scenario: Running as compiled binary
- **WHEN** the compiled binary `/path/to/b3-selic-pre` is run with `--create-shortcut`
- **THEN** the `Exec` field in the generated `.desktop` SHALL be `/path/to/b3-selic-pre --gui`

### Requirement: Desktop directory detection
The system SHALL detect the user's Desktop directory using XDG conventions, supporting localized directory names.

#### Scenario: Portuguese locale
- **WHEN** the system locale is pt-BR and `xdg-user-dir` reports `~/Área de Trabalho`
- **THEN** the `.desktop` file is created in `~/Área de Trabalho/`

#### Scenario: English locale fallback
- **WHEN** `xdg-user-dir` is not available and `~/.config/user-dirs.dirs` does not define `XDG_DESKTOP_DIR`
- **THEN** the system falls back to `~/Desktop/`

### Requirement: Icon installation
The system SHALL copy the application icon to `~/.local/share/icons/` and reference it with an absolute path in the `.desktop` file.

#### Scenario: Icon copied and referenced
- **WHEN** the shortcut is created
- **THEN** `b3-selic-pre.png` is copied to `~/.local/share/icons/b3-selic-pre.png`
- **AND** the `Icon` field in the `.desktop` file points to that absolute path
