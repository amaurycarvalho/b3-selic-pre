## MODIFIED Requirements

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
