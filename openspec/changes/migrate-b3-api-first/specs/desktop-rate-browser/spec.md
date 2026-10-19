## MODIFIED Requirements

### Requirement: Date-based rate query

The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date. The system SHALL use the B3 `GetList` API as the primary source, SHALL use `GetDate` to validate the available API window, and SHALL use the CSV download only as a temporary fallback for dates outside that window. When the evolution checkbox is checked, the system SHALL fetch rates for 5 dates (base date and 7, 14, 21, 28 days prior) on the first check of the current session. Dates older than 30 days are rejected in raw and consolidated modes; evolution mode is exempt when fetching historical data, subject to API availability and the temporary CSV fallback.

#### Scenario: User fetches rates for a valid date

- **WHEN** the user enters a valid date and starts the query
- **THEN** the system requests SELIC Pré reference rates for that date from the B3 API endpoint

#### Scenario: User enters an invalid date

- **WHEN** the user enters a date that is not in `YYYY-MM-DD` format
- **THEN** the system rejects the query and displays a validation message without contacting B3

#### Scenario: First evolution check fetches 5 dates

- **WHEN** the user checks "Evolução da curva" for the first time in a session and historical data has not been loaded yet
- **THEN** the system fetches rates for all 5 dates using `GetList` for dates in the `GetDate` window and the temporary CSV fallback for dates outside it

#### Scenario: Subsequent evolution toggles only switch display

- **WHEN** the user unchecks and re-checks "Evolução da curva" after historical data has been loaded
- **THEN** the system switches the chart display without any network requests

#### Scenario: Date older than 30 days is rejected in raw/consolidated modes

- **WHEN** raw or consolidated mode is active and the entered date is more than 30 days in the past
- **THEN** the system shows "Data muito antiga. Informe uma data nos últimos 30 dias." and does not fetch

#### Scenario: Date outside the API window uses fallback or is reported unavailable

- **WHEN** the user requests a date that is not in the `GetDate` window
- **THEN** the system attempts the temporary CSV fallback
- **AND** if the fallback is empty, the system reports that no data is available for that date

#### Scenario: API failure is not masked by the CSV fallback

- **WHEN** a date is in the `GetDate` window and the API fails after retries
- **THEN** the system displays an error message
- **AND** does not silently replace the API result with CSV data
