## ADDED Requirements

### Requirement: Metric extraction from detailed rate data
The system SHALL extract quantitative metrics from a list of `RateRecord` objects for use in rule evaluation. Metrics SHALL include: initial rate, final rate, maximum rate, minimum rate, linear slope (via numpy polyfit degree 1), quadratic coefficient (via numpy polyfit degree 2), standard deviation of successive rate differences (volatility), and count of direction changes (oscillations).

#### Scenario: Metrics computed from valid records
- **WHEN** the system receives a non-empty list of RateRecord objects
- **THEN** all metrics are computed deterministically using numpy operations

#### Scenario: Empty records produce zero/None metrics
- **WHEN** the system receives an empty list
- **THEN** all metrics SHALL return safe defaults (0.0, None, or empty)

### Requirement: Curve shape classification
The system SHALL classify the detailed curve shape as ascending, descending, or flat based on the difference between final and initial rates, using configurable thresholds:
- Ascending: `final - initial > threshold_ascend` → "A estrutura a termo apresenta inclinação positiva, indicando taxas maiores para vencimentos mais longos."
- Descending: `final - initial < -threshold_descend` → "A curva encontra-se invertida, refletindo expectativa de redução futura das taxas de juros."
- Flat: `|final - initial| < threshold_flat` → "A curva permanece praticamente plana ao longo dos vencimentos."

#### Scenario: Ascending curve detected
- **WHEN** `taxa_final - taxa_inicial > +0.20%`
- **THEN** the report includes the ascending curve text

#### Scenario: Descending curve detected
- **WHEN** `taxa_final - taxa_inicial < -0.20%`
- **THEN** the report includes the inverted curve text

#### Scenario: Flat curve detected
- **WHEN** `|taxa_final - taxa_inicial| < 0.15%`
- **THEN** the report includes the flat curve text

### Requirement: Slope classification
The system SHALL classify the linear slope magnitude as "Muito forte", "Forte", "Moderada", "Fraca", "Nula", or "Negativa" using configurable thresholds, and include a corresponding text statement.

#### Scenario: Strong positive slope
- **WHEN** the slope exceeds the "Forte" threshold
- **THEN** the report states "A inclinação da curva é acentuada, indicando prêmio relevante para prazos longos."

### Requirement: Convexity classification
The system SHALL classify curve convexity as Linear, Côncava, Convexa, or "Em S" using the sign and magnitude of the quadratic regression coefficient, and include a corresponding text statement.

#### Scenario: Convex curve
- **WHEN** the quadratic coefficient is positive and above threshold
- **THEN** the report states "O crescimento das taxas acelera nos vencimentos longos."

#### Scenario: Concave curve
- **WHEN** the quadratic coefficient is negative and below threshold
- **THEN** the report states "O avanço das taxas perde intensidade conforme aumenta o prazo."

### Requirement: Volatility classification
The system SHALL classify the standard deviation of successive rate differences as "Muito baixa", "Baixa", "Normal", "Alta", or "Muito alta" using configurable thresholds, with corresponding text (e.g., "Os vértices apresentam comportamento homogêneo." or "Observa-se elevada irregularidade entre vértices consecutivos.").

#### Scenario: Low volatility
- **WHEN** volatility is classified as "Muito baixa" or "Baixa"
- **THEN** the report states vertices are homogeneous

#### Scenario: High volatility
- **WHEN** volatility is classified as "Alta" or "Muito alta"
- **THEN** the report states there is elevated irregularity

### Requirement: Oscillation counting
The system SHALL count direction changes (inversions) in the rate sequence and include a text statement when oscillations exceed a configurable threshold.

#### Scenario: High oscillation count
- **WHEN** the number of direction changes exceeds the threshold
- **THEN** the report states "Existem diversas oscilações locais, sugerindo baixa uniformidade da curva."

### Requirement: Envelope spread analysis
The system SHALL compute the average spread (max - min) across all years from consolidated data and classify it as "Muito estreito", "Dentro do padrão histórico", or "Elevada dispersão" using configurable thresholds, with corresponding text.

#### Scenario: Very narrow spread
- **WHEN** average spread < 0.05
- **THEN** the report states "Existe elevado consenso do mercado sobre o nível esperado das taxas."

#### Scenario: Spread within historical range
- **WHEN** average spread is between 0.05 and 0.30
- **THEN** the report states "A dispersão entre as taxas permanece dentro do padrão histórico."

#### Scenario: High dispersion
- **WHEN** average spread > 0.30
- **THEN** the report states "Há elevada dispersão entre as taxas negociadas para o mesmo horizonte temporal."

### Requirement: Envelope trend analysis
The system SHALL detect whether the spread increases or decreases with the year number and include corresponding text:
- Increasing spread → "A incerteza aumenta conforme se alonga o horizonte temporal."
- Decreasing spread → "O mercado demonstra maior convergência nas expectativas para os vencimentos longos."

#### Scenario: Spread increases with year
- **WHEN** `spread(year_n+1) > spread(year_n)` consistently
- **THEN** the report states uncertainty increases with horizon

#### Scenario: Spread decreases with year
- **WHEN** `spread(year_n+1) < spread(year_n)` consistently
- **THEN** the report states convergence for long maturities

### Requirement: Evolution trend detection
The system SHALL detect the trend across the 5 historical dates in evolution mode: "ALTA_CONTÍNUA" (all rates rose), "QUEDA_CONTÍNUA" (all rates fell), or "INSTABILIDADE" (mixed signals), with corresponding text.

#### Scenario: Continuous upward repricing
- **WHEN** all 4 deltas (Δ7, Δ14, Δ21, Δ28) are positive
- **THEN** the report states "A curva vem sendo gradualmente reprecificada para cima nas últimas semanas."

#### Scenario: Continuous downward adjustment
- **WHEN** all 4 deltas are negative
- **THEN** the report states "O mercado vem reduzindo consistentemente as expectativas de juros."

#### Scenario: Mixed signals
- **WHEN** deltas alternate between positive and negative
- **THEN** the report states "As expectativas oscilaram significativamente ao longo das últimas semanas."

### Requirement: Movement diffusion analysis
The system SHALL analyze how many years moved up vs down and classify the diffusion as "Disseminado por toda a curva", "Concentrado nos vencimentos longos", or "Concentrado nos vencimentos curtos".

#### Scenario: Widespread movement
- **WHEN** >80% of years moved in the same direction
- **THEN** the report states "O movimento foi disseminado por praticamente toda a curva."

#### Scenario: Long-end concentration
- **WHEN** movement concentrated in longer years
- **THEN** the report states "A alta concentrou-se nos vencimentos longos."

#### Scenario: Short-end concentration
- **WHEN** movement concentrated in shorter years
- **THEN** the report states "O ajuste ocorreu principalmente na parte curta da curva."

### Requirement: Curve rotation classification
The system SHALL classify the curve movement type as Bear Steepening, Bull Steepening, Bear Flattening, or Bull Flattening based on the relative change between short and long maturities, with corresponding text.

#### Scenario: Bear Steepening
- **WHEN** long-end rates rose more than short-end
- **THEN** the report states "A parte longa da curva avançou mais intensamente que a curta, aumentando sua inclinação e indicando maior prêmio exigido para prazos longos."

#### Scenario: Bull Steepening
- **WHEN** rates fell across the curve but short-end fell more
- **THEN** the report states "As taxas recuaram em toda a curva, porém a redução foi mais acentuada nos vencimentos curtos, elevando a inclinação relativa."

#### Scenario: Bear Flattening
- **WHEN** short-end rates rose more than long-end
- **THEN** the report states "A alta concentrou-se na parte curta da curva, reduzindo sua inclinação e sugerindo expectativa de juros elevados no curto prazo."

#### Scenario: Bull Flattening
- **WHEN** rates fell across the curve but long-end fell more
- **THEN** the report states "As taxas caíram principalmente nos vencimentos longos, achatando a curva e indicando redução do prêmio de prazo."

### Requirement: Movement intensity classification
The system SHALL classify the absolute average delta across all years as "Muito pequeno", "Pequeno", "Moderado", "Grande", or "Muito grande" using configurable thresholds, with corresponding text.

#### Scenario: Small movement
- **WHEN** intensity is classified as "Muito pequeno" or "Pequeno"
- **THEN** the report states "O movimento semanal foi discreto."

#### Scenario: Large movement
- **WHEN** intensity is classified as "Grande" or "Muito grande"
- **THEN** the report states "Houve reprecificação significativa da curva."

### Requirement: Aggregate score computation
The system SHALL compute an aggregate score by summing weights of all activated rules, classify the score as "Mercado estável" (0-3), "Mudança moderada" (4-7), "Mudança relevante" (8-12), or "Mudança expressiva" (13+), and include the classification text.

#### Scenario: Expressive repricing detected
- **WHEN** the aggregate score exceeds 12
- **THEN** the report states "O conjunto dos indicadores aponta para uma reprecificação expressiva da curva de juros."

### Requirement: Report formatting
The system SHALL format the analysis report as a structured text with sections: "Formato da Curva", "Dispersão e Consenso", "Evolução Recente", "Qualidade do Movimento", and "Conclusão", concatenating the texts of all activated rules in the appropriate section.

#### Scenario: Full report generated
- **WHEN** analysis completes with data
- **THEN** a structured report with all 5 sections is returned as a formatted string

#### Scenario: No data shows empty report
- **WHEN** no records are available
- **THEN** an empty report or "Sem dados para análise" is returned

### Requirement: GUI collapsible sidebar
The system SHALL provide a collapsible sidebar panel on the right side of the GUI window that displays the analysis report. The panel SHALL start collapsed and SHALL expand/collapse via a toggle button.

#### Scenario: Sidebar toggles open
- **WHEN** the user clicks the toggle button "▶ Análise"
- **THEN** the sidebar expands to display the report text in a readonly widget

#### Scenario: Sidebar toggles closed
- **WHEN** the user clicks the toggle button "▼ Análise" while the sidebar is open
- **THEN** the sidebar collapses, hiding the report text

### Requirement: Automatic report update
The system SHALL automatically regenerate and display the analysis report whenever the chart is redrawn (view mode change, data fetch, evolution toggle). The report SHALL reflect the current view mode (raw/detailed vs consolidated vs evolution).

#### Scenario: Report updates on data fetch
- **WHEN** new data is fetched and the chart redraws
- **THEN** the report text updates to reflect the new data

#### Scenario: Report updates on view toggle
- **WHEN** the user switches between Detalhado, Consolidado, or Evolution modes
- **THEN** the report text updates to match the current view

### Requirement: Configurable thresholds
The system SHALL accept an `AnalysisThresholds` dataclass with all classification thresholds as parameters, providing sensible defaults. Callers MAY override individual thresholds.

#### Scenario: Default thresholds used
- **WHEN** `analyze()` is called without custom thresholds
- **THEN** default threshold values are used for all classifications

#### Scenario: Custom thresholds accepted
- **WHEN** `analyze()` is called with a custom `AnalysisThresholds` instance
- **THEN** the custom thresholds override defaults for all classifications
