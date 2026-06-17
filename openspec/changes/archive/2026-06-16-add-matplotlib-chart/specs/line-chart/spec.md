## Purpose

Provide an interactive line chart for visualizing SELIC Pré rates in both raw form (rate vs. maturity) and yearly-consolidated form (min/max rate envelope by year).

## ADDED Requirements

### Requirement: Raw mode line chart
The system SHALL render a line chart with DC365 (dias corridos) on the X-axis and TAXA on the Y-axis when consolidation is off, using a green line.

#### Scenario: Raw chart is displayed on fetch
- **WHEN** the user fetches rates and the consolidate toggle is off
- **THEN** the chart shows a single green line plotting TAXA against DC365 for all fetched records

#### Scenario: Raw chart X-axis uses 30-day scale
- **WHEN** the raw chart is displayed
- **THEN** the X-axis shows tick marks at 30-day intervals (0, 30, 60, 90, ...)

### Requirement: Consolidated mode dual-line chart
The system SHALL render a chart with year on the X-axis and TAXA on the Y-axis when consolidation is on, showing menor_taxa in blue and maior_taxa in red.

#### Scenario: Consolidated chart shows two lines
- **WHEN** the consolidation toggle is on and rates are displayed
- **THEN** the chart shows a blue line for menor_taxa and a red line for maior_taxa, plotted against the year

#### Scenario: Y-axis auto-scales to data range
- **WHEN** the chart is rendered in either mode
- **THEN** the Y-axis range is automatically set to fit the displayed data with reasonable margins

### Requirement: Interactive zoom and pan
The system SHALL provide zoom and pan controls via the matplotlib navigation toolbar embedded in the GUI window.

#### Scenario: User zooms into a region
- **WHEN** the user uses the zoom tool on the chart
- **THEN** the chart axes re-scale to the selected region

#### Scenario: User resets the view
- **WHEN** the user clicks the home button on the toolbar
- **THEN** the chart returns to the original auto-scaled view

### Requirement: Chart-to-clipboard copy
The system SHALL provide a "Copiar gráfico" button that copies the current chart as an image to the system clipboard.

#### Scenario: User copies chart to clipboard
- **WHEN** the user clicks "Copiar gráfico" and the chart contains data
- **THEN** the chart image is placed on the system clipboard

#### Scenario: Copy button disabled without data
- **WHEN** no data has been fetched and the user clicks "Copiar gráfico"
- **THEN** the system prevents the copy and displays an informational message

### Requirement: Chart PNG export
The system SHALL provide an "Exportar PNG" button that saves the current chart as a PNG file via a file-save dialog.

#### Scenario: User exports chart as PNG
- **WHEN** the user clicks "Exportar PNG" and the chart contains data
- **THEN** a file-save dialog opens, and upon confirmation the chart is saved as a PNG image

#### Scenario: Export button disabled without data
- **WHEN** no data has been fetched and the user clicks "Exportar PNG"
- **THEN** the system prevents the export and displays an informational message
