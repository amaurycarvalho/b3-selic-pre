## ADDED Requirements

### Requirement: Date-based rate query form

The system SHALL provide a browser UI that lets users enter or select a reference date for a B3 SELIC pré rate query.

#### Scenario: User opens the UI

- **WHEN** the user opens the local UI in a browser
- **THEN** the system displays a date input and an action to fetch rates

#### Scenario: User submits a valid date

- **WHEN** the user submits a valid `YYYY-MM-DD` reference date
- **THEN** the system requests B3 SELIC pré rates for that date

### Requirement: Rate results table

The system SHALL display returned B3 SELIC pré rate rows in a table that includes the 252-day count, 360-day count, and rate value for each row.

#### Scenario: Rates are returned

- **WHEN** B3 returns one or more rate rows
- **THEN** the system displays each row with its `day252`, `day360`, and `rate` values

#### Scenario: No rates are returned

- **WHEN** B3 returns no rate rows for the selected date
- **THEN** the system displays an empty-results message instead of an empty table

### Requirement: Query state feedback

The system SHALL communicate loading, validation, and fetch failure states in the browser UI.

#### Scenario: Query is loading

- **WHEN** a rate query is in progress
- **THEN** the system displays a loading state and prevents duplicate submissions for the same in-flight request

#### Scenario: Date input is invalid

- **WHEN** the user submits an empty or invalid reference date
- **THEN** the system displays a validation error without sending a B3 request

#### Scenario: B3 request fails

- **WHEN** the local service cannot retrieve or parse B3 rate data
- **THEN** the system displays an error message that does not expose a traceback

### Requirement: Local JSON query endpoint

The system SHALL provide a local JSON endpoint that accepts a reference date and returns normalized B3 SELIC pré rate data for the UI.

#### Scenario: Endpoint receives a valid date

- **WHEN** the endpoint receives a valid `YYYY-MM-DD` reference date
- **THEN** the endpoint returns JSON containing a `results` array of rate rows

#### Scenario: Endpoint receives an invalid date

- **WHEN** the endpoint receives an invalid reference date
- **THEN** the endpoint returns a client error response with a clear error message
