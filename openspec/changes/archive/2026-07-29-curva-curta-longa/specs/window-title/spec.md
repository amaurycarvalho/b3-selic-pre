## MODIFIED Requirements

### Requirement: Dynamic window title
The system SHALL update the window title to reflect loaded data context.

#### Scenario: Title after successful load
- **WHEN** data is successfully loaded
- **THEN** the window title SHALL show the application name followed by the date and record count: `"Taxas Referenciais SELIC (B3) — 2026-06-27 — 312 registros"`

#### Scenario: Title on error
- **WHEN** data loading fails or data is cleared
- **THEN** the window title SHALL revert to the base `"Taxas Referenciais SELIC (B3) v{version}"`

#### Scenario: Title with historical data
- **WHEN** historical data is loaded
- **THEN** the window title SHALL show the date range: `"Taxas Referenciais SELIC (B3) — 5 datas, 1240 registros"`
