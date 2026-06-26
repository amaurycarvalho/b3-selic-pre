## Purpose

Allow users to visualize how the SELIC Pré interest rate curve has moved over time by superimposing multiple detailed rate lines (Dias úteis × TAXA) with gradient coloring, one per historical date.

## Requirements

### Requirement: Detailed evolution chart rendering (Dias úteis × TAXA)
The system SHALL provide a function `render_detailed_evolution(fig, date_rates)` that plots 5 superposed lines of individual rate records (Dias úteis × TAXA) with gradient coloring, a date legend, and quiver arrows at minor tick positions showing rate change direction.

#### Scenario: Five detailed lines are plotted with green gradient
- **WHEN** `render_detailed_evolution` is called with data for 5 dates
- **THEN** the chart shows 5 lines in the range 0–756 Dias úteis, with the oldest curve having the lightest green color and the newest having the darkest green color

#### Scenario: X-axis label shows "Dias úteis"
- **WHEN** `render_detailed_evolution` is called with data
- **THEN** the X-axis label shows "Dias úteis"

#### Scenario: X-axis uses quarterly (~66 DU) scale
- **WHEN** `render_detailed_evolution` is called with data
- **THEN** the X-axis shows major tick marks at approximately 66-DU intervals with nearest-match to real data (tolerance 44), and dashed minor grid lines at approximately 22-DU intervals with nearest-match to real data (tolerance 22, excluding major positions)

#### Scenario: Quiver arrows show rate change direction at minor tick positions
- **WHEN** `render_detailed_evolution` is called with data containing rates at minor tick positions (~22 DU intervals)
- **THEN** the chart shows quiver arrows at those minor tick positions indicating the rate change direction between consecutive dates, using nearest-match per date for rate lookup (tolerance 22)
- **AND** at most one arrow is drawn per tick position, cycling through transitions by offset (oldest curve at offset 1, step 5)

#### Scenario: Y-axis auto-scales to fit all data
- **WHEN** the detailed evolution chart is rendered
- **THEN** the Y-axis range is automatically set to include all 5 curves with margins

#### Scenario: Legend identifies each date
- **WHEN** the detailed evolution chart is rendered
- **THEN** the legend contains 5 entries showing each date in ISO format (YYYY-MM-DD)

#### Scenario: Empty data shows placeholder
- **WHEN** `render_detailed_evolution` is called with an empty `date_rates` dict
- **THEN** the chart shows "Sem dados" centered text

### Requirement: 3D rendering mode available from detailed evolution
When the evolution checkbox and 3D checkbox are both ON and the "Detalhado" radio is selected, the system SHALL render the detailed evolution data as a 3D surface instead of 2D lines.

#### Scenario: 3D checkbox enables 3D detailed rendering
- **WHEN** evolution checkbox is ON
- **AND** 3D checkbox is ON
- **AND** "Detalhado" radio is selected
- **THEN** `render_3d_evolution(fig, historical_data, consolidated=False)` is called instead of `render_detailed_evolution`
