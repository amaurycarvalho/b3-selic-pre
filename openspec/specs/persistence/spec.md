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
