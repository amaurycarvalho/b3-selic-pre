# Spec Delta

## MODIFIED Requirements

### Requirement: Date-based rate query
The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date. The initial date SHALL be the last business day available in the calendar cache; without a calendar cache, only the weekend rule applies. A non-business date SHALL be resolved to the previous business day and the adjustment SHALL be announced in the status bar. When the evolution checkbox is checked, the system SHALL fetch rates for 5 resolved dates (base date and 7, 14, 21, 28 days prior, each resolved to a business day) on the first check of the current session. Dates older than 30 days are rejected in raw and consolidated modes; evolution mode is exempt when fetching historical data.

#### Scenario: User fetches rates for a valid date
- **WHEN** the user enters a valid date and starts the query
- **THEN** the system requests SELIC Pré reference rates for that date from the B3 endpoint

#### Scenario: User enters an invalid date
- **WHEN** the user enters a date that is not in `YYYY-MM-DD` format
- **THEN** the system rejects the query and displays a validation message without contacting B3

#### Scenario: Initial date is the last business day
- **WHEN** the application opens on a weekend or holiday and the calendar cache is available
- **THEN** the date field shows the last business day
- **THEN** no network request is made during tab construction

#### Scenario: Holiday date is adjusted with a warning
- **WHEN** the user enters a holiday and starts the query
- **THEN** the system uses the previous business day
- **THEN** the status bar identifies the holiday and the resolved date

#### Scenario: First evolution check fetches 5 dates
- **WHEN** the user checks "Evolução da curva" for the first time in a session and historical data has not been loaded yet
- **THEN** the system fetches rates for all 5 resolved dates using `GetDownloadFile` (historical) and `GetList` (base date if today)

#### Scenario: Subsequent evolution toggles only switch display
- **WHEN** the user unchecks and re-checks "Evolução da curva" after historical data has been loaded
- **THEN** the system switches the chart display without any network requests

#### Scenario: Date older than 30 days is rejected in raw/consolidated modes
- **WHEN** raw or consolidated mode is active and the entered date is more than 30 days in the past
- **THEN** the system shows "Data muito antiga. Informe uma data nos últimos 30 dias." and does not fetch
