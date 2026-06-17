## ADDED Requirements

### Requirement: Current-view CSV clipboard copy

The GUI SHALL provide a "Copiar dados" button that copies the currently displayed dataset as CSV to the system clipboard.

#### Scenario: Raw mode CSV copy

- **WHEN** the chart is in raw mode (consolidation toggle off) and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns `DU252,DC365,TAXA` matching the raw CLI output

#### Scenario: Consolidated mode CSV copy

- **WHEN** the chart is in consolidated mode (consolidation toggle on) and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns `ANO,MENOR_TAXA,MAIOR_TAXA` matching the yearly CLI output

#### Scenario: Button disabled when no data

- **WHEN** no rate data has been loaded
- **THEN** the "Copiar dados" button is disabled

#### Scenario: Status feedback after copy

- **WHEN** data is loaded and the user clicks "Copiar dados"
- **THEN** a status message confirms `Dados copiados para a área de transferência.`
