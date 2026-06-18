## MODIFIED Requirements

### Requirement: Raw mode line chart
The system SHALL render a line chart with "Dias úteis" on the X-axis and TAXA on the Y-axis when consolidation is off, using a green line.

#### Scenario: Raw chart x-axis label shows "Dias úteis"
- **WHEN** the raw chart is displayed
- **THEN** the X-axis label shows "Dias úteis"

#### Scenario: Raw chart X-axis uses quarterly (~66 DU) scale
- **WHEN** the raw chart is displayed
- **THEN** the X-axis shows major tick marks at approximately 66-DU intervals with nearest-match to real data (tolerance 44), and dashed minor grid lines at approximately 22-DU intervals with nearest-match to real data (tolerance 22, excluding major positions)

## REMOVED Requirements

### Requirement: Raw chart X-axis uses 20-day scale
**Reason**: Replaced by quarterly (60-DU) major scale with 20-DU minor grid
**Migration**: X-axis now uses 60-DU major ticks with 20-DU dashed minor grid lines
