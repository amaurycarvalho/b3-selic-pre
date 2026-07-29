## ADDED Requirements

### Requirement: CSV parsing with automatic dialect detection
The system SHALL parse the Treasury Direct CSV using the `csv` standard library module with automatic separator and dialect detection.

#### Scenario: CSV delimiter is detected automatically
- **WHEN** the CSV file is read
- **THEN** the system SHALL use `csv.Sniffer` to detect the delimiter (comma or semicolon)

#### Scenario: CSV encoding fallback is attempted
- **WHEN** reading the CSV with UTF-8 encoding fails
- **THEN** the system SHALL retry with Latin-1 encoding before raising an error

#### Scenario: Empty CSV raises error
- **WHEN** the downloaded CSV file is empty or contains only headers
- **THEN** the system SHALL raise a `ValueError` with message "Arquivo CSV está vazio."

### Requirement: Column mapping with case-insensitive matching
The system SHALL map CSV columns to `MovimentacaoTesouroDireto` fields using case-insensitive name matching with fallback for unknown columns.

#### Scenario: Expected columns are mapped correctly
- **WHEN** the CSV contains headers matching `data`, `titulo`, `venda`, `resgate`, `saldo`, `vencimento` (case-insensitive)
- **THEN** each row SHALL be converted to a `MovimentacaoTesouroDireto` instance

#### Scenario: Unknown columns are logged and ignored
- **WHEN** the CSV contains columns not in the expected set
- **THEN** the system SHALL log a warning with the column name and ignore that column

#### Scenario: Missing required column raises error
- **WHEN** a required column (`data`, `titulo`) is missing from the CSV headers
- **THEN** the system SHALL raise a `ValueError` identifying which column is missing

### Requirement: Data type conversion and validation
The system SHALL convert and validate CSV values to the appropriate Python types for each field.

#### Scenario: Date fields are standardized
- **WHEN** the `data` or `vencimento` column contains a date value
- **THEN** the system SHALL convert it to ISO 8601 format (YYYY-MM-DD)

#### Scenario: Monetary fields are converted to float
- **WHEN** the `venda`, `resgate`, or `saldo` column contains a numeric value
- **THEN** the system SHALL convert it to `float`, handling Brazilian locale formatting (comma as decimal separator, dot as thousands separator)

#### Scenario: Invalid numeric value raises error
- **WHEN** a monetary field contains a value that cannot be parsed as a number
- **THEN** the system SHALL raise a `ValueError` indicating the row and column where the error occurred

### Requirement: Data processing functions
The system SHALL provide pure functions in `application/tesouro/` for processing and transforming Tesouro Direto records.

#### Scenario: Records are filtered by titulo
- **WHEN** `filtrar_por_titulo(records, "Tesouro Selic 2029")` is called
- **THEN** it SHALL return only records whose `titulo` field matches the filter

#### Scenario: Records are filtered by date range
- **WHEN** `filtrar_por_periodo(records, "2026-01-01", "2026-06-30")` is called
- **THEN** it SHALL return only records with `data` within the inclusive range

#### Scenario: Records are aggregated by titulo
- **WHEN** `agregar_por_titulo(records)` is called
- **THEN** it SHALL return a dict mapping each titulo name to its total `venda`, `resgate`, and `saldo`
