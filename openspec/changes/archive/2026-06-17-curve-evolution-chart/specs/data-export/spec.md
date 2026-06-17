## ADDED Requirements

### Requirement: Evolution mode CSV clipboard copy
The GUI SHALL, when in evolution mode, copy CSV data for all 7 dates when the user clicks "Copiar dados".

#### Scenario: Evolution mode copies 7-date CSV
- **WHEN** the chart is in evolution mode and the user clicks "Copiar dados"
- **THEN** the clipboard receives CSV with columns `DATA;ANO;TAXA_MEDIA` containing one row per year per date (7 dates × ~21 years ≈ 147 rows)

#### Scenario: Evolution CSV uses semicolon delimiter
- **WHEN** evolution CSV is copied
- **THEN** the CSV uses semicolon (`;`) as delimiter and period (`.`) as decimal separator
