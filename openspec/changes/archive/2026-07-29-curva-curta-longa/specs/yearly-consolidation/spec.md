## MODIFIED Requirements

### Requirement: GUI yearly toggle
The GUI SHALL provide radio buttons labeled "Curva curta", "Curva longa", and "Evolução da curva" that switch the chart display between raw mode (green line, TAXA × DU252), consolidated mode (blue menor_taxa line + red maior_taxa line), and evolution mode (5 superposed curves with quiver arrows).

#### Scenario: Raw mode shows detailed chart
- **WHEN** the "Curva curta" radio button is selected
- **THEN** the chart shows a green line plotting TAXA against DU252

#### Scenario: Consolidated mode shows envelope chart
- **WHEN** the "Curva longa" radio button is selected
- **THEN** the chart shows a blue line for menor_taxa and a red line for maior_taxa plotted against the year

#### Scenario: View state is preserved across data fetches
- **WHEN** the user fetches new data while consolidated mode is active
- **THEN** the new data is rendered in consolidated chart mode immediately
