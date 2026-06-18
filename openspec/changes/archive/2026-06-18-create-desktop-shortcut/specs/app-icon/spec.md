## ADDED Requirements

### Requirement: Icon copy for shortcut
When creating a desktop shortcut, the system SHALL copy `b3_selic_pre.png` to `~/.local/share/icons/` for stable reference by the `.desktop` file.

#### Scenario: Icon copied during shortcut creation
- **WHEN** the user creates a shortcut (via CLI `--create-shortcut` or GUI button)
- **THEN** the icon file `b3_selic_pre.png` is copied to `~/.local/share/icons/b3-selic-pre.png`

#### Scenario: Icon source resolution in frozen mode
- **WHEN** the application is running as a compiled PyInstaller binary
- **AND** the user creates a shortcut
- **THEN** the icon is resolved from the PyInstaller bundle directory (`sys._MEIPASS`)

#### Scenario: Icon source resolution in script mode
- **WHEN** the application is running as a Python script
- **AND** the user creates a shortcut
- **THEN** the icon is resolved from the `icons/` directory relative to the script location
