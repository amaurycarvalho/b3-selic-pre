## ADDED Requirements

### Requirement: 3D rendering mode available from consolidated evolution
When the evolution checkbox and 3D checkbox are both ON and the "Consolidado" radio is selected, the system SHALL render the consolidated evolution data as a 3D surface instead of 2D lines.

#### Scenario: 3D checkbox enables 3D consolidated rendering
- **WHEN** evolution checkbox is ON
- **AND** 3D checkbox is ON
- **AND** "Consolidado" radio is selected
- **THEN** `render_3d_evolution(fig, historical_data, consolidated=True)` is called instead of `render_curve_evolution`
