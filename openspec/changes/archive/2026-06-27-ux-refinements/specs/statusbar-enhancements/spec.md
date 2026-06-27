## ADDED Requirements

### Requirement: Unicode severity icons in status messages
The system SHALL prefix statusbar messages with a Unicode icon matching the message type.

#### Scenario: Info messages show clock icon
- **WHEN** `set_status("Buscando taxas...")` is called with default type
- **THEN** the statusbar SHALL display "⏳ Buscando taxas..."

#### Scenario: Success messages show checkmark
- **WHEN** `set_status("Dados carregados.", msg_type="success")` is called
- **THEN** the statusbar SHALL display "✓ Dados carregados."

#### Scenario: Warning messages show warning icon
- **WHEN** `set_status("Data muito antiga.", msg_type="warning")` is called
- **THEN** the statusbar SHALL display "⚠ Data muito antiga."

#### Scenario: Error messages show cross mark
- **WHEN** `set_status("Erro ao buscar.", msg_type="error")` is called
- **THEN** the statusbar SHALL display "✖ Erro ao buscar."

### Requirement: Data source indicator
The system SHALL indicate the data source in the statusbar after loading.

#### Scenario: API source shown
- **WHEN** data is loaded from the B3 API (today's date)
- **THEN** the statusbar SHALL indicate "API B3"

#### Scenario: File download source shown
- **WHEN** data is loaded from the B3 file download (past dates)
- **THEN** the statusbar SHALL indicate "Arquivo oficial B3"

#### Scenario: Historical source shown
- **WHEN** historical data is loaded
- **THEN** the statusbar SHALL indicate "Histórico B3"

### Requirement: Last update timestamp
The system SHALL show the time of the last successful data load.

#### Scenario: Timestamp displayed after load
- **WHEN** data is successfully loaded
- **THEN** the statusbar SHALL display "Atualizado às HH:MM:SS"
