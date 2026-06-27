## ADDED Requirements

### Requirement: Full UI lock during loading
The system SHALL disable all interactive controls during data fetch operations.

#### Scenario: All controls disabled during fetch
- **WHEN** `fetch_rates()` is called and a network operation starts
- **THEN** the date entry, calendar button, "Buscar" button, radio buttons, checkboxes, copy/export buttons, and "Hoje" button SHALL be disabled

#### Scenario: Controls restored after fetch completes
- **WHEN** data is loaded or an error occurs
- **THEN** all controls SHALL be restored to their appropriate enabled/disabled state based on available data

### Requirement: Wait cursor during loading
The system SHALL display a wait cursor while a network operation is in progress.

#### Scenario: Watch cursor shown during fetch
- **WHEN** `fetch_rates()` begins a network operation
- **THEN** the root window cursor SHALL change to `"watch"`

#### Scenario: Default cursor restored after fetch
- **WHEN** data loading completes or fails
- **THEN** the root window cursor SHALL return to the default `""`

### Requirement: Indeterminate progress for single fetch
The system SHALL show an indeterminate progress bar during single-date API or file fetches.

#### Scenario: Indeterminate bar visible during single fetch
- **WHEN** fetching rates for a single date
- **THEN** an indeterminate `ttk.Progressbar` SHALL be visible in the statusbar area

#### Scenario: Progress bar hidden after fetch
- **WHEN** the fetch completes or fails
- **THEN** the indeterminate progress bar SHALL be hidden

### Requirement: Determinate progress for historical fetch
The system SHALL show a determinate progress bar during historical (7-step) fetches.

#### Scenario: Determinate bar shows progress
- **WHEN** fetching historical rates with a progress callback
- **THEN** a determinate `ttk.Progressbar` SHALL display the completion ratio (e.g., 3/7 → ~43%)

#### Scenario: Determinate bar hidden after fetch
- **WHEN** the historical fetch completes or fails
- **THEN** the determinate progress bar SHALL be hidden
