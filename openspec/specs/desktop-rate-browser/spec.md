## Purpose

Provide a desktop interface for querying, viewing, copying, and exporting B3 SELIC Pré reference-rate data.

## Requirements

### Requirement: Date-based rate query
The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date.

#### Scenario: User fetches rates for a valid date
- **WHEN** the user enters a valid date and starts the query
- **THEN** the system requests SELIC Pré reference rates for that date from the B3 endpoint

#### Scenario: User enters an invalid date
- **WHEN** the user enters a date that is not in `YYYY-MM-DD` format
- **THEN** the system rejects the query and displays a validation message without contacting B3

### Requirement: Chart display of rate data
The system SHALL display fetched SELIC Pré rates in a matplotlib line chart embedded in the GUI window, replacing the previous tabular view.

#### Scenario: Chart replaces table after fetch
- **WHEN** the B3 response contains one or more rate records
- **THEN** the chart displays the rate data according to the active view mode (raw or consolidated) and no table is shown

#### Scenario: Empty result shows message on chart area
- **WHEN** the B3 response contains no rate records
- **THEN** the chart area shows an empty-data message and no chart is rendered

### Requirement: Chart responds to consolidation toggle
The chart SHALL switch between raw mode (single green line) and consolidated mode (dual lines) when the "Consolidar por ano" checkbox is toggled, without re-fetching data.

#### Scenario: Toggling consolidation updates chart
- **WHEN** the user checks or unchecks the "Consolidar por ano" checkbox after data has been fetched
- **THEN** the chart immediately updates to reflect the corresponding mode

### Requirement: Chart image export
The system SHALL allow users to export the current chart image as a PNG file or copy it to the system clipboard.

#### Scenario: User exports chart with data
- **WHEN** the chart contains rendered data and the user clicks "Exportar PNG"
- **THEN** a file-save dialog opens and the chart is saved as a PNG upon confirmation

#### Scenario: User copies chart to clipboard
- **WHEN** the chart contains rendered data and the user clicks "Copiar gráfico"
- **THEN** the chart image is copied to the system clipboard

### Requirement: Request state feedback
The system SHALL provide visible desktop feedback for loading, successful completion, validation errors, and request failures.

#### Scenario: Request is in progress
- **WHEN** the system is waiting for a B3 response
- **THEN** the GUI indicates that loading is in progress and prevents duplicate concurrent fetches

#### Scenario: Request fails
- **WHEN** the B3 request fails or returns unexpected data
- **THEN** the GUI displays an error message and remains usable for another query

### Requirement: CLI behavior preservation
The system SHALL preserve a command-line path for fetching and printing SELIC Pré rates while adding the desktop GUI.

#### Scenario: User runs the command-line entry point
- **WHEN** the user runs the existing command-line workflow
- **THEN** the system prints SELIC Pré rate rows without requiring GUI interaction

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
