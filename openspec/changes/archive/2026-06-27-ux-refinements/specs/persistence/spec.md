## ADDED Requirements

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
- **THEN** the system SHALL use default values (date=today, view=raw, evolution=off, 3D=off, sidebar=off)

#### Scenario: Corrupt file uses defaults
- **WHEN** the settings file contains invalid JSON
- **THEN** the system SHALL use default values
