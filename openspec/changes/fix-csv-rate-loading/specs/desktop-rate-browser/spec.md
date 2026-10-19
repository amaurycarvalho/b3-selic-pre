## ADDED Requirements

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
