## MODIFIED Requirements

### Requirement: Curve evolution chart rendering
The system SHALL provide a function `render_curve_evolution(fig, date_rates)` that plots 5 superposed curves of average rate per year, with gradient coloring and quiver arrows at key maturities.

#### Scenario: Five curves with gradient are plotted
- **WHEN** `render_curve_evolution` is called with data for 5 dates
- **THEN** the chart shows 5 lines in the range years 0-20, with the oldest curve having the lightest color and the newest (base date) having the darkest color

#### Scenario: Quiver arrows at key maturities
- **WHEN** the evolution chart is rendered
- **THEN** quiver arrows are drawn at maturities 0, 1, 2, 3, 5, 10, 15, 20 showing consecutive rate transitions from oldest to newest date
- **AND** at most one arrow is drawn per tick position, cycling through transitions by offset (offset 1, step 5)

#### Scenario: Arrow direction indicates rate movement
- **WHEN** rates increased between consecutive dates at a given maturity
- **THEN** the arrow at that maturity points upward (positive V component)
- **WHEN** rates decreased
- **THEN** the arrow points downward (negative V component)

#### Scenario: Base date curve is visually prominent
- **WHEN** the evolution chart is rendered
- **THEN** the base date curve uses a solid line with width >= 2.0 and full opacity

#### Scenario: Historical curves use fading alpha
- **WHEN** the evolution chart is rendered
- **THEN** each historical curve has lower alpha and thinner line width than the next more recent curve

#### Scenario: Y-axis auto-scales to fit all data
- **WHEN** the evolution chart is rendered
- **THEN** the Y-axis range is automatically set to include all 5 curves with margins

#### Scenario: X-axis ranges from year 0 to year 20
- **WHEN** the evolution chart is rendered
- **THEN** the X-axis shows integer ticks from 0 to 20

### Requirement: Legend identifies each date
The evolution chart SHALL display a legend mapping each line color/alpha to its date label.

#### Scenario: Legend shows date labels
- **WHEN** the evolution chart is rendered
- **THEN** the legend contains 5 entries showing each date in ISO format (YYYY-MM-DD)

### Requirement: Detailed evolution rendering as alternative view
The system SHALL provide `render_detailed_evolution(fig, date_rates)` alongside the existing `render_curve_evolution` as an alternative rendering path for curve evolution data, selected based on the active radio button when evolution is enabled.

#### Scenario: Detailed evolution is selected via radio button
- **WHEN** evolution checkbox is ON and "Detalhado" radio is selected
- **THEN** `render_detailed_evolution` is called instead of `render_curve_evolution`
