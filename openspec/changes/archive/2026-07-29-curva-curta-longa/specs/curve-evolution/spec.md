## MODIFIED Requirements

### Requirement: Detailed evolution rendering as alternative view
The system SHALL provide `render_detailed_evolution(fig, date_rates)` alongside the existing `render_curve_evolution` as an alternative rendering path for curve evolution data, selected based on the active radio button when evolution is enabled.

#### Scenario: Detailed evolution is selected via radio button
- **WHEN** evolution checkbox is ON and "Curva curta" radio is selected
- **THEN** `render_detailed_evolution` is called instead of `render_curve_evolution`

### Requirement: 3D rendering mode available from consolidated evolution
When the evolution checkbox and 3D checkbox are both ON and the "Curva longa" radio is selected, the system SHALL render the consolidated evolution data as a 3D surface instead of 2D lines.

#### Scenario: 3D checkbox enables 3D consolidated rendering
- **WHEN** evolution checkbox is ON
- **AND** 3D checkbox is ON
- **AND** "Curva longa" radio is selected
- **THEN** `render_3d_evolution(fig, historical_data, consolidated=True)` is called instead of `render_curve_evolution`
