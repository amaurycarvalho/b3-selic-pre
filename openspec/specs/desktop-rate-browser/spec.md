## Purpose

Provide a desktop interface for querying, viewing, copying, and exporting B3 SELIC Pré reference-rate data.

## Requirements

### Requirement: Date-based rate query
The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date. In evolution mode, the system SHALL fetch rates for 5 dates (base date and 7, 14, 21, 28 days prior). Dates older than 30 days are rejected in raw and consolidated modes.

#### Scenario: User fetches rates for a valid date
- **WHEN** the user enters a valid date and starts the query
- **THEN** the system requests SELIC Pré reference rates for that date from the B3 endpoint

#### Scenario: User enters an invalid date
- **WHEN** the user enters a date that is not in `YYYY-MM-DD` format
- **THEN** the system rejects the query and displays a validation message without contacting B3

#### Scenario: Fetch in evolution mode fetches 5 dates
- **WHEN** the evolution mode is active and the user clicks "Buscar"
- **THEN** the system fetches rates for all 5 dates using `GetDownloadFile` (historical) and `GetList` (base date if today)

#### Scenario: Date older than 30 days is rejected in raw/consolidated modes
- **WHEN** raw or consolidated mode is active and the entered date is more than 30 days in the past
- **THEN** the system shows "Data muito antiga. Informe uma data nos últimos 30 dias." and does not fetch

### Requirement: Chart display of rate data
The system SHALL display fetched SELIC Pré rates in a matplotlib line chart embedded in the GUI window, replacing the previous tabular view.

#### Scenario: Chart replaces table after fetch
- **WHEN** the B3 response contains one or more rate records
- **THEN** the chart displays the rate data according to the active view mode (raw or consolidated) and no table is shown

#### Scenario: Empty result shows message on chart area
- **WHEN** the B3 response contains no rate records
- **THEN** the chart area shows an empty-data message and no chart is rendered

### Requirement: Chart responds to view mode toggle
The chart SHALL switch between raw mode (single green line), consolidated mode (dual lines), and curve evolution mode (5 superposed curves with quiver arrows) when the user selects the corresponding radio button, without re-fetching data when switching between raw and consolidated modes. Switching to evolution mode may trigger a historical data fetch if not already loaded.

#### Scenario: Radio button switches to raw chart
- **WHEN** the user selects "Detalhado" after data has been fetched
- **THEN** the chart immediately shows the raw green line (TAXA × DU252)

#### Scenario: Radio button switches to consolidated chart
- **WHEN** the user selects "Consolidado" after data has been fetched
- **THEN** the chart immediately shows the blue/red min-max envelope

#### Scenario: Radio button switches to evolution chart with data
- **WHEN** the user selects "Evolução da curva" and historical data has already been fetched
- **THEN** the chart immediately shows the 5-curve evolution view

#### Scenario: Evolution mode auto-sets date to today
- **WHEN** the user selects "Evolução da curva"
- **THEN** the date field automatically changes to today's date

### Requirement: Chart image export
The system SHALL allow users to export the current chart image as a PNG file or copy it to the system clipboard.

#### Scenario: User exports chart with data
- **WHEN** the chart contains rendered data and the user clicks "Exportar PNG"
- **THEN** a file-save dialog opens and the chart is saved as a PNG upon confirmation

#### Scenario: User copies chart to clipboard
- **WHEN** the chart contains rendered data and the user clicks "Copiar gráfico"
- **THEN** the chart image is copied to the system clipboard

### Requirement: Request state feedback
The system SHALL provide visible desktop feedback for loading, successful completion, validation errors, and request failures. During evolution mode multi-date fetch, the status bar SHALL show detailed progress.

#### Scenario: Request is in progress
- **WHEN** the system is waiting for a B3 response
- **THEN** the GUI indicates that loading is in progress and prevents duplicate concurrent fetches

#### Scenario: Request fails
- **WHEN** the B3 request fails or returns unexpected data
- **THEN** the GUI displays an error message and remains usable for another query

#### Scenario: Progress shown during multi-date fetch
- **WHEN** the system is fetching 5 dates in evolution mode
- **THEN** the status bar shows "Buscando taxas históricas... (N/5 concluídas)" with N incrementing

#### Scenario: Evolution fetch error shows message
- **WHEN** one or more of the 5 historical fetches fail
- **THEN** the status bar shows an error message indicating the failed date(s) and the chart is not updated

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

### Requirement: Chart title positioned below toolbar
The chart title SHALL be positioned at `y=0.92` in all three view modes to avoid overlap with the matplotlib toolbar.

#### Scenario: Title is below toolbar in all modes
- **WHEN** the chart is rendered in any view mode (raw, consolidated, or evolution)
- **THEN** the title is positioned at `y=0.92` via `fig.suptitle(..., y=0.92)`

### Requirement: Date input with calendar picker
The date input field SHALL have a calendar button next to it that opens a popup DatePicker calendar for visual date selection.

#### Scenario: Calendar button opens DatePicker
- **WHEN** the user clicks the calendar button (📅) next to the date entry
- **THEN** a popup calendar window appears with month/year navigation and a clickable day grid

#### Scenario: DatePicker sets the date field
- **WHEN** the user clicks a day in the DatePicker
- **THEN** the date field is set to the selected date in `YYYY-MM-DD` format and the popup closes
