## ADDED Requirements

### Requirement: Calculate short-term rate delta
The system SHALL calculate the change in the short-term rate as the difference between the current and previous curve's first vertex.

#### Scenario: Delta short calculation
- **WHEN** current short rate is C% and previous short rate is P%
- **THEN** ΔCurto SHALL be (C - P) * 100 bps

### Requirement: Calculate long-term rate delta
The system SHALL calculate the change in the long-term rate as the difference between the current and previous curve's last vertex.

#### Scenario: Delta long calculation
- **WHEN** current long rate is C% and previous long rate is P%
- **THEN** ΔLongo SHALL be (C - P) * 100 bps

### Requirement: Calculate real interest rate delta
The system SHALL calculate the change in the implied real interest rate as the difference between current and previous real rate.

#### Scenario: Delta real with fixed inflation
- **WHEN** expected inflation is fixed at E%
- **THEN** ΔReal SHALL equal ΔCurto (since inflation cancels out in the subtraction)

#### Scenario: Delta real formula
- **WHEN** expected inflation may vary in the future
- **THEN** the system SHALL use (CurtoAtual - InflaçãoAtual) - (CurtoAnterior - InflaçãoAnterior)

### Requirement: Calculate slope delta
The system SHALL calculate the change in curve slope as the difference between current and previous slope.

#### Scenario: Delta slope calculation
- **WHEN** current slope is S_c bps and previous slope is S_p bps
- **THEN** ΔSlope SHALL be S_c - S_p bps

### Requirement: Classify curve movement
The system SHALL classify the overall direction of the curve movement based on ΔCurto and ΔLongo signs, subject to a movement threshold.

#### Scenario: Bear movement
- **WHEN** ΔCurto > `movement_threshold_bps` AND ΔLongo > `movement_threshold_bps`
- **THEN** movement SHALL be "Bear"

#### Scenario: Bull movement
- **WHEN** ΔCurto < -`movement_threshold_bps` AND ΔLongo < -`movement_threshold_bps`
- **THEN** movement SHALL be "Bull"

#### Scenario: Twist movement
- **WHEN** (ΔCurto > `movement_threshold_bps` AND ΔLongo < -`movement_threshold_bps`) OR (ΔCurto < -`movement_threshold_bps` AND ΔLongo > `movement_threshold_bps`)
- **THEN** movement SHALL be "Twist"

#### Scenario: Stable (below threshold)
- **WHEN** max(|ΔCurto|, |ΔLongo|) < `movement_threshold_bps`
- **THEN** movement SHALL be "Estável"

### Requirement: Classify slope movement
The system SHALL classify the change in curve slope as steepening or flattening.

#### Scenario: Steepening detected
- **WHEN** ΔSlope > `steepening_threshold_bps`
- **THEN** slope movement SHALL be "Steepening"

#### Scenario: Flattening detected
- **WHEN** ΔSlope < -`steepening_threshold_bps`
- **THEN** slope movement SHALL be "Flattening"

#### Scenario: Parallel shift
- **WHEN** |ΔSlope| <= `steepening_threshold_bps`
- **THEN** slope movement SHALL be "Parallel Shift"

### Requirement: Classify combined regime
The system SHALL combine the curve movement and slope movement into a single regime classification.

#### Scenario: Bear Steepening
- **WHEN** movement is "Bear" AND slope movement is "Steepening"
- **THEN** regime SHALL be "Bear Steepening"

#### Scenario: Bear Flattening
- **WHEN** movement is "Bear" AND slope movement is "Flattening"
- **THEN** regime SHALL be "Bear Flattening"

#### Scenario: Bull Steepening
- **WHEN** movement is "Bull" AND slope movement is "Steepening"
- **THEN** regime SHALL be "Bull Steepening"

#### Scenario: Bull Flattening
- **WHEN** movement is "Bull" AND slope movement is "Flattening"
- **THEN** regime SHALL be "Bull Flattening"

#### Scenario: Bear Parallel Shift
- **WHEN** movement is "Bear" AND slope movement is "Parallel Shift"
- **THEN** regime SHALL be "Bear Parallel Shift"

#### Scenario: Bull Parallel Shift
- **WHEN** movement is "Bull" AND slope movement is "Parallel Shift"
- **THEN** regime SHALL be "Bull Parallel Shift"

#### Scenario: Twist regime
- **WHEN** movement is "Twist"
- **THEN** regime SHALL be "Twist" (regardless of slope movement)

#### Scenario: Stable regime
- **WHEN** movement is "Estável"
- **THEN** regime SHALL be "Estável" (regardless of slope movement)

### Requirement: Classify movement intensity
The system SHALL classify the overall intensity of the curve movement based on the maximum absolute delta.

#### Scenario: Intensity ranges
- **WHEN** max(|ΔCurto|, |ΔLongo|) < 5 bps
- **THEN** intensity SHALL be "Muito Fraca"
- **WHEN** max(|ΔCurto|, |ΔLongo|) is 5-15 bps
- **THEN** intensity SHALL be "Fraca"
- **WHEN** max(|ΔCurto|, |ΔLongo|) is 15-30 bps
- **THEN** intensity SHALL be "Moderada"
- **WHEN** max(|ΔCurto|, |ΔLongo|) is 30-50 bps
- **THEN** intensity SHALL be "Forte"
- **WHEN** max(|ΔCurto|, |ΔLongo|) > 50 bps
- **THEN** intensity SHALL be "Muito Forte"

### Requirement: Classify monetary policy change
The system SHALL classify the change in implied monetary policy based on ΔReal.

#### Scenario: ΔReal > 20 bps
- **WHEN** ΔReal > 20 bps
- **THEN** policy change SHALL be "Mercado passou a precificar política mais restritiva"

#### Scenario: ΔReal 5-20 bps
- **WHEN** ΔReal is 5-20 bps
- **THEN** policy change SHALL be "Política ligeiramente mais restritiva"

#### Scenario: ΔReal -5 to +5 bps
- **WHEN** ΔReal is -5 bps to +5 bps
- **THEN** policy change SHALL be "Política praticamente inalterada"

#### Scenario: ΔReal -20 to -5 bps
- **WHEN** ΔReal is -20 to -5 bps
- **THEN** policy change SHALL be "Política ligeiramente menos restritiva"

#### Scenario: ΔReal < -20 bps
- **WHEN** ΔReal < -20 bps
- **THEN** policy change SHALL be "Mercado passou a precificar política significativamente menos restritiva"

### Requirement: Classify term premium change
The system SHALL classify the change in term premium based on ΔSlope.

#### Scenario: ΔSlope > 20 bps
- **WHEN** ΔSlope > 20 bps
- **THEN** term premium change SHALL be "Prêmio de prazo aumentou significativamente"

#### Scenario: ΔSlope 10-20 bps
- **WHEN** ΔSlope is 10-20 bps
- **THEN** term premium change SHALL be "Prêmio aumentou"

#### Scenario: ΔSlope -10 to +10 bps
- **WHEN** ΔSlope is -10 to +10 bps
- **THEN** term premium change SHALL be "Praticamente estável"

#### Scenario: ΔSlope -20 to -10 bps
- **WHEN** ΔSlope is -20 to -10 bps
- **THEN** term premium change SHALL be "Prêmio diminuiu"

#### Scenario: ΔSlope < -20 bps
- **WHEN** ΔSlope < -20 bps
- **THEN** term premium change SHALL be "Forte redução do prêmio"

### Requirement: Derive general direction
The system SHALL derive a general direction label from the combined regime and intensity.

#### Scenario: Bear + Fraca or stronger
- **WHEN** regime is Bear (any variant) AND intensity is at least "Fraca"
- **THEN** direction SHALL be "↑ Revisão Altista dos Juros"

#### Scenario: Bear + Muito Fraca
- **WHEN** regime is Bear (any variant) AND intensity is "Muito Fraca"
- **THEN** direction SHALL be "→ Juros Marginalmente Mais Altos"

#### Scenario: Bull + Fraca or stronger
- **WHEN** regime is Bull (any variant) AND intensity is at least "Fraca"
- **THEN** direction SHALL be "↓ Revisão Baixista dos Juros"

#### Scenario: Bull + Muito Fraca
- **WHEN** regime is Bull (any variant) AND intensity is "Muito Fraca"
- **THEN** direction SHALL be "→ Juros Marginalmente Mais Baixos"

#### Scenario: Twist
- **WHEN** regime is "Twist"
- **THEN** direction SHALL be "↕ Movimento Misto na Estrutura"

#### Scenario: Stable
- **WHEN** regime is "Estável"
- **THEN** direction SHALL be "→ Estrutura a Juros Praticamente Estável"

### Requirement: Generate evolution summary text
The system SHALL generate a text summary composed of 6 blocks: regime, monetary policy change, term premium change, intensity, general direction, and a final market message.

#### Scenario: Regime text — Bear Steepening
- **WHEN** regime is "Bear Steepening"
- **THEN** text SHALL be "O mercado revisou para cima toda a estrutura de juros, principalmente os vencimentos longos."

#### Scenario: Regime text — Bear Flattening
- **WHEN** regime is "Bear Flattening"
- **THEN** text SHALL be "O mercado revisou para cima toda a estrutura de juros, principalmente os vencimentos curtos."

#### Scenario: Regime text — Bull Steepening
- **WHEN** regime is "Bull Steepening"
- **THEN** text SHALL be "O mercado passou a esperar cortes de juros, sobretudo nos vencimentos curtos."

#### Scenario: Regime text — Bull Flattening
- **WHEN** regime is "Bull Flattening"
- **THEN** text SHALL be "O mercado reduziu as expectativas de juros, principalmente nos vencimentos longos."

#### Scenario: Regime text — Parallel Shift
- **WHEN** regime contains "Parallel Shift"
- **THEN** text SHALL be "O mercado alterou toda a estrutura de juros sem mudanças relevantes na inclinação."

#### Scenario: Regime text — Twist
- **WHEN** regime is "Twist"
- **THEN** text SHALL be "Houve movimento divergente entre curto e longo prazo."

#### Scenario: Regime text — Estável
- **WHEN** regime is "Estável"
- **THEN** text SHALL be "A curva permaneceu praticamente estável desde a última atualização."

#### Scenario: Monetary policy text — Muito Mais Restritiva
- **WHEN** policy change is "Mercado passou a precificar política mais restritiva"
- **THEN** text SHALL be "O mercado passou a precificar uma política monetária significativamente mais contracionista."

#### Scenario: Monetary policy text — Mais Restritiva
- **WHEN** policy change is "Política ligeiramente mais restritiva"
- **THEN** text SHALL be "O mercado elevou ligeiramente a expectativa para os juros reais."

#### Scenario: Monetary policy text — Estável
- **WHEN** policy change is "Política praticamente inalterada"
- **THEN** text SHALL be "A percepção sobre a política monetária permaneceu praticamente inalterada."

#### Scenario: Monetary policy text — Menos Restritiva
- **WHEN** policy change is "Política ligeiramente menos restritiva"
- **THEN** text SHALL be "O mercado passou a esperar uma política monetária menos restritiva."

#### Scenario: Monetary policy text — Muito Menos Restritiva
- **WHEN** policy change is "Mercado passou a precificar política significativamente menos restritiva"
- **THEN** text SHALL be "O mercado passou a precificar uma política monetária significativamente menos contracionista."

#### Scenario: Term premium text — Aumentou
- **WHEN** term premium change starts with "Prêmio de prazo aumentou" or "Prêmio aumentou"
- **THEN** text SHALL be "O prêmio exigido para aplicações de longo prazo aumentou."

#### Scenario: Term premium text — Estável
- **WHEN** term premium change is "Praticamente estável"
- **THEN** text SHALL be "O prêmio de prazo permaneceu praticamente inalterado."

#### Scenario: Term premium text — Reduziu
- **WHEN** term premium change starts with "Prêmio diminuiu" or "Forte redução"
- **THEN** text SHALL be "O prêmio exigido para aplicações longas diminuiu."

#### Scenario: Intensity text
- **WHEN** intensity is "Muito Fraca"
- **THEN** text SHALL be "A magnitude das alterações foi muito fraca."
- **WHEN** intensity is "Fraca"
- **THEN** text SHALL be "A magnitude das alterações foi fraca."
- **WHEN** intensity is "Moderada"
- **THEN** text SHALL be "A magnitude das alterações foi moderada."
- **WHEN** intensity is "Forte"
- **THEN** text SHALL be "A magnitude das alterações foi forte."
- **WHEN** intensity is "Muito Forte"
- **THEN** text SHALL be "A magnitude das alterações foi muito forte."

### Requirement: Build EvolutionReport
The system SHALL return an `EvolutionReport` object containing all calculated indicators and generated text.

#### Scenario: Report structure
- **WHEN** `analyze_evolution()` is called with valid current and previous records
- **THEN** it SHALL return an `EvolutionReport` with `statements`, `delta_short_bps`, `delta_long_bps`, `delta_slope_bps`, `delta_real_bps`, `regime`, `intensity`, `monetary_policy_msg`, `term_premium_msg`, `direction`, and `market_message`

### Requirement: Accept configuration for evolution
The system SHALL accept an optional configuration parameter for evolution analysis.

#### Scenario: Custom configuration
- **WHEN** a `CurvaJurosConfig` with custom `evolution` settings is passed to `analyze_evolution()`
- **THEN** it SHALL use the provided configuration instead of defaults

### Requirement: Handle missing previous curve
The system SHALL handle the case where there is no previous curve available.

#### Scenario: No previous curve
- **WHEN** `previous` records list is empty
- **THEN** `analyze_evolution()` SHALL return `None`

### Requirement: Represent monetary policy delta with directional arrow
The system SHALL prefix the monetary policy change text with a directional arrow when displayed.

#### Scenario: More restrictive
- **WHEN** ΔReal > 0
- **THEN** the display SHALL prefix with "▲"

#### Scenario: Less restrictive
- **WHEN** ΔReal < 0
- **THEN** the display SHALL prefix with "▼"

#### Scenario: Unchanged
- **WHEN** ΔReal is within -5 to +5 bps
- **THEN** the display SHALL prefix with "→"

### Requirement: Represent term premium delta with directional arrow
The system SHALL prefix the term premium change text with a directional arrow when displayed.

#### Scenario: Premium increased
- **WHEN** ΔSlope > 10 bps
- **THEN** the display SHALL prefix with "▲"

#### Scenario: Premium decreased
- **WHEN** ΔSlope < -10 bps
- **THEN** the display SHALL prefix with "▼"

#### Scenario: Premium stable
- **WHEN** |ΔSlope| <= 10 bps
- **THEN** the display SHALL prefix with "→"
