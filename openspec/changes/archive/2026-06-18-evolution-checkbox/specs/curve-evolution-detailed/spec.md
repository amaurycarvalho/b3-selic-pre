## ADDED Requirements

### Requirement: Detailed evolution chart rendering (DU252 × TAXA)
The system SHALL provide a function `render_detailed_evolution(fig, date_rates)` that plots 5 superposed lines of individual rate records (DU252 × TAXA) with gradient coloring and a date legend.

#### Scenario: Five detailed lines are plotted with green gradient
- **WHEN** `render_detailed_evolution` is called with data for 5 dates
- **THEN** the chart shows 5 lines in the range DU252 0–756, with the oldest curve having the lightest green color and the newest having the darkest green color

#### Scenario: Y-axis auto-scales to fit all data
- **WHEN** the detailed evolution chart is rendered
- **THEN** the Y-axis range is automatically set to include all 5 curves with margins

#### Scenario: X-axis ranges from DU252 0 to 756
- **WHEN** the detailed evolution chart is rendered
- **THEN** the X-axis shows integer ticks every 20 from 0 to 756

#### Scenario: Legend identifies each date
- **WHEN** the detailed evolution chart is rendered
- **THEN** the legend contains 5 entries showing each date in ISO format (YYYY-MM-DD)

#### Scenario: Empty data shows placeholder
- **WHEN** `render_detailed_evolution` is called with an empty `date_rates` dict
- **THEN** the chart shows "Sem dados" centered text
