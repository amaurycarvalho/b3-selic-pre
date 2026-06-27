# Buscar Cancel

## Purpose
Provide visual feedback on the fetch button during network operations. TBD.

## Requirements

### Requirement: Button text changes during fetch
The system SHALL change the "Buscar" button text to "Buscando…" while a fetch is in progress.

#### Scenario: Text changes on fetch start
- **WHEN** `fetch_rates()` begins a network operation
- **THEN** the button text SHALL change from "Buscar" to "Buscando…"

#### Scenario: Text restored on fetch end
- **WHEN** the fetch completes or fails
- **THEN** the button text SHALL return to "Buscar"
