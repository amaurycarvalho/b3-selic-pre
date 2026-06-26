## ADDED Requirements

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
- **WHEN** a curve of 230 points has a segment of 80 contiguous points with 85% positive deltas (≥ 70%), positive regression slope, and amplitude of 0.30 while total amplitude is 0.35 (86% ≥ 40%)
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

## MODIFIED Requirements

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

### Requirement: Complete score weight table in ScoringPolicy
The ScoringPolicy SHALL define the following mapping (+ marks additions):

| Fact ID | Score Base | Weight Level |
|---------|-----------|-------------|
| ASCENDENTE, DESCENDENTE, VALE, PICO, SIGMOIDE | +2 | ×3 |
| OSCILANTE | +1 | ×3 |
| PLANA, INDEFINIDA | 0 | ×3 |
| RECUPERACAO_SUSTENTADA | +1 | ×2 |
| **+ RECUPERACAO_LONGA** | **+1** | **×2** |
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
| **+ VOLATILIDADE_MODERADA** | **0** | **×1** |

Classification labels SHALL remain: 0–2 Estavel, 3–5 Moderada, 6–8 Relevante, 9–11 Significativa, 12+ Estrutural.

#### Scenario: New facts integrated into score calculation
- **WHEN** VALE (2×3=6), RECUPERACAO_LONGA (1×2=2), and VOLATILIDADE_MODERADA (0×1=0) are generated
- **THEN** total score SHALL be 8
- **AND** intensity SHALL be "Reprecificacao ascendente relevante"

### Requirement: InferenceConfig extended with new thresholds
The `InferenceConfig` dataclass SHALL include the following new parameters for RECUPERACAO_LONGA detection:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `recuperacao_longa_min_pct` | 0.15 | Minimum fraction of curve length for a qualifying segment |
| `recuperacao_longa_min_ratio` | 0.70 | Minimum proportion of positive deltas in the segment |
| `recuperacao_longa_min_amplitude` | 0.40 | Minimum ratio of segment amplitude to total amplitude |

All existing parameters SHALL retain their current defaults. No existing defaults SHALL be changed.

#### Scenario: Custom thresholds via InferenceConfig
- **WHEN** user passes `InferenceConfig(recuperacao_longa_min_pct=0.20, recuperacao_longa_min_ratio=0.80)`
- **THEN** LONG_RECOVERY detection SHALL use 20% length and 80% positive delta requirements

#### Scenario: Threshold override via analyze()
- **WHEN** user passes `threshold_overrides={"recuperacao_longa_min_amplitude": 0.30}`
- **THEN** the override value 0.30 SHALL replace the default 0.40
