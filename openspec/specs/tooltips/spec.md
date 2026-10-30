# Tooltips

## Purpose
Show descriptive tooltips on hover for all interactive controls. TBD.

## Requirements

### Requirement: Tooltips on interactive widgets
The system SHALL show a tooltip on hover for all interactive controls, explaining their function.

#### Scenario: Tooltip appears on hover
- **WHEN** the user hovers over a button, radio button, checkbox, or entry
- **THEN** a tooltip SHALL appear after a short delay

#### Scenario: Tooltip disappears on leave
- **WHEN** the cursor leaves the widget
- **THEN** the tooltip SHALL be hidden

#### Scenario: Tooltip text per widget
- **WHEN** the user hovers over "Consolidado"
- **THEN** the tooltip SHALL show "Agrupa os vencimentos por ano"
- **WHEN** the user hovers over "Evolução da curva"
- **THEN** the tooltip SHALL show "Carrega automaticamente os últimos 5 pregões"
- **WHEN** the user hovers over "3D"
- **THEN** the tooltip SHALL show "Exibe a evolução temporal em três dimensões"
- **WHEN** the user hovers over the refresh button in the `Feriados` tab
- **THEN** the tooltip SHALL show "Atualiza o calendário de feriados da ANBIMA"
- **WHEN** the user hovers over the holiday tree
- **THEN** the tooltip SHALL show "Selecione ano, mês ou dia para ver os feriados"
