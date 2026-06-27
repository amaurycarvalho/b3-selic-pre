# Analysis Panel

## Purpose
Display AI analysis results with rich formatting in a resizable sidebar panel. TBD.

## Requirements

### Requirement: Section headers in analysis panel
The system SHALL display section headers within the analysis text panel.

#### Scenario: Header shown for each section
- **WHEN** analysis content is displayed in the sidebar
- **THEN** each section (CLASSE PRIMÁRIA, ESTRUTURA, QUALIDADE, INTENSIDADE) SHALL be preceded by a bold header

### Requirement: Rich-text formatting in analysis panel
The system SHALL use Text widget tags for visual formatting of analysis content.

#### Scenario: Bold headers
- **WHEN** section headers are displayed
- **THEN** they SHALL appear in bold with increased font size

#### Scenario: Colored confidence values
- **WHEN** confidence percentages are displayed
- **THEN** high confidence (≥80%) SHALL be shown in green, medium in orange, low in red

#### Scenario: Colored fact text
- **WHEN** fact descriptions mention positive/negative indicators
- **THEN** positive indicators SHALL be shown in green, negative in red, neutral in default color

### Requirement: Resizable sidebar via PanedWindow
The system SHALL allow the user to resize the analysis sidebar by dragging its left edge.

#### Scenario: Sidebar draggable edge
- **WHEN** the analysis sidebar is visible
- **THEN** the user SHALL be able to drag the edge between chart and sidebar to resize

#### Scenario: Sidebar hidden with PanedWindow
- **WHEN** the user unchecks "Análise"
- **THEN** the sidebar pane SHALL be removed from the PanedWindow and the chart SHALL fill the full width

#### Scenario: Sidebar shown with PanedWindow
- **WHEN** the user checks "Análise"
- **THEN** the sidebar pane SHALL be added to the PanedWindow at its default width (280px)
