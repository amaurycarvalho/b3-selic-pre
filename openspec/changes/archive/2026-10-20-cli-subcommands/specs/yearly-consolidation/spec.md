## MODIFIED Requirements

### Requirement: CLI yearly consolidation flag

The CLI SHALL expose yearly consolidation through `consultar --curva longa`. When `--curva curta` is used or `--curva` is omitted, the CLI SHALL output the raw records.

#### Scenario: CLI with --yearly outputs consolidated CSV
- **WHEN** the user runs `b3-selic-pre consultar --data 2026-06-10 --curva longa`
- **THEN** the output is a CSV with columns `ANO,MENOR_TAXA,MAIOR_TAXA`

#### Scenario: CLI without --yearly outputs raw records
- **WHEN** the user runs `b3-selic-pre consultar --data 2026-06-10` with `--curva` omitted or set to `curta`
- **THEN** the output is the raw CSV format `DU252,DC365,TAXA`
