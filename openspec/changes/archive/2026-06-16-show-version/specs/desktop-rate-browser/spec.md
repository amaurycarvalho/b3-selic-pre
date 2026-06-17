## ADDED Requirements

### Requirement: Version display in title bar
The system SHALL display the application version in the GUI window title bar.

#### Scenario: Version shown in title
- **WHEN** the GUI window is created
- **THEN** the title bar contains the application version in the format `"B3 SELIC Pré v<version>"`

### Requirement: CLI --version flag
The system SHALL accept a `--version` flag in CLI mode that prints the application version and exits.

#### Scenario: --version prints version
- **WHEN** the user runs `b3_selic_pre.py --version`
- **THEN** the output is `"b3-selic-pre <version>"` and the program exits with code 0
