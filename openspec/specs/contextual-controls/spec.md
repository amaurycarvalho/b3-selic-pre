# Contextual Controls

## Purpose
Dynamically enable or disable UI controls based on available data context. TBD.

## Requirements

### Requirement: Contextual enable/disable of controls
The system SHALL dynamically enable or disable controls based on available data context.

#### Scenario: 3D disabled without historical data
- **WHEN** no historical data is loaded
- **THEN** the "3D" checkbox SHALL be disabled

#### Scenario: Consolidated disabled without data
- **WHEN** no records are loaded
- **THEN** the "Consolidado" radio button SHALL be disabled (but "Detalhado" remains enabled)

#### Scenario: Evolution disabled when date is too recent
- **WHEN** the entered date has no historical data available (system knows historical fetch will fail)
- **THEN** the "Evolução da curva" checkbox SHALL be disabled and show a tooltip explaining why

#### Scenario: Analysis disabled without data
- **WHEN** no records are loaded
- **THEN** the "Análise" checkbox SHALL be disabled

#### Scenario: Controls enabled when data becomes available
- **WHEN** data is loaded successfully
- **THEN** all applicable controls SHALL be enabled based on the loaded data context
