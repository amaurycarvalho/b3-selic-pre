# Chart Enhancements

## Purpose
Add statistics summary, improved empty state, and update feedback to the chart area. TBD.

## Requirements

### Requirement: Quick statistics row above chart
The system SHALL display a compact statistics row between the top controls and the chart area when data is loaded.

#### Scenario: Stats shown on data load
- **WHEN** data is successfully loaded
- **THEN** a single-line frame above the chart SHALL display: date, record count, highest rate, lowest rate, maturity count

#### Scenario: Stats hidden when no data
- **WHEN** no data is loaded (startup, error, cleared)
- **THEN** the statistics row SHALL be hidden

#### Scenario: Stats updated on view change
- **WHEN** the user switches between raw and consolidated view
- **THEN** the displayed statistics SHALL reflect the current view

### Requirement: Informative empty chart placeholder
The system SHALL show a descriptive message in the chart area when no data is loaded.

#### Scenario: Detailed placeholder on empty state
- **WHEN** no data is loaded
- **THEN** the chart area SHALL display "Nenhum dado carregado.\nInforme uma data e clique em Buscar." centered in gray

### Requirement: Chart update status feedback
The system SHALL show a brief status message when the chart is being redrawn.

#### Scenario: Status message on chart update
- **WHEN** the chart is being redrawn (view toggle, evolution toggle)
- **THEN** the statusbar SHALL briefly display "Atualizando gráfico..."
