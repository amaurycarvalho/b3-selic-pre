## ADDED Requirements

### Requirement: MovimentacaoTesouroDireto dataclass
The system SHALL define a frozen dataclass `MovimentacaoTesouroDireto` in `domain/models.py` representing a single record of Treasury Direct movement.

#### Scenario: Dataclass is immutable
- **WHEN** a `MovimentacaoTesouroDireto` instance is created
- **THEN** its fields SHALL NOT be modifiable after creation

#### Scenario: Dataclass has all expected fields
- **WHEN** a `MovimentacaoTesouroDireto` is instantiated with `data`, `titulo`, `venda`, `resgate`, `saldo`, `vencimento`
- **THEN** all six fields SHALL be accessible as attributes

#### Scenario: Monetary fields use float type
- **WHEN** `venda`, `resgate`, and `saldo` values are provided
- **THEN** they SHALL be stored as `float` type

#### Scenario: Date fields use string type
- **WHEN** `data` and `vencimento` values are provided
- **THEN** they SHALL be stored as `str` type in YYYY-MM-DD format

### Requirement: Domain constants for Tesouro Direto
The system SHALL define constants in `domain/constants.py` for the Tesouro Direto data source configuration.

#### Scenario: Base URL constant is defined
- **WHEN** code references `TESOURO_BASE_URL`
- **THEN** it SHALL resolve to `https://www.tesourotransparente.gov.br/ckan`

#### Scenario: Dataset ID constant is defined
- **WHEN** code references `TESOURO_DATASET_ID`
- **THEN** it SHALL resolve to `vendas-do-tesouro-direto`

#### Scenario: Cache TTL constant is defined
- **WHEN** code references `TESOURO_CACHE_TTL_MINUTES`
- **THEN** it SHALL resolve to `360` (6 hours)
