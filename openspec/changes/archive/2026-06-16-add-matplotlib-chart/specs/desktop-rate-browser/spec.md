## Purpose

Provide a desktop interface for querying, viewing, copying, and exporting B3 SELIC Pré reference-rate data.

## ADDED Requirements

### Requirement: Chart display of rate data
The system SHALL display fetched SELIC Pré rates in a matplotlib line chart embedded in the GUI window, replacing the previous tabular view.

#### Scenario: Chart replaces table after fetch
- **WHEN** the B3 response contains one or more rate records
- **THEN** the chart displays the rate data according to the active view mode (raw or consolidated) and no table is shown

#### Scenario: Empty result shows message on chart area
- **WHEN** the B3 response contains no rate records
- **THEN** the chart area shows an empty-data message and no chart is rendered

### Requirement: Chart responds to consolidation toggle
The chart SHALL switch between raw mode (single green line) and consolidated mode (dual lines) when the "Consolidar por ano" checkbox is toggled, without re-fetching data.

#### Scenario: Toggling consolidation updates chart
- **WHEN** the user checks or unchecks the "Consolidar por ano" checkbox after data has been fetched
- **THEN** the chart immediately updates to reflect the corresponding mode

### Requirement: Chart image export
The system SHALL allow users to export the current chart image as a PNG file or copy it to the system clipboard.

#### Scenario: User exports chart with data
- **WHEN** the chart contains rendered data and the user clicks "Exportar PNG"
- **THEN** a file-save dialog opens and the chart is saved as a PNG upon confirmation

#### Scenario: User copies chart to clipboard
- **WHEN** the chart contains rendered data and the user clicks "Copiar gráfico"
- **THEN** the chart image is copied to the system clipboard

## REMOVED Requirements

### Requirement: Tabular result display
**Reason**: Tabular display replaced by matplotlib line chart for better visual analysis. Tabular data remains accessible via CLI (`--yearly` flag) and CSV export.
**Migration**: Use CLI mode or export-to-CSV for tabular data access.

### Requirement: Export displayed rates
**Reason**: Export/copy functionality migrated from text-based (CSV) to image-based (PNG/clipboard) in the GUI. CLI export remains unchanged.
**Migration**: Use CLI for CSV text export.
