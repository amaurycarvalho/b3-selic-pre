## ADDED Requirements

### Requirement: CLI subcommand for Tesouro Direto
The system SHALL provide a `--tesouro` flag in the CLI to query Treasury Direct movements.

#### Scenario: Tesouro flag with no arguments shows latest data
- **WHEN** the user runs `b3-selic-pre --tesouro`
- **THEN** the system SHALL fetch and display the most recent Treasury Direct movements in a tabular format

#### Scenario: Tesouro flag with titulo filter
- **WHEN** the user runs `b3-selic-pre --tesouro --titulo "Tesouro Selic 2029"`
- **THEN** the system SHALL display only movements for the specified titulo

#### Scenario: Tesouro flag with date range filter
- **WHEN** the user runs `b3-selic-pre --tesouro --inicio 2026-01-01 --fim 2026-06-30`
- **THEN** the system SHALL display only movements within the specified date range

#### Scenario: Tesouro flag with output format
- **WHEN** the user runs `b3-selic-pre --tesouro --json`
- **THEN** the system SHALL output the data in JSON format instead of tabular text

#### Scenario: Tesouro flag triggers download and cache
- **WHEN** the user runs any `--tesouro` command for the first time
- **THEN** the system SHALL download the CSV, cache it, and display the results

#### Scenario: Tesouro flag with force refresh
- **WHEN** the user runs `b3-selic-pre --tesouro --no-cache`
- **THEN** the system SHALL bypass cache and download fresh data from Tesouro Transparente

### Requirement: GUI tab for Tesouro Direto
The system SHALL provide a "Tesouro Direto" tab in the GUI application.

#### Scenario: Tesouro Direto tab is present in the GUI
- **WHEN** the GUI application starts
- **THEN** a tab labeled "Tesouro Direto" SHALL be available alongside existing tabs

#### Scenario: Tesouro Direto tab displays a data table
- **WHEN** the user clicks the "Tesouro Direto" tab and clicks "Atualizar"
- **THEN** a scrollable table (Treeview) SHALL display the movement records with columns: Data, Titulo, Venda, Resgate, Saldo, Vencimento

#### Scenario: Tesouro Direto tab shows loading state
- **WHEN** the user clicks "Atualizar" and data is being fetched
- **THEN** the tab SHALL display a progress bar and disable the update button until the fetch completes

#### Scenario: Tesouro Direto tab shows error state
- **WHEN** the data fetch fails (network error, parsing error)
- **THEN** the tab SHALL display the error message in red text in the status area

#### Scenario: Tesouro Direto tab shows cache indicator
- **WHEN** data is served from cache
- **THEN** the status area SHALL display "Fonte: Cache (data do download: YYYY-MM-DD HH:MM)"

#### Scenario: Tesouro Direto tab supports titulo filter
- **WHEN** the user selects a titulo from the dropdown in the tab
- **THEN** the table SHALL filter to show only records for that titulo

### Requirement: Formatted output for Tesouro Direto data
The system SHALL format Tesouro Direto records for display in both CLI tabular text and JSON formats.

#### Scenario: CLI output uses aligned columns
- **WHEN** the CLI displays Tesouro Direto data
- **THEN** columns SHALL be aligned with headers: Data, Titulo, Venda (R$), Resgate (R$), Saldo (R$), Vencimento

#### Scenario: Monetary values use Brazilian formatting
- **WHEN** monetary values are displayed in CLI output
- **THEN** they SHALL be formatted with dot as thousands separator and comma as decimal separator (e.g., `1.234.567,89`)

#### Scenario: JSON output includes metadata
- **WHEN** `--json` flag is used
- **THEN** the output SHALL include `fonte`, `data_extracao`, `total_registros`, and `periodo` metadata alongside the `registros` array

### Requirement: RFC-001 document updated
The system SHALL include an updated RFC-001 document reflecting the Clean Architecture redesign.

#### Scenario: RFC-001 references layered architecture
- **WHEN** the updated RFC-001 is read
- **THEN** it SHALL describe the feature in terms of domain, application, infrastructure, and presentation layers

#### Scenario: RFC-001 removes external dependency examples
- **WHEN** the updated RFC-001 is read
- **THEN** it SHALL use `urllib`, `csv`, and `json` in code examples instead of `requests`, `beautifulsoup4`, or `pandas`

#### Scenario: RFC-001 documents CKAN API approach
- **WHEN** the updated RFC-001 is read
- **THEN** it SHALL describe CKAN JSON API usage for dataset discovery instead of HTML scraping
