## MODIFIED Requirements

### Requirement: Section headers in analysis panel
The system SHALL display section headers within the analysis text panel.

#### Scenario: Header shown for each section
- **WHEN** analysis content is displayed in the sidebar
- **THEN** each section (Resumo Executivo — Curva Atual, Nível Nominal, Política Monetária, Inclinação, Prêmio de Prazo, Estabilidade das Expectativas, Última Mudança, Mensagem do Mercado) SHALL be preceded by a bold header

### Requirement: Rich-text formatting in analysis panel
The system SHALL use Text widget tags for visual formatting of analysis content.

#### Scenario: Bold headers
- **WHEN** section headers are displayed
- **THEN** they SHALL appear in bold

#### Scenario: Colored steepening/flattening indicators
- **WHEN** a steepening indicator (▲) is displayed
- **THEN** it SHALL be shown in green using the "positive" tag
- **WHEN** a flattening indicator (▼) is displayed
- **THEN** it SHALL be shown in red using the "negative" tag

#### Scenario: Bullet points for values
- **WHEN** indicator values are displayed (e.g., "● Muito Altos (14,25%)")
- **THEN** they SHALL use indentation and the standard text color

## REMOVED Requirements

### Requirement: Colored confidence values
**Reason**: The new Resumo Executivo does not display confidence percentages; it displays stability levels instead.
**Migration**: Stability levels are displayed as text labels (e.g., "● Alta") without color coding.

### Requirement: Colored fact text
**Reason**: The new Resumo Executivo does not display individual facts with positive/negative indicators. The only colored elements are the steepening/flattening directional arrows.
**Migration**: Steepening/flattening arrows use "positive" (green) and "negative" (red) tags.
