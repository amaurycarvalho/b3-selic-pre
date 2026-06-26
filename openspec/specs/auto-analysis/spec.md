## Purpose

Automatically analyze the SELIC Pré interest rate curve data and generate a structured natural-language commentary report. The analysis uses a hierarchical 5-level classification engine for curve shape analysis (primary class, structural characteristics, quality), plus envelope dispersion, historical evolution trends, movement intensity, and aggregate scoring.

## Requirements

### Requirement: Metric extraction from detailed rate data
The system SHALL extract quantitative metrics from a list of `RateRecord` objects. Metrics SHALL include: initial rate, final rate, maximum rate, minimum rate, index of the global minimum, linear regression slope over all points (`slope_global`), standard deviation of successive rate differences, and count of direction changes. The `indice_tendencia` field is removed.

#### Scenario: Metrics computed from valid records
- **WHEN** the system receives a non-empty list of RateRecord objects
- **THEN** all metrics are computed deterministically using numpy operations
- **AND** `slope_global` SHALL be `numpy.polyfit(days, rates, 1)[0]` — the coefficient of the best-fit line through all points

#### Scenario: Empty records produce zero/None metrics
- **WHEN** the system receives an empty list
- **THEN** all metrics SHALL return safe defaults (0.0, None, or empty)

### Requirement: AFTER_MIN_UP feature computation window
The system SHALL compute the `AFTER_MIN_UP` feature using only the recovery zone between the last occurrence of the global minimum and the global maximum. The window start SHALL be `last_min = max(i for i, r in enumerate(rates) if r == rates[min_idx])` — the LAST index where the rate equals the minimum value. When `max_idx > last_min`, the analysis window SHALL be `rates[last_min:max_idx+1]`. When `max_idx <= last_min`, `AFTER_MIN_UP` SHALL be False (no recovery zone exists).

The `after_min_ratio` SHALL be computed as `non_negative_deltas / len(deltas)` over this restricted window, where a delta is non-negative if `rates[k+1] - rates[k] >= 0`. Zero deltas SHALL count as recovery (rate did not decrease). The feature SHALL be True when `after_min_ratio >= config.recuperacao_min_ratio`.

#### Scenario: Valley with recovery then plateau
- **WHEN** min_idx=39, last_min=48, max_idx=138, and the recovery zone from last_min to max contains 90 deltas with 21 strictly positive and 66 zero (all >= 0)
- **THEN** after_min_ratio SHALL be 87/90 ≈ 0.97
- **AND** AFTER_MIN_UP SHALL be True (0.97 >= 0.80)

#### Scenario: Valley floor excluded from window
- **WHEN** the minimum value 14.03 appears at indices [39..48] (10 records)
- **THEN** last_min SHALL be 48 and the window SHALL start at index 48, excluding the 9 zero-deltas of the valley floor

### Requirement: AFTER_MAX_DOWN feature computation window
The system SHALL compute the `AFTER_MAX_DOWN` feature using only the descent zone between the last occurrence of the global maximum and the global minimum. The window start SHALL be `last_max = max(i for i, r in enumerate(rates) if r == rates[max_idx])`. When `min_idx > last_max`, the analysis window SHALL be `rates[last_max:min_idx+1]`. When `min_idx <= last_max`, `AFTER_MAX_DOWN` SHALL be False (no descent zone exists).

The `after_max_ratio` SHALL be computed as `non_positive_deltas / len(deltas)` over this restricted window, where a delta is non-positive if `rates[k+1] - rates[k] <= 0`. Zero deltas SHALL count as descent (rate did not increase). The feature SHALL be True when `after_max_ratio >= config.recuperacao_min_ratio`.

#### Scenario: Peak with descent
- **WHEN** last_max=25, min_idx=150, and the descent zone contains 124 deltas with 110 strictly negative and 10 zero (all <= 0)
- **THEN** after_max_ratio SHALL be 120/124 ≈ 0.97
- **AND** AFTER_MAX_DOWN SHALL be True (0.97 >= 0.80)

### Requirement: Hierarchical 5-level classification architecture
The system SHALL classify curves using a 5-level hierarchical architecture instead of flat rule evaluation. Level 1 (Primary Classification) SHALL be mutually exclusive via `exclusive_group` in RuleDef. Level 2 (Structural Characteristics) SHALL be gated by the primary class. Level 3 (Curve Quality) SHALL always evaluate all rules independently.

#### Scenario: Hierarchy enforces mutual exclusion
- **WHEN** a curve satisfies both VALE and ASCENDENTE conditions
- **THEN** VALE SHALL be chosen (higher priority) and ASCENDENTE SHALL not be evaluated

### Requirement: Level 1 — Primary Classification
The system SHALL classify each curve into exactly one primary class, evaluated in ascending order of `priority`: OSCILANTE > VALE > PICO > SIGMOIDE > ASCENDENTE > DESCENDENTE > PLANA. Lower number = higher priority. The Rule Registry SHALL document the priority of each rule. The first class whose conditions are satisfied SHALL be selected.

#### Scenario: Valley curve detected
- **WHEN** exactly 1 local minimum exists, position < 35% of curve length, and final rate > initial rate
- **THEN** primary class SHALL be VALE

#### Scenario: Ascending curve detected
- **WHEN** no higher-priority class matches and `slope_global > 0.00005`
- **THEN** primary class SHALL be ASCENDENTE

#### Scenario: Flat curve requires triple condition
- **WHEN** no higher-priority class matches and `amplitude < 0.10` AND `|delta_final| < 0.05` AND `|slope_global| < 0.00005`
- **THEN** primary class SHALL be PLANA

#### Scenario: Flat curve not detected when amplitude is high
- **WHEN** no higher-priority class matches and `amplitude >= 0.10` even if `|slope_global| < 0.00005`
- **THEN** primary class SHALL NOT be PLANA (falls through to default PLANA only if all 3 conditions met)

### Requirement: Level 2 — Structural Characteristics gating policy
The system SHALL classify structural facts into two categories: **dependent** (requiring a specific primary class context) and **independent** (evaluated regardless of primary class).

Dependent facts SHALL retain `gated_by`:
- `RECUPERACAO_SUSTENTADA` SHALL be gated by `["VALE"]` (requires valley context)

Independent facts SHALL have no `gated_by` restriction:
- `ACHATAMENTO` (requires ACHATAMENTO_FLAG)
- `EMPINAMENTO` (requires EMPINAMENTO_FLAG)
- `TORCAO` (requires TORCAO_FLAG)
- `DEGRAUS` (requires STAIRCASE)
- `MONOTONIA_STRUCT` (requires MONOTONIC)
- `RECUPERACAO_LONGA` (requires LONG_RECOVERY, new)

#### Scenario: Independent structural fact activates with INDEFINIDA primary class
- **WHEN** primary class is INDEFINIDA and ACHATAMENTO_FLAG is True
- **THEN** ACHATAMENTO fact SHALL be generated (gate removed, independent evaluation)

#### Scenario: Dependent fact does not activate without gate
- **WHEN** primary class is INDEFINIDA and medio.delta > 0 and longo.delta > 0
- **THEN** RECUPERACAO_SUSTENTADA SHALL NOT be generated (gate requires VALE)

### Requirement: Level 3 — Curve Quality (always evaluated)
The system SHALL evaluate all quality rules (SUAVE, SERRILHADA, CONSENSO, DISPERSÃO) regardless of primary class.

#### Scenario: Quality rules always evaluated
- **WHEN** primary class is OSCILANTE
- **THEN** SUAVE, SERRILHADA, CONSENSO, and DISPERSÃO rules SHALL still be evaluated

### Requirement: R012 — Mudança Estrutural with stricter condition
The system SHALL detect structural change only when the difference between maximum and minimum segment slopes exceeds 30%, not merely when inflection count >= 1.

#### Scenario: Structural change detected
- **WHEN** primary class enables MUDANCA_ESTRUTURAL and `|max_slope - min_slope| / max(|slopes|) > 0.30`
- **THEN** MUDANCA_ESTRUTURAL activates

#### Scenario: Minor curvature not structural
- **WHEN** `qtd_inflexoes >= 1` but slope difference < 30%
- **THEN** MUDANCA_ESTRUTURAL does NOT activate

### Requirement: R020 — SIGMOIDE with minimum segment size
The system SHALL classify a curve as SIGMOIDE only when `qtd_inflexoes >= 2` AND each inflection segment spans at least 15% of the total curve length.

#### Scenario: True S-shape detected
- **WHEN** 2 inflection points exist with segments of 25% and 30% of curve length
- **THEN** primary class SHALL be SIGMOIDE

#### Scenario: Noise inflection rejected
- **WHEN** 2 inflection points exist but one segment spans only 5% of curve length
- **THEN** primary class SHALL NOT be SIGMOIDE

### Requirement: Direction detection via linear regression
The system SHALL determine overall trend direction using `slope_global` (linear regression over all points) instead of `(final - inicial) / amplitude`. A positive slope above threshold indicates ascending; a negative slope below threshold indicates descending.

#### Scenario: Ascending via regression despite valley
- **WHEN** a curve starts at 14.15, dips to 14.05, and rises to 14.39
- **THEN** `slope_global` SHALL be positive (regression captures overall upward trend)
- **AND** primary class may be VALE (higher priority) or ASCENDENTE (if valley conditions not met)

### Requirement: Confidence per Fact
Each Fact SHALL carry a `confidence` field computed as `satisfied_optional / total_optional`. For rules without optional features, confidence SHALL be 1.0. Confidence SHALL be displayed in the report.

#### Scenario: Partial confidence
- **WHEN** VALE activates with 3 of 4 optional conditions
- **THEN** `fact.confidence` SHALL be 0.75

#### Scenario: Full confidence
- **WHEN** a rule with no optional features activates
- **THEN** `fact.confidence` SHALL be 1.0

### Requirement: Two-level traceability
The system SHALL provide two-level traceability. Each Feature SHALL carry `derived_from_metrics` listing the metric names used to compute it. Each Fact SHALL carry `derived_from_features` listing the Feature names that activated it. The full chain `Métrica → Feature → Fact` SHALL be reconstructible from any Fact.

#### Scenario: Full trace chain from Fact to Metric
- **WHEN** CURVA_COM_VALE is activated
- **THEN** `fact.derived_from_features` SHALL list `["MIN_GLOBAL_LEFT", "AFTER_MIN_UP", ...]`
- **AND** `feature["MIN_GLOBAL_LEFT"].derived_from_metrics` SHALL list `["indice_minimo_global"]`

### Requirement: Features are immutable after computation
The system SHALL freeze the Features dictionary after `compute_features()` returns. No rule SHALL modify Features. Only new Facts may be produced. This prevents side effects between rule evaluations.

#### Scenario: Feature mutation prevented
- **WHEN** any rule attempts to modify a Feature value
- **THEN** the operation SHALL be prohibited (e.g., via frozen dataclass or read-only view)

### Requirement: FactType classification
The system SHALL classify each Fact with a `FactType` enum: `CLASSIFICATION` (Level 1), `STRUCTURE` (Level 2), `QUALITY` (Level 3), `INTENSITY` (Level 4, from Scorer), `AUXILIARY` (informational, no score impact). The Report SHALL use `FactType` to group facts into blocks, without depending on rule names.

#### Scenario: Report groups by FactType
- **WHEN** Facts of types CLASSIFICATION, STRUCTURE, and QUALITY exist
- **THEN** report SHALL have blocks for each type, ordered by level

### Requirement: InferenceConfig centralizes all thresholds
The system SHALL define all epsilon thresholds in a single `InferenceConfig` dataclass. Every module that needs a threshold SHALL receive it via `InferenceConfig`, never via hardcoded constant. The dataclass SHALL include: `epsilon_slope`, `epsilon_convexity`, `epsilon_amplitude`, `epsilon_horizontal`, `vale_posicao_max`, `pico_posicao_max`, `recuperacao_min_ratio`, `recuperacao_magnitude`, `recuperacao_longa_min_pct`, `recuperacao_longa_min_ratio`, `recuperacao_longa_min_amplitude`, and all other configurable limits.

New RECUPERACAO_LONGA parameters and their defaults:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `recuperacao_longa_min_pct` | 0.15 | Minimum fraction of curve length for a qualifying segment |
| `recuperacao_longa_min_ratio` | 0.70 | Minimum proportion of positive deltas in the segment |
| `recuperacao_longa_min_amplitude` | 0.40 | Minimum ratio of segment amplitude to total amplitude |

All existing parameters SHALL retain their current defaults. No existing defaults SHALL be changed.

#### Scenario: All thresholds in one place
- **WHEN** a user wants to adjust the slope threshold
- **THEN** they SHALL pass `InferenceConfig(epsilon_slope=0.0001)` without modifying any source file

#### Scenario: Custom thresholds via InferenceConfig
- **WHEN** user passes `InferenceConfig(recuperacao_longa_min_pct=0.20, recuperacao_longa_min_ratio=0.80)`
- **THEN** LONG_RECOVERY detection SHALL use 20% length and 80% positive delta requirements

#### Scenario: Threshold override via analyze()
- **WHEN** user passes `threshold_overrides={"recuperacao_longa_min_amplitude": 0.30}`
- **THEN** the override value 0.30 SHALL replace the default 0.40

### Requirement: Engine versioning
The system SHALL include `engine_version` (semantic version of the inference engine), `ruleset_version` (version of the rule definitions), and `generated_at` (ISO 8601 timestamp) in every `AnalysisResult`. This SHALL guarantee that the same engine version + ruleset + input data produces identical results.

#### Scenario: Reproducibility across time
- **WHEN** an analysis is generated on date D with engine v2.0.0 and ruleset v1.0.0
- **THEN** running the same engine version and ruleset on the same data on any future date SHALL produce the same result

### Requirement: Classifier is a pure function
The Classifier SHALL be deterministic, stateless, and free of side effects. It SHALL NOT mutate its input parameters. It SHALL NOT use internal caches or global state. Same inputs SHALL always produce same outputs.

#### Scenario: Classifier determinism
- **WHEN** `classify(features, registry)` is called twice with identical inputs
- **THEN** both calls SHALL return identical Facts

### Requirement: Priority ordering — lower number = higher priority
The system SHALL evaluate rules in ascending order of `priority`. Priority 0 evaluates before priority 100. The Rule Registry SHALL document the priority of each rule.

#### Scenario: Priority order respected
- **WHEN** Rule A has priority 1 and Rule B has priority 10
- **THEN** Rule A SHALL be evaluated before Rule B

### Requirement: Templates internationalizable via template_id
The system SHALL reference templates by `template_id`, not inline text. A separate template module SHALL map `(template_id, locale) → text`. The Report SHALL resolve templates using the active locale.

#### Scenario: Portuguese and English output
- **WHEN** locale is "en" and a rule references `template_id = "vale_primary"`
- **THEN** the report SHALL display the English template text

### Requirement: Report consumes only Facts
The Report module SHALL NOT import or access Features, Metrics, or the Rule Registry. It SHALL receive only `list[Fact]` and `AnalysisResult`. All information needed for display SHALL be present in the Facts (text, type, confidence, derived_from).

#### Scenario: Report isolated from internals
- **WHEN** the Feature implementation changes
- **THEN** the Report module SHALL require no modifications

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

### Requirement: ScoringPolicy independent of Rule Registry
The system SHALL store rule weights in a separate ScoringPolicy module, not in the Rule Registry. The Registry SHALL define only rule logic (required features, generated fact, template_id, exclusive_group). The ScoringPolicy SHALL map `fact_id → (score_base, weight_level)`. This allows different scoring policies without modifying rules.

#### Scenario: Two scoring policies produce different scores
- **WHEN** Conservative policy assigns VALE weight (1, 2) and Aggressive policy assigns (3, 3)
- **THEN** the same Facts produce different total scores without any rule changes

### Requirement: Aggregate score computation with direction-aware classification
The system SHALL compute an aggregate score using the ScoringPolicy module to look up each Fact's `(score_base, weight_level)`. The score SHALL be computed as `sum(score_base * weight_level)` across all scored facts. The score SHALL be classified into intensity labels based on the direction determined by the primary class.

#### Scenario: Weighted score from all levels
- **WHEN** primary class is VALE (score_base +2, weight_level ×3 = +6) and RECUPERACAO_SUSTENTADA activates (+1, weight_level ×2 = +2) and CURVA_SUAVE activates (+1, weight_level ×1 = +1)
- **THEN** total score is 9

### Requirement: Complete score weight table in ScoringPolicy
The ScoringPolicy SHALL define the following mapping:

| Fact ID | Score Base | Weight Level |
|---------|-----------|-------------|
| ASCENDENTE, DESCENDENTE, VALE, PICO, SIGMOIDE | +2 | ×3 |
| OSCILANTE | +1 | ×3 |
| PLANA, INDEFINIDA | 0 | ×3 |
| RECUPERACAO_SUSTENTADA | +1 | ×2 |
| RECUPERACAO_LONGA | +1 | ×2 |
| ACHATAMENTO, EMPINAMENTO | +1 | ×2 |
| TORCAO | +2 | ×3 |
| DEGRAUS | 0 | ×1 |
| ENVELOPE_CRESCENTE, ENVELOPE_DECRESCENTE | +1 | ×1 |
| CURVA_SUAVE | +1 | ×1 |
| BAIXA_VOLATILIDADE | +1 | ×1 |
| CURVA_SERRILHADA | -1 | ×1 |
| ALTA_VOLATILIDADE | -2 | ×1 |
| OSCILACAO | -2 | ×1 |
| MONOTONIA | 0 | ×1 |
| VOLATILIDADE_MODERADA | 0 | ×1 |

Classification labels: 0–2 Estável, 3–5 Moderada, 6–8 Relevante, 9–11 Significativa, 12+ Estrutural.

### Requirement: Report structure — 5 blocks with traceability
The system SHALL generate a report with 5 blocks: (1) CLASSE PRIMÁRIA, (2) ESTRUTURA, (3) QUALIDADE, (4) INTENSIDADE, (5) RESUMO. Each fact SHALL display its confidence and `derived_from_features` trace. The summary SHALL concatenate templates in fixed order (Primary → Structure → Quality → Intensity). Empty blocks SHALL be omitted.

#### Scenario: Full report with all blocks
- **WHEN** analysis completes with a VALE curve, RECUPERACAO_SUSTENTADA, and CURVA_SUAVE
- **THEN** the report SHALL contain CLASSE PRIMÁRIA block with "Vale"
- **AND** ESTRUTURA block with "Recuperação sustentada"
- **AND** QUALIDADE block with "Curva suave"
- **AND** INTENSIDADE block with score and intensity label
- **AND** RESUMO block concatenating the templates

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

### Requirement: RuleEvaluation — per-rule evaluation state tracking
The system SHALL track evaluation state for each rule during the classification loop. A `RuleEvaluation` struct SHALL be produced for every evaluated rule, containing: `rule_id`, `matched_features` (list of satisfied required and optional features), `missing_features` (list of unsatisfied required and optional features), `activation_score` (weighted ratio of satisfied to total features), and `activated` (whether the rule generated a Fact).

The `activation_score` SHALL be computed as `Σ pesos_das_features_em_matched_features / Σ pesos_de_todas_as_features_da_regra (required + optional)`. Feature weights SHALL be defined in `FEATURE_WEIGHTS` (see R199 requirement).

Rules that fail gating or required-feature checks SHALL still produce a `RuleEvaluation` with `activated=False` and their partial `activation_score`. Rules skipped due to exclusive group already activated SHALL NOT produce an evaluation.

#### Scenario: Evaluation tracks matched and missing features
- **WHEN** VALE rule is evaluated with VALLEY_EARLY (True), FINAL_GT_INITIAL (True), AFTER_MIN_UP (True), RECOVERY_STRONG (False), SHORT_END_UP (False)
- **THEN** `matched_features` SHALL be `["VALLEY_EARLY", "FINAL_GT_INITIAL", "AFTER_MIN_UP"]`
- **AND** `missing_features` SHALL be `["RECOVERY_STRONG", "SHORT_END_UP"]`
- **AND** `activation_score` SHALL be 7.0/9.5 ≈ 0.74
- **AND** `activated` SHALL be False (min_optional=3 not met)

#### Scenario: Activated rule produces evaluation with activated=True
- **WHEN** ASCENDENTE rule is evaluated with TREND_UP (True), LONG_END_UP (True), MID_END_UP (True), MONOTONIC (False)
- **THEN** `activation_score` SHALL reflect all satisfied features
- **AND** `activated` SHALL be True

#### Scenario: Gated rule produces evaluation even when gate fails
- **WHEN** RECUPERACAO_SUSTENTADA is evaluated but VALE is not in activated_facts
- **THEN** a `RuleEvaluation` SHALL still be produced with `activated=False` and `activation_score` reflecting its own feature satisfaction

#### Scenario: Skipped rule produces no evaluation
- **WHEN** DESCENDENTE is skipped because ASCENDENTE already activated PRIMARY_CLASS
- **THEN** no `RuleEvaluation` SHALL be produced for DESCENDENTE

### Requirement: R199 — Classe Primaria por Dominancia (consome evaluations, nao reavalia)
The system SHALL provide a fallback mechanism R199 that activates when no primary class rule generated a Fact during the main evaluation loop. R199 SHALL consume the `RuleEvaluation` records already produced — it SHALL NOT re-evaluate features or rules.

R199 SHALL filter evaluations to those whose rule belongs to `exclusive_group == "PRIMARY_CLASS"` (excluding INDEFINIDA). It SHALL select the evaluation with the highest `activation_score`. If that score is >= 0.70, R199 SHALL generate a Fact for the corresponding class with `confidence = activation_score`, `fact_type = CLASSIFICATION`, and `template_id = "fallback_primary"`. If no evaluation reaches 0.70, R199 SHALL take no action (INDEFINIDA remains).

Feature weights for `activation_score` computation SHALL be:

| Feature | Weight | Rationale |
|---------|--------|-----------|
| VALLEY_EARLY, PEAK_EARLY, SIGMOIDAL_SHAPE, TREND_UP, TREND_DOWN, OSCILLATING | 3.0 | Assinaturas estruturais — maximo valor diagnostico |
| FINAL_GT_INITIAL, FINAL_LT_INITIAL, AFTER_MIN_UP, AFTER_MAX_DOWN, AMPLITUDE_LOW, DELTA_FINAL_LOW, SLOPE_FLAT | 2.0 | Evidencias direcionais e de planicidade |
| RECOVERY_STRONG, MONOTONIC | 1.5 | Confirmacao contextual |
| SHORT_END_UP, SHORT_END_DOWN, LONG_END_UP, LONG_END_DOWN, MID_END_UP | 1.0 | Evidencias segmentais |

#### Scenario: VALE promoted via R199 fallback
- **WHEN** no PRIMARY_CLASS fact was generated
- **AND** VALE evaluation has `activation_score = 0.74` (highest among primary class evaluations)
- **THEN** R199 SHALL generate fact VALE with confidence 0.74
- **AND** template `fallback_primary` SHALL be used
- **AND** `derived_from_features` SHALL list `matched_features` from the VALE evaluation

#### Scenario: No class reaches 70% threshold
- **WHEN** the highest `activation_score` among primary class evaluations is 0.55
- **THEN** R199 SHALL NOT generate any fact
- **AND** INDEFINIDA SHALL remain as the primary class

#### Scenario: R199 does not execute when primary class already activated
- **WHEN** VALE generated a Fact during the main evaluation loop
- **THEN** R199 SHALL NOT execute (PRIMARY_CLASS already set)

#### Scenario: R199 selects best among multiple partial evaluations
- **WHEN** VALE evaluation has score 0.74, PICO has 0.45, ASCENDENTE has 0.55
- **THEN** R199 SHALL select VALE (0.74 >= 0.70, highest score)

### Requirement: RECUPERACAO_LONGA — definicao matematica deterministica
The system SHALL provide a structural fact `RECUPERACAO_LONGA` that detects sustained upward trends. The feature `LONG_RECOVERY` SHALL be True when ALL of the following conditions are satisfied:

1. **TAMANHO MINIMO**: n >= 20 data points.
2. **SEGMENTO CONTIGUO**: There exists a contiguous segment S = rates[i..j] such that:
   - a) `|S| >= max(10, n * config.recuperacao_longa_min_pct)`, where `recuperacao_longa_min_pct` defaults to 0.15.
   - b) The proportion of positive point-to-point deltas in S is >= `config.recuperacao_longa_min_ratio` (default 0.70), where a delta is positive if `rates[k+1] - rates[k] > config.epsilon_slope`.
3. **SLOPE POSITIVO**: `numpy.polyfit(days[i..j], rates[i..j], 1)[0] > config.epsilon_slope`.
4. **AMPLITUDE SIGNIFICATIVA**: `(max(rates[i..j]) - min(rates[i..j])) >= amplitude_total * config.recuperacao_longa_min_amplitude`, where `recuperacao_longa_min_amplitude` defaults to 0.40.

If multiple segments satisfy all conditions, the longest segment SHALL be selected.

`RECUPERACAO_LONGA` SHALL be an independent structural fact (no `gated_by` restriction). Its score SHALL be (1, 2).

#### Scenario: Long sustained recovery detected
- **WHEN** a curve of 230 points has a segment of 80 contiguous points with 85% positive deltas (>= 70%), positive regression slope, and amplitude of 0.30 while total amplitude is 0.35 (86% >= 40%)
- **AND** 80 >= max(10, 230×0.15) = 35
- **THEN** LONG_RECOVERY SHALL be True
- **AND** fact RECUPERACAO_LONGA SHALL be generated with FactType STRUCTURE

#### Scenario: Segment too short rejected
- **WHEN** a curve of 230 points has the best qualifying segment of only 20 points (20 < 35)
- **THEN** LONG_RECOVERY SHALL be False

#### Scenario: Insufficient positive deltas rejected
- **WHEN** a segment of 50 points has only 55% positive deltas (55% < 70%)
- **THEN** LONG_RECOVERY SHALL be False (even if other criteria pass)

#### Scenario: Negative slope rejected
- **WHEN** a segment has sufficient length and positive deltas, but regression slope is negative
- **THEN** LONG_RECOVERY SHALL be False

#### Scenario: Low amplitude segment rejected
- **WHEN** a segment has sufficient length, positive deltas, and positive slope, but amplitude is only 10% of total curve amplitude (10% < 40%)
- **THEN** LONG_RECOVERY SHALL be False

#### Scenario: Multiple qualifying segments — longest wins
- **WHEN** segment A of 60 points and segment B of 90 points both satisfy all criteria
- **THEN** segment B SHALL be selected and LONG_RECOVERY SHALL be True

### Requirement: VOLATILIDADE_MODERADA quality fact
The system SHALL provide a quality fact `VOLATILIDADE_MODERADA` that activates when volatility is between the low and high thresholds. The feature `VOLATILITY_MODERATE` SHALL be True when `config.volatilidade_baixa < indice_volatilidade < config.volatilidade_alta`.

#### Scenario: Moderate volatility detected
- **WHEN** `indice_volatilidade = 0.043`, `volatilidade_baixa = 0.01`, and `volatilidade_alta = 0.05`
- **THEN** VOLATILITY_MODERATE SHALL be True (0.01 < 0.043 < 0.05)
- **AND** fact VOLATILIDADE_MODERADA SHALL be generated with FactType QUALITY

#### Scenario: Low volatility does not trigger moderate
- **WHEN** `indice_volatilidade = 0.008` and `volatilidade_baixa = 0.01`
- **THEN** VOLATILITY_MODERATE SHALL be False
- **AND** VOLATILITY_LOW SHALL be True

### Requirement: ScoringPolicy entries for new facts
The ScoringPolicy SHALL include the following new entries:

| Fact ID | Score Base | Weight Level |
|---------|-----------|-------------|
| VOLATILIDADE_MODERADA | 0 | ×1 |
| RECUPERACAO_LONGA | +1 | ×2 |

#### Scenario: RECUPERACAO_LONGA contributes to score
- **WHEN** INDEFINIDA (0×3) and RECUPERACAO_LONGA (+1×2) are the only facts
- **THEN** total score SHALL be 2
- **AND** intensity SHALL be "Mercado estavel" (score < 3)

### Requirement: Templates for new facts and fallback
The system SHALL provide the following templates in the `pt` locale:

| template_id | Text |
|-------------|------|
| `fallback_primary` | "A curva nao atende plenamente a nenhuma classe geometrica, mas apresenta evidencias parciais de {classe} (confianca: {pct})." |
| `volmod_qual` | "A volatilidade da curva e moderada, indicando nivel intermediario de oscilacao nas expectativas." |
| `longrec_struct` | "Observa-se uma recuperacao longa e sustentada ao longo de parte significativa da curva, indicando persistencia direcional." |

The `{classe}` placeholder SHALL be replaced with the promoted class name (e.g., "VALE"). The `{pct}` placeholder SHALL be replaced with the confidence percentage (e.g., "74%").

#### Scenario: Fallback template renders with placeholders resolved
- **WHEN** R199 promotes VALE with confidence 0.74
- **THEN** the report SHALL display "evidencias parciais de VALE (confianca: 74%)"


