## ADDED Requirements

### Requirement: GUI launches when no arguments given
When the user invokes `b3-selic-pre` without any arguments, the GUI SHALL launch instead of printing CSV to stdout.

#### Scenario: No arguments launches GUI
- **WHEN** user runs `b3-selic-pre` with no arguments
- **THEN** the GUI window SHALL open

#### Scenario: Arguments launch CLI mode
- **WHEN** user runs `b3-selic-pre` with any argument (date, `--yearly`, `--today`, `--version`, `--create-shortcut`)
- **THEN** the CLI mode SHALL be used (CSV output, version string, shortcut creation, etc.)

### Requirement: --today flag for today's CSV
The system SHALL provide a `--today` flag that prints today's reference rates as CSV to stdout, restoring the behavior of bare invocation before this change.

#### Scenario: --today prints today's rates
- **WHEN** user runs `b3-selic-pre --today`
- **THEN** today's reference rates SHALL be fetched and printed as CSV to stdout

#### Scenario: --today with other CLI flags
- **WHEN** user runs `b3-selic-pre --today --yearly`
- **THEN** today's rates SHALL be consolidated by year and printed as yearly CSV

### Requirement: --gui flag continues to work
The existing `--gui` flag SHALL continue to launch the GUI when explicitly passed.

#### Scenario: Explicit --gui launches GUI
- **WHEN** user runs `b3-selic-pre --gui`
- **THEN** the GUI window SHALL open

### Requirement: Desktop shortcut unchanged
The `--create-shortcut` command SHALL continue to generate desktop entries with `--gui` appended to the exec line.

#### Scenario: Shortcut contains --gui
- **WHEN** user runs `b3-selic-pre --create-shortcut`
- **THEN** the generated `.desktop` file SHALL contain `--gui` in its `Exec` line
