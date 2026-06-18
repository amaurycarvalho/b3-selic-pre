## MODIFIED Requirements

### Requirement: Date-based rate query
**Was**: The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date. In evolution mode, the system SHALL fetch rates for 5 dates (base date and 7, 14, 21, 28 days prior). Dates older than 30 days are rejected in raw and consolidated modes.

**Now**: The system SHALL provide a desktop GUI control for entering a B3 reference date in `YYYY-MM-DD` format and fetching SELIC Pré reference rates for that date. When the evolution checkbox is checked, the system SHALL fetch rates for 5 dates (base date and 7, 14, 21, 28 days prior) on the first check of the current session. Dates older than 30 days are rejected in raw and consolidated modes; evolution mode is exempt when fetching historical data.

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

### Requirement: Chart responds to view mode toggle
**Was**: The chart SHALL switch between raw mode (single green line), consolidated mode (dual lines), and curve evolution mode (5 superposed curves with quiver arrows) when the user selects the corresponding radio button, without re-fetching data when switching between raw and consolidated modes. Switching to evolution mode may trigger a historical data fetch if not already loaded.

**Now**: The chart SHALL respond to two independent controls: a radiobutton pair ("Detalhado", "Consolidado") selects the base view mode, and a checkbox ("Evolução da curva") toggles evolution overlay on or off. When evolution is ON, the chart SHALL display the evolution rendering corresponding to the active radio button (detailed evolution for "Detalhado", consolidated evolution for "Consolidado"). When evolution is OFF, the chart SHALL display the base view (raw or consolidated) without evolution data.

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
