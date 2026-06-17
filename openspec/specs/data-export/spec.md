## Purpose

Allow users to copy the raw data behind the current chart view (raw, consolidated, or evolution) as CSV to the system clipboard, for use in spreadsheets and external analysis tools.

## Requirements

### Requirement: Current-view CSV clipboard copy

The GUI SHALL provide a "Copiar dados" button that copies the currently displayed dataset as CSV to the system clipboard, respecting the active view mode.

#### Scenario: Raw mode CSV copy

- **WHEN** the chart is in raw mode and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns `DU252,DC365,TAXA` matching the raw CLI output

#### Scenario: Consolidated mode CSV copy

- **WHEN** the chart is in consolidated mode and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns `ANO,MENOR_TAXA,MAIOR_TAXA` matching the yearly CLI output

#### Scenario: Evolution mode CSV copy

- **WHEN** the chart is in evolution mode and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns `DATA;ANO;TAXA_MEDIA` containing one row per year per date (5 dates × ~21 years ≈ 105 rows), using semicolon delimiter and period decimal separator

#### Scenario: Button disabled when no data

- **WHEN** no rate data has been loaded
- **THEN** the "Copiar dados" button is disabled

#### Scenario: Status feedback after copy

- **WHEN** data is loaded and the user clicks "Copiar dados"
- **THEN** a status message confirms `Dados copiados para a área de transferência.`
