## Purpose

Allow users to view SELIC Pré rates consolidated by year, showing minimum and maximum rates per year, in both CLI and GUI interfaces.

## MODIFIED Requirements

### Requirement: GUI yearly toggle
The GUI SHALL provide a checkbox labeled "Consolidar por ano" that switches the chart display between raw mode (green line, TAXA × DC365) and consolidated mode (blue menor_taxa line + red maior_taxa line).

#### Scenario: Toggle is off (default) shows raw chart
- **WHEN** the checkbox is unchecked
- **THEN** the chart shows a green line plotting TAXA against DC365
- **PREVIOUSLY**: the table showed individual RateRecord rows

#### Scenario: Toggle is on shows consolidated chart
- **WHEN** the checkbox is checked
- **THEN** the chart shows a blue line for menor_taxa and a red line for maior_taxa plotted against the year
- **PREVIOUSLY**: the table showed rows with ANO, MENOR TAXA, MAIOR TAXA

#### Scenario: Toggle state is preserved across data fetches
- **WHEN** the user fetches new data while the toggle is on
- **THEN** the new data is rendered in consolidated chart mode immediately

## ADDED Requirements

### Requirement: Consolidated chart Y-axis
The Y-axis SHALL auto-scale to fit both menor_taxa and maior_taxa lines, showing a clear visual envelope between the two.

#### Scenario: Dual lines with visible envelope
- **WHEN** the consolidated chart is displayed
- **THEN** the area between the blue and red lines forms a visible band, and the Y-axis range includes both lines with margins
