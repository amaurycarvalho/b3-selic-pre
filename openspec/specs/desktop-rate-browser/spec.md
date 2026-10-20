## Purpose

Provide a desktop interface for querying, viewing, copying, and exporting B3 SELIC Pré reference-rate data.

## Requirements

### Requirement: Date-based rate query
The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date. When the evolution checkbox is checked, the system SHALL fetch rates for 5 dates (base date and 7, 14, 21, 28 days prior) on the first check of the current session. Dates older than 30 days are rejected in raw and consolidated modes; evolution mode is exempt when fetching historical data.

#### Scenario: User fetches rates for a valid date
- **WHEN** the user enters a valid date and starts the query
- **THEN** the system requests SELIC Pré reference rates for that date from the B3 endpoint

#### Scenario: User enters an invalid date
- **WHEN** the user enters a date that is not in `YYYY-MM-DD` format
- **THEN** the system rejects the query and displays a validation message without contacting B3

#### Scenario: First evolution check fetches 5 dates
- **WHEN** the user checks "Evolução da curva" for the first time in a session and historical data has not been loaded yet
- **THEN** the system fetches rates for all 5 dates using `GetDownloadFile` (historical) and `GetList` (base date if today)

#### Scenario: Subsequent evolution toggles only switch display
- **WHEN** the user unchecks and re-checks "Evolução da curva" after historical data has been loaded
- **THEN** the system switches the chart display without any network requests

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
The chart SHALL respond to two independent controls: a radiobutton pair ("Detalhado", "Consolidado") selects the base view mode, and a checkbox ("Evolução da curva") toggles evolution overlay on or off. When evolution is ON, the chart SHALL display the evolution rendering corresponding to the active radio button (detailed evolution for "Detalhado", consolidated evolution for "Consolidado"). When evolution is OFF, the chart SHALL display the base view (raw or consolidated) without evolution data.

#### Scenario: Radio button switches between raw and consolidated
- **WHEN** the user selects "Detalhado" or "Consolidado" with evolution OFF
- **THEN** the chart immediately shows the corresponding base view without re-fetching data

#### Scenario: Evolution checkbox shows detailed evolution
- **WHEN** the user checks "Evolução da curva", historical data exists, and "Detalhado" is the active radio
- **THEN** the chart shows the 5-line detailed evolution rendering (DU252 × TAXA with gradient)

#### Scenario: Evolution checkbox shows consolidated evolution
- **WHEN** the user checks "Evolução da curva", historical data exists, and "Consolidado" is the active radio
- **THEN** the chart shows the 5-curve consolidated evolution rendering (average per year with quiver arrows)

#### Scenario: Evolution checkbox hides evolution
- **WHEN** the user unchecks "Evolução da curva"
- **THEN** the chart returns to the base view (raw or consolidated) without re-fetching data

#### Scenario: Radio switch changes evolution rendering
- **WHEN** evolution is ON and the user switches the radio from "Detalhado" to "Consolidado"
- **THEN** the chart switches from detailed evolution to consolidated evolution without re-fetching any data

#### Scenario: Evolution mode auto-sets date to today
- **WHEN** the user checks "Evolução da curva"
- **THEN** the date field automatically changes to today's date if it is not already today

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

### Requirement: GUI source selection by reference date

The system SHALL use the same source selection as the B3 rate source contract: the current date SHALL be fetched with `GetList`, and earlier dates SHALL be fetched with `GetDownloadFile` with `GetList` as fallback only after the CSV retries are exhausted. The GUI SHALL NOT present a transient empty response as a successful empty curve.

#### Scenario: Today is loaded from GetList
- **WHEN** the user searches for the current date in the GUI
- **THEN** the GUI loads the curve using `GetList`

#### Scenario: Earlier date is loaded from GetDownloadFile
- **WHEN** the user searches for an earlier date in the GUI and the CSV returns valid records
- **THEN** the GUI loads the curve from `GetDownloadFile`

#### Scenario: Persistent empty response shows an error
- **WHEN** the selected date remains empty after all retries and fallback
- **THEN** the GUI shows a communication error message and remains usable for another query

### Requirement: Empty or partial historical data does not break the GUI

When historical data is empty, partial, or missing one or more dates, the GUI SHALL remain usable and SHALL NOT raise an exception while redrawing the chart. If no usable historical date exists, the GUI SHALL fall back to the active base view (raw or consolidated) and display the empty-data message. If some dates are available, the GUI SHALL render the available curves and report the unavailable dates in the status bar.

#### Scenario: All historical dates are empty
- **WHEN** the evolution fetch returns no records for every date
- **THEN** the GUI shows the base view with the empty-data message and does not raise an exception

#### Scenario: Some historical dates are unavailable
- **WHEN** the evolution fetch returns records for at least one date but not for all five dates
- **THEN** the GUI renders the available curves and reports the unavailable dates in the status bar

#### Scenario: Partial historical data is not treated as complete
- **WHEN** a historical date has an incomplete record set
- **THEN** the GUI does not treat that result as complete and follows the retry and fallback policy

### Requirement: CLI source selection by reference date

The CLI SHALL use the same source selection as the GUI: the current date SHALL use `GetList`, and earlier dates SHALL use `GetDownloadFile` with `GetList` fallback. The CLI output format SHALL remain unchanged. A persistent communication failure SHALL exit with a non-zero status code and a clear message.

#### Scenario: CLI loads today from GetList
- **WHEN** the user runs the CLI for the current date
- **THEN** the CLI fetches and prints the rates from `GetList`

#### Scenario: CLI loads an earlier date from GetDownloadFile
- **WHEN** the user runs the CLI for an earlier date and the CSV returns valid records
- **THEN** the CLI prints the CSV-derived rates in the existing output format

#### Scenario: CLI reports a persistent communication failure
- **WHEN** the selected date remains empty after all retries and fallback
- **THEN** the CLI prints a clear error and exits with a non-zero status code
