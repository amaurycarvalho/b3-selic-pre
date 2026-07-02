## ADDED Requirements

### Requirement: Display evolution sub-panel in sidebar
The system SHALL display a second sub-panel titled "Resumo Executivo — Evolução da Curva" below the current curve analysis panel when evolution mode is active.

#### Scenario: Evolution panel visible
- **WHEN** the mode is "Evolução" AND historical data contains at least one previous curve
- **THEN** the evolution sub-panel SHALL be displayed below the "Resumo Executivo — Curva Atual" panel
- **AND** the two panels SHALL be separated by a horizontal divider line

#### Scenario: Evolution panel hidden
- **WHEN** the mode is not "Evolução" OR no previous curve is available
- **THEN** the evolution sub-panel SHALL NOT be displayed

#### Scenario: Stable evolution (compact mode)
- **WHEN** the evolution regime is "Estável"
- **THEN** the system SHALL display a compact version with only regime, direction, and market message

### Requirement: Format evolution panel content
The system SHALL format the evolution panel content using tk.Text tags for rich text display.

#### Scenario: Headers in evolution panel
- **WHEN** section names are displayed in the evolution panel
- **THEN** they SHALL appear in bold using the "header" tag

#### Scenario: Directional arrows in evolution panel
- **WHEN** an ▲ arrow is displayed (more restrictive / premium increased)
- **THEN** it SHALL be shown in green using the "positive" tag
- **WHEN** a ▼ arrow is displayed (less restrictive / premium decreased)
- **THEN** it SHALL be shown in red using the "negative" tag
- **WHEN** a → arrow is displayed (stable)
- **THEN** it SHALL be shown in default color using no special tag

### Requirement: Evolution panel layout
The system SHALL display exactly 6 named lines plus a market message in the evolution panel.

#### Scenario: Full evolution layout
- **WHEN** evolution is not "Estável"
- **THEN** the evolution panel SHALL display: Regime, Política Monetária, Prêmio de Prazo, Intensidade, Direção Geral, and a final market message section

#### Scenario: Compact evolution layout
- **WHEN** evolution is "Estável"
- **THEN** the evolution panel SHALL display: Regime, Direção Geral, and a market message

### Requirement: Build analysis text with both panels
The system SHALL build the full sidebar text by combining the current curve analysis and the evolution analysis.

#### Scenario: Both panels displayed
- **WHEN** evolution mode is active AND both panels have content
- **THEN** the sidebar text SHALL be the concatenation of the current curve panel, a horizontal divider, and the evolution panel
