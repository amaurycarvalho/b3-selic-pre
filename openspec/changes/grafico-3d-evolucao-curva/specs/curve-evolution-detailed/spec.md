## ADDED Requirements

### Requirement: 3D rendering mode available from detailed evolution
When the evolution checkbox and 3D checkbox are both ON and the "Detalhado" radio is selected, the system SHALL render the detailed evolution data as a 3D surface instead of 2D lines.

#### Scenario: 3D checkbox enables 3D detailed rendering
- **WHEN** evolution checkbox is ON
- **AND** 3D checkbox is ON
- **AND** "Detalhado" radio is selected
- **THEN** `render_3d_evolution(fig, historical_data, consolidated=False)` is called instead of `render_detailed_evolution`
