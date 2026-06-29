# Loading State

## Purpose
Provide clear visual feedback during data fetch operations, including UI lock, wait cursor, and progress bars. TBD.

## Requirements

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
The system SHALL show a determinate progress bar during single-date API fetches, using a hybrid approach: indeterminate until the first page response reveals the total page count, then determinate for subsequent pages.

#### Scenario: Indeterminate bar shown before first page completes
- **WHEN** a single-date fetch starts
- **THEN** an indeterminate `ttk.Progressbar` SHALL be visible in the statusbar area

#### Scenario: Determinate bar shown after first page
- **WHEN** the first API page response is received and pagination metadata is available
- **THEN** the progress bar SHALL switch to determinate mode, with maximum set to total page count

#### Scenario: Progress bar updates on each page
- **WHEN** each subsequent page is fetched
- **THEN** the determinate bar SHALL advance by one step (current_page / total_pages)

#### Scenario: Progress bar hidden after fetch
- **WHEN** the fetch completes or fails
- **THEN** the progress bar SHALL be hidden

#### Scenario: Fallback to indeterminate when pagination metadata is missing
- **WHEN** the API response does not contain pagination metadata (`totalCount`)
- **THEN** the progress bar SHALL remain indeterminate for the entire fetch

### Requirement: Determinate progress for historical fetch
The system SHALL show a determinate progress bar during historical (7-step) fetches.

#### Scenario: Determinate bar shows progress
- **WHEN** fetching historical rates with a progress callback
- **THEN** a determinate `ttk.Progressbar` SHALL display the completion ratio (e.g., 3/7 → ~43%)

#### Scenario: Determinate bar hidden after fetch
- **WHEN** the historical fetch completes or fails
- **THEN** the determinate progress bar SHALL be hidden
