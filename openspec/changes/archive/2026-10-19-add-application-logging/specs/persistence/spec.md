## ADDED Requirements

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
