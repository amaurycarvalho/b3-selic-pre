## MODIFIED Requirements

### Requirement: Chart responds to view mode toggle
**Was**: The chart SHALL switch between raw mode (single green line) and consolidated mode (dual lines) when the "Consolidar por ano" checkbox is toggled, without re-fetching data.

**Now**: The chart SHALL switch between raw mode (single green line), consolidated mode (dual lines), and curve evolution mode (5 superposed curves with quiver arrows) when the user selects the corresponding radio button, without re-fetching data when switching between raw and consolidated modes. Switching to evolution mode auto-sets the date to today and may trigger a historical data fetch if not already loaded.

#### Scenario: Radio button switches to raw chart
- **WHEN** the user selects "Detalhado" after data has been fetched
- **THEN** the chart immediately shows the raw green line (TAXA × DU252)

#### Scenario: Radio button switches to consolidated chart
- **WHEN** the user selects "Consolidado" after data has been fetched
- **THEN** the chart immediately shows the blue/red min-max envelope

#### Scenario: Radio button switches to evolution chart with data
- **WHEN** the user selects "Evolução da curva" and historical data has already been fetched
- **THEN** the chart immediately shows the 5-curve evolution view

#### Scenario: Evolution mode auto-sets date to today
- **WHEN** the user selects "Evolução da curva"
- **THEN** the date field automatically changes to today's date

### Requirement: Date-based rate query (evolution mode)
The system SHALL, when in evolution mode, fetch rates for 5 dates (base date and 7, 14, 21, 28 days prior) upon clicking "Buscar".

#### Scenario: Fetch in evolution mode fetches 5 dates
- **WHEN** the evolution mode is active and the user clicks "Buscar"
- **THEN** the system fetches rates for all 5 dates using `GetDownloadFile` (historical) and `GetList` (base date if today)

#### Scenario: Fetch in raw or consolidated mode fetches 1 date
- **WHEN** raw or consolidated mode is active and the user clicks "Buscar"
- **THEN** the system fetches rates for only the entered date (existing behavior)

#### Scenario: Date older than 30 days is rejected in raw/consolidated modes
- **WHEN** raw or consolidated mode is active and the entered date is more than 30 days in the past
- **THEN** the system shows "Data muito antiga. Informe uma data nos últimos 30 dias." and does not fetch

### Requirement: Request state feedback (evolution mode)
The system SHALL show detailed progress feedback when fetching historical data for evolution mode.

#### Scenario: Progress shown during multi-date fetch
- **WHEN** the system is fetching 5 dates in evolution mode
- **THEN** the status bar shows "Buscando taxas históricas... (N/5 concluídas)" with N incrementing

#### Scenario: Evolution fetch error shows message
- **WHEN** one or more of the 5 historical fetches fail
- **THEN** the status bar shows an error message indicating the failed date(s) and the chart is not updated

### Requirement: Chart title positioned below toolbar
**Was**: Chart title uses default matplotlib `suptitle` position (y ~ 0.98).

**Now**: Chart title is positioned at `y=0.92` in all three view modes to avoid overlap with the matplotlib toolbar.

### Requirement: Date input with calendar picker
**Was**: Date input is a plain text entry field for `YYYY-MM-DD`.

**Now**: Date input has a calendar button (📅) next to the text entry that opens a popup DatePicker calendar for visual date selection.
