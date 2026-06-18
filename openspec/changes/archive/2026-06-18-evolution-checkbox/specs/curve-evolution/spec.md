## ADDED Requirements

### Requirement: Detailed evolution rendering as alternative view
The system SHALL provide `render_detailed_evolution(fig, date_rates)` alongside the existing `render_curve_evolution` as an alternative rendering path for curve evolution data, selected based on the active radio button when evolution is enabled.

#### Scenario: Detailed evolution is selected via radio button
- **WHEN** evolution checkbox is ON and "Detalhado" radio is selected
- **THEN** `render_detailed_evolution` is called instead of `render_curve_evolution`
