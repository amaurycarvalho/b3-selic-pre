## ADDED Requirements

### Requirement: Yearly consolidation computation
The system SHALL provide a function that groups RateRecord instances by year (calculated as `day360 // 365`) and returns, for each year, the minimum and maximum rate values.

#### Scenario: Records spanning multiple years are consolidated
- **WHEN** given rate records with `day360` values spanning multiple years
- **THEN** each group of records sharing the same `day360 // 365` produces a single consolidated row containing `(year, min_rate, max_rate)`

#### Scenario: Single-year records produce one consolidated row
- **WHEN** given rate records where all `day360` values fall within the same year band
- **THEN** a single consolidated row is returned with the min and max of all rates

### Requirement: CLI yearly consolidation flag
The CLI SHALL support a `--yearly` flag that, when present, outputs the consolidated-by-year table instead of the raw records.

#### Scenario: CLI with --yearly outputs consolidated CSV
- **WHEN** the user runs `b3_selic_pre.py <date> --yearly`
- **THEN** the output is a CSV with columns `ANO,MENOR_TAXA,MAIOR_TAXA`

#### Scenario: CLI without --yearly outputs raw records
- **WHEN** the user runs `b3_selic_pre.py <date>` without the `--yearly` flag
- **THEN** the output is the existing raw CSV format `DU252,DC365,TAXA`

### Requirement: GUI yearly toggle
The GUI SHALL provide a checkbox labeled "Consolidar por ano" that switches the table display between raw records and yearly-consolidated rows.

#### Scenario: Toggle is off (default) shows raw records
- **WHEN** the checkbox is unchecked
- **THEN** the table shows individual RateRecord rows with DU252, DC365, TAXA columns

#### Scenario: Toggle is on shows consolidated view
- **WHEN** the checkbox is checked
- **THEN** the table shows consolidated rows with columns ANO, MENOR TAXA, MAIOR TAXA

#### Scenario: Toggle state is preserved across data fetches
- **WHEN** the user fetches new data while the toggle is on
- **THEN** the new data is rendered in consolidated view immediately

### Requirement: Export and copy respect current view
The export/copy operations SHALL use whatever view mode (raw or consolidated) is currently active in the table.

#### Scenario: Copy in consolidated mode copies consolidated CSV
- **WHEN** the toggle is on and the user clicks "Copiar tabela"
- **THEN** the clipboard receives consolidated CSV with columns ANO,MENOR_TAXA,MAIOR_TAXA

#### Scenario: Copy in raw mode copies raw CSV
- **WHEN** the toggle is off and the user clicks "Copiar tabela"
- **THEN** the clipboard receives raw CSV with columns day252,day360,rate

## MODIFIED Requirements

### Requirement: Export displayed rates (modified)
The system SHALL allow users to export or copy the currently displayed rate records in a tabular text format, respecting the active view mode.

#### Scenario: User exports populated results (modified)
- **WHEN** the table contains rate records (raw or consolidated) and the user chooses export or copy
- **THEN** the system produces tabular text containing headers and all displayed rows, using the format matching the active view mode

#### Scenario: User exports without results (unchanged)
- **WHEN** the table contains no rate records and the user chooses export or copy
- **THEN** the system displays a message that there is no data to export
