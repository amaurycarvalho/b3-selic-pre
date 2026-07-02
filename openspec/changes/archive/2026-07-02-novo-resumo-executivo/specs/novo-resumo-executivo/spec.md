## ADDED Requirements

### Requirement: Calculate short-term rate
The system SHALL use the first vertex of the curve as the short-term rate.

#### Scenario: Short rate equals first vertex
- **WHEN** a curve has N vertices
- **THEN** the short-term rate SHALL be the rate at vertex 0 (first vertex)

### Requirement: Calculate long-term rate
The system SHALL use the last vertex of the curve as the long-term rate.

#### Scenario: Long rate equals last vertex
- **WHEN** a curve has N vertices
- **THEN** the long-term rate SHALL be the rate at vertex N-1 (last vertex)

### Requirement: Calculate curve slope
The system SHALL calculate the curve slope as the difference between long-term and short-term rates, expressed in basis points (bps).

#### Scenario: Slope calculation
- **WHEN** short-term rate is S% and long-term rate is L%
- **THEN** slope = (L - S) * 100 bps

### Requirement: Classify curve slope
The system SHALL classify the curve slope into 5 categories according to fixed thresholds.

#### Scenario: Slope classification ranges
- **WHEN** |slope| < 10 bps
- **THEN** slope classification SHALL be "Quase Plana"
- **WHEN** |slope| is 10-30 bps
- **THEN** slope classification SHALL be "Muito Plana"
- **WHEN** |slope| is 30-60 bps
- **THEN** slope classification SHALL be "Plana"
- **WHEN** |slope| is 60-100 bps
- **THEN** slope classification SHALL be "Moderadamente Inclinada"
- **WHEN** |slope| > 100 bps
- **THEN** slope classification SHALL be "Muito Inclinada"

### Requirement: Classify term premium
The system SHALL classify the term premium (slope) according to configurable thresholds.

#### Scenario: Classification ranges
- **WHEN** slope < 20 bps
- **THEN** premium SHALL be "Muito Baixo"
- **WHEN** slope is 20-50 bps
- **THEN** premium SHALL be "Baixo"
- **WHEN** slope is 50-90 bps
- **THEN** premium SHALL be "Normal"
- **WHEN** slope is 90-150 bps
- **THEN** premium SHALL be "Elevado"
- **WHEN** slope > 150 bps
- **THEN** premium SHALL be "Muito Elevado"

### Requirement: Classify nominal interest rate level
The system SHALL classify the nominal interest rate level using the short-term rate according to configurable thresholds.

#### Scenario: Nominal classification ranges
- **WHEN** short-term rate < 6%
- **THEN** nominal level SHALL be "Muito Baixos"
- **WHEN** short-term rate is 6-9%
- **THEN** nominal level SHALL be "Baixos"
- **WHEN** short-term rate is 9-11%
- **THEN** nominal level SHALL be "Moderados"
- **WHEN** short-term rate is 11-13%
- **THEN** nominal level SHALL be "Altos"
- **WHEN** short-term rate > 13%
- **THEN** nominal level SHALL be "Muito Altos"

### Requirement: Calculate implied real interest rate
The system SHALL calculate the implied real interest rate as the short-term rate minus the expected inflation.

#### Scenario: Real rate calculation
- **WHEN** short-term rate is 14.25% and expected inflation is 3.00%
- **THEN** real rate SHALL be 11.25%

### Requirement: Classify monetary policy restrictiveness
The system SHALL classify the degree of monetary policy restrictiveness using the real interest rate according to configurable thresholds.

#### Scenario: Restrictiveness classification ranges
- **WHEN** real rate < 2%
- **THEN** policy SHALL be "Expansionista"
- **WHEN** real rate is 2-4%
- **THEN** policy SHALL be "Neutra"
- **WHEN** real rate is 4-6%
- **THEN** policy SHALL be "Restritiva"
- **WHEN** real rate > 6%
- **THEN** policy SHALL be "Muito Restritiva"

### Requirement: Calculate expectations stability
The system SHALL calculate the mean deviation of the last N curves to measure expectations stability. The number of curves is defined by `stability_window`.

#### Scenario: Stability with sufficient history
- **WHEN** there are at least `stability_window` historical curves available
- **THEN** stability SHALL be calculated as the mean absolute deviation of the slope across the last N curves
- **THEN** the display SHALL show the deviation value in bps (e.g., "Alta (desvio médio: 8.0 bps)")

#### Scenario: Stability fallback "default"
- **WHEN** there are fewer than `stability_window` historical curves AND `stability_fallback = default`
- **THEN** stability SHALL use `default_mean_deviation_bps` as the deviation value
- **THEN** the display SHALL show "(estimado por ausência de histórico)" instead of the raw deviation

#### Scenario: Stability fallback "auto"
- **WHEN** there are fewer than `stability_window` historical curves AND `stability_fallback = auto`
- **THEN** stability SHALL estimate deviation as `|slope_current| / 5`
- **THEN** the display SHALL show "(estimado por ausência de histórico)" instead of the raw deviation

#### Scenario: Stability fallback "unavailable"
- **WHEN** there are fewer than `stability_window` historical curves AND `stability_fallback = unavailable`
- **THEN** the stability indicator SHALL be omitted from the executive summary

### Requirement: Classify expectations stability
The system SHALL classify the calculated deviation into stability levels.

#### Scenario: Stability classification ranges
- **WHEN** deviation < 5 bps
- **THEN** stability SHALL be "Muito Alta"
- **WHEN** deviation is 5-10 bps
- **THEN** stability SHALL be "Alta"
- **WHEN** deviation is 10-20 bps
- **THEN** stability SHALL be "Média"
- **WHEN** deviation is 20-35 bps
- **THEN** stability SHALL be "Baixa"
- **WHEN** deviation >= 35 bps
- **THEN** stability SHALL be "Muito Baixa"

### Requirement: Calculate steepening/flattening
The system SHALL compare the current curve slope with the previous curve slope to detect steepening or flattening.

#### Scenario: Steepening detected
- **WHEN** ΔSlope = slope_current - slope_previous > `steepening_threshold_bps`
- **THEN** the system SHALL report "Steepening" with the ΔSlope value

#### Scenario: Flattening detected
- **WHEN** ΔSlope < -`steepening_threshold_bps`
- **THEN** the system SHALL report "Flattening" with the absolute ΔSlope value

#### Scenario: No significant change
- **WHEN** |ΔSlope| <= `steepening_threshold_bps`
- **THEN** the system SHALL report "Sem alteração relevante"

#### Scenario: Steepening fallback "unavailable"
- **WHEN** there is no previous curve AND `steepening_fallback = unavailable`
- **THEN** the steepening/flattening indicator SHALL be omitted from the executive summary

#### Scenario: Steepening fallback "default"
- **WHEN** there is no previous curve AND `steepening_fallback = default`
- **THEN** the system SHALL use `estimated_delta_slope_bps` as ΔSlope

**Note**: The default value for `steepening_fallback` in settings is `"unavailable"`, meaning the "Última Mudança" block is omitted unless the user explicitly configures `"default"` or `"auto"`.

#### Scenario: Steepening fallback "auto"
- **WHEN** there is no previous curve AND `steepening_fallback = auto`
- **THEN** the system SHALL estimate ΔSlope as `|slope_current| / 5`

### Requirement: Classify steepening/flattening magnitude
The system SHALL classify the magnitude of steepening or flattening.

#### Scenario: Magnitude ranges
- **WHEN** |ΔSlope| < 10 bps
- **THEN** magnitude SHALL be "Leve"
- **WHEN** |ΔSlope| is 10-20 bps
- **THEN** magnitude SHALL be "Moderado"
- **WHEN** |ΔSlope| is 20-40 bps
- **THEN** magnitude SHALL be "Forte"
- **WHEN** |ΔSlope| >= 40 bps
- **THEN** magnitude SHALL be "Muito Forte"

### Requirement: Generate executive summary text
The system SHALL generate a text summary composed of 5 concatenated blocks: nominal level, monetary restrictiveness, slope, term premium, stability, steepening/flattening, and a final market message.

#### Scenario: Nominal level text
- **WHEN** nominal classification is "Muito Baixos"
- **THEN** text SHALL be "O mercado precifica juros historicamente baixos."
- **WHEN** nominal classification is "Baixos"
- **THEN** text SHALL be "O mercado precifica juros relativamente baixos."
- **WHEN** nominal classification is "Moderados"
- **THEN** text SHALL be "O mercado precifica juros próximos da média histórica."
- **WHEN** nominal classification is "Altos"
- **THEN** text SHALL be "O mercado precifica juros elevados."
- **WHEN** nominal classification is "Muito Altos"
- **THEN** text SHALL be "O mercado precifica juros entre os maiores níveis observados."

#### Scenario: Restrictiveness text
- **WHEN** policy classification is "Expansionista"
- **THEN** text SHALL be "A política monetária estimula crédito e atividade."
- **WHEN** policy classification is "Neutra"
- **THEN** text SHALL be "A política monetária é aproximadamente neutra."
- **WHEN** policy classification is "Restritiva"
- **THEN** text SHALL be "A política monetária busca conter pressões inflacionárias."
- **WHEN** policy classification is "Muito Restritiva"
- **THEN** text SHALL be "A política monetária permanece fortemente voltada ao controle da inflação."

#### Scenario: Slope text
- **WHEN** slope classification is "Quase Plana"
- **THEN** text SHALL be "Os juros são praticamente iguais em todos os prazos, indicando forte consenso de que o nível atual deverá permanecer por um longo período."
- **WHEN** slope classification is "Muito Plana"
- **THEN** text SHALL be "A pequena diferença entre os vencimentos curtos e longos indica que os investidores esperam a manutenção desse nível de juros por um período prolongado, sem antecipar mudanças significativas na política monetária."
- **WHEN** slope classification is "Plana"
- **THEN** text SHALL be "Os juros de longo prazo permanecem ligeiramente acima dos de curto prazo, sugerindo expectativa de estabilidade da política monetária com um pequeno prêmio para prazos maiores."
- **WHEN** slope classification is "Moderadamente Inclinada"
- **THEN** text SHALL be "Os investidores exigem um prêmio moderado para aplicações de longo prazo, refletindo alguma incerteza sobre a evolução da inflação e dos juros nos próximos anos."
- **WHEN** slope classification is "Muito Inclinada"
- **THEN** text SHALL be "Os juros aumentam significativamente conforme o prazo, indicando que o mercado exige um prêmio elevado para aplicações longas devido às incertezas sobre inflação, política monetária e riscos econômicos futuros."

#### Scenario: Steepening text
- **WHEN** steepening is detected
- **THEN** text SHALL be "A última atualização mostrou aumento da inclinação da curva."

#### Scenario: Flattening text
- **WHEN** flattening is detected
- **THEN** text SHALL be "A última atualização mostrou redução da inclinação da curva."

### Requirement: Build AnalysisReport
The system SHALL return an `AnalysisReport` object containing the formatted statements, score (always 0 for new implementation), and score_label (empty string).

#### Scenario: Report structure
- **WHEN** `analyze()` is called with valid records
- **THEN** it SHALL return an `AnalysisReport` with `statements`, `score=0`, and `score_label=""`

### Requirement: Accept configuration
The system SHALL accept an optional `CurvaJurosConfig` parameter. If not provided, it SHALL load defaults from settings.json.

#### Scenario: Custom configuration
- **WHEN** a `CurvaJurosConfig` is passed to `analyze()`
- **THEN** it SHALL use the provided configuration instead of defaults
