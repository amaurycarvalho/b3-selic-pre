## Purpose

Allow users to view SELIC Pré rates consolidated by year, showing minimum and maximum rates per year, in both CLI and GUI interfaces.

## Requirements

### Requirement: Yearly consolidation computation
The system SHALL provide a function that groups RateRecord instances by year (calculated as `day360 // 365`) and returns, for each year, the minimum and maximum rate values.

#### Scenario: Records spanning multiple years are consolidated
- **WHEN** given rate records with `day360` values spanning multiple years
- **THEN** each group of records sharing the same `day360 // 365` produces a single consolidated row containing `(year, min_rate, max_rate)`

#### Scenario: Single-year records produce one consolidated row
- **WHEN** given rate records where all `day360` values fall within the same year band
- **THEN** a single consolidated row is returned with the min and max of all rates

### Requirement: Average rate computation from consolidated data
The system SHALL provide a function `average_rate_by_year(records)` that computes the arithmetic mean of `min_rate` and `max_rate` for each year, using the output of `consolidate_by_year`.

#### Scenario: Average rate equals midpoint
- **WHEN** consolidated data contains `{year: 1, min_rate: 14.0, max_rate: 15.0}`
- **THEN** `average_rate_by_year` returns `{1: 14.5}`

### Requirement: CLI yearly consolidation flag
The CLI SHALL support a `--yearly` flag that, when present, outputs the consolidated-by-year table instead of the raw records.

#### Scenario: CLI with --yearly outputs consolidated CSV
- **WHEN** the user runs `b3_selic_pre.py <date> --yearly`
- **THEN** the output is a CSV with columns `ANO,MENOR_TAXA,MAIOR_TAXA`

#### Scenario: CLI without --yearly outputs raw records
- **WHEN** the user runs `b3_selic_pre.py <date>` without the `--yearly` flag
- **THEN** the output is the existing raw CSV format `DU252,DC365,TAXA`

### Requirement: GUI yearly toggle
The GUI SHALL provide radio buttons labeled "Detalhado", "Consolidado", and "Evolução da curva" that switch the chart display between raw mode (green line, TAXA × DU252), consolidated mode (blue menor_taxa line + red maior_taxa line), and evolution mode (5 superposed curves with quiver arrows).

#### Scenario: Raw mode shows detailed chart
- **WHEN** the "Detalhado" radio button is selected
- **THEN** the chart shows a green line plotting TAXA against DU252

#### Scenario: Consolidated mode shows envelope chart
- **WHEN** the "Consolidado" radio button is selected
- **THEN** the chart shows a blue line for menor_taxa and a red line for maior_taxa plotted against the year

#### Scenario: View state is preserved across data fetches
- **WHEN** the user fetches new data while consolidated mode is active
- **THEN** the new data is rendered in consolidated chart mode immediately

### Requirement: Consolidated chart Y-axis
The Y-axis SHALL auto-scale to fit both menor_taxa and maior_taxa lines, showing a clear visual envelope between the two.

#### Scenario: Dual lines with visible envelope
- **WHEN** the consolidated chart is displayed
- **THEN** the area between the blue and red lines forms a visible band, and the Y-axis range includes both lines with margins

### Requirement: Export and copy respect current view
The export/copy operations SHALL use whatever view mode (raw, consolidated, or evolution) is currently active.

#### Scenario: Copy in consolidated mode copies consolidated CSV
- **WHEN** consolidated mode is active and the user clicks "Copiar dados"
- **THEN** the clipboard receives consolidated CSV with columns ANO,MENOR_TAXA,MAIOR_TAXA

#### Scenario: Copy in raw mode copies raw CSV
- **WHEN** raw mode is active and the user clicks "Copiar dados"
- **THEN** the clipboard receives raw CSV with columns day252,day360,rate

#### Scenario: Copy in evolution mode copies evolution CSV
- **WHEN** evolution mode is active and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns DATA;ANO;TAXA_MEDIA in semicolon-delimited format
