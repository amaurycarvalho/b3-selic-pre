## MODIFIED Requirements

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
