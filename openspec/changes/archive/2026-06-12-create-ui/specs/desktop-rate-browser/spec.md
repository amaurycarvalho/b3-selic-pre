## ADDED Requirements

### Requirement: Date-based rate query
The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date.

#### Scenario: User fetches rates for a valid date
- **WHEN** the user enters a valid date and starts the query
- **THEN** the system requests SELIC Pré reference rates for that date from the B3 endpoint

#### Scenario: User enters an invalid date
- **WHEN** the user enters a date that is not in `YYYY-MM-DD` format
- **THEN** the system rejects the query and displays a validation message without contacting B3

### Requirement: Tabular result display
The system SHALL display fetched SELIC Pré rates in a desktop table containing at least `day252`, `day360`, and `rate` columns.

#### Scenario: B3 returns rate records
- **WHEN** the B3 response contains one or more rate records
- **THEN** the system displays each record as a row in the results table

#### Scenario: B3 returns no rate records
- **WHEN** the B3 response contains no rate records
- **THEN** the system displays an empty-result message and leaves the table without stale rows

### Requirement: Request state feedback
The system SHALL provide visible desktop feedback for loading, successful completion, validation errors, and request failures.

#### Scenario: Request is in progress
- **WHEN** the system is waiting for a B3 response
- **THEN** the GUI indicates that loading is in progress and prevents duplicate concurrent fetches

#### Scenario: Request fails
- **WHEN** the B3 request fails or returns unexpected data
- **THEN** the GUI displays an error message and remains usable for another query

### Requirement: Export displayed rates
The system SHALL allow users to export or copy the currently displayed rate records in a tabular text format.

#### Scenario: User exports populated results
- **WHEN** the table contains rate records and the user chooses export or copy
- **THEN** the system produces tabular text containing headers and all displayed rows

#### Scenario: User exports without results
- **WHEN** the table contains no rate records and the user chooses export or copy
- **THEN** the system displays a message that there is no data to export

### Requirement: CLI behavior preservation
The system SHALL preserve a command-line path for fetching and printing SELIC Pré rates while adding the desktop GUI.

#### Scenario: User runs the command-line entry point
- **WHEN** the user runs the existing command-line workflow
- **THEN** the system prints SELIC Pré rate rows without requiring GUI interaction
