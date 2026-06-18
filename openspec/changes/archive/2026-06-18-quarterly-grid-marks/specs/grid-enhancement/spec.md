## ADDED Requirements

### Requirement: Grid lines at 90-DU intervals on detailed charts (major, solid)
The system SHALL display solid vertical grid lines every 90 DU on raw detailed charts and detailed evolution charts to provide quarterly visual reference marks. The existing 20-DU grid lines SHALL be displayed as dashed, subtle (minor) grid lines.

#### Scenario: Detailed chart shows quarterly major grid
- **WHEN** a detailed chart (raw or detailed evolution) is rendered with data
- **THEN** the x-axis has major ticks at every 90 DU from 90 to 720, with solid grid lines at alpha 0.3

#### Scenario: 20-DU grid becomes minor dashed
- **WHEN** a detailed chart is rendered
- **THEN** the x-axis has minor ticks at every 20 DU (excluding multiples of 90), with dashed grid lines at alpha 0.15, linestyle "--"

### Requirement: Grid lines at 3-year intervals on consolidated charts (major, solid)
The system SHALL display solid vertical grid lines every 3 years on consolidated charts and consolidated evolution charts to provide triennial visual reference marks. The existing 1-year grid lines SHALL be displayed as dashed, subtle (minor) grid lines.

#### Scenario: Consolidated chart shows triennial major grid
- **WHEN** a consolidated chart (yearly or consolidated evolution) is rendered with data
- **THEN** the x-axis has major ticks at every 3 years from 0 to 18, with solid grid lines at alpha 0.3

#### Scenario: Annual grid becomes minor dashed
- **WHEN** a consolidated chart is rendered
- **THEN** the x-axis has minor ticks at every year (excluding 0, 3, 6, 9, 12, 15, 18), with dashed grid lines at alpha 0.15, linestyle "--"
