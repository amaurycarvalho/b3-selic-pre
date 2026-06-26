## 1. Extend InferenceConfig

- [x] 1.1 Add `recuperacao_longa_min_pct: float = 0.15` to `InferenceConfig` in `_config.py`
- [x] 1.2 Add `recuperacao_longa_min_ratio: float = 0.70` to `InferenceConfig` in `_config.py`
- [x] 1.3 Add `recuperacao_longa_min_amplitude: float = 0.40` to `InferenceConfig` in `_config.py`

## 2. Add new features

- [x] 2.1 Add `VOLATILITY_MODERATE` boolean feature in `_features.py`: True when `config.volatilidade_baixa < indice_volatilidade < config.volatilidade_alta`
- [x] 2.2 Add `LONG_RECOVERY` boolean feature in `_features.py` with deterministic criteria: find longest contiguous segment where (a) |segment| >= max(10, n * config.recuperacao_longa_min_pct), (b) proportion of positive deltas >= config.recuperacao_longa_min_ratio, (c) regression slope > config.epsilon_slope, (d) segment amplitude >= total_amplitude * config.recuperacao_longa_min_amplitude. Select longest segment if multiple qualify.
- [x] 2.3 Ensure both new features have correct `derived_from_metrics` references

## 3. Update Rule Registry

- [x] 3.1 Remove `gated_by` from ACHATAMENTO rule
- [x] 3.2 Remove `gated_by` from EMPINAMENTO rule
- [x] 3.3 Remove `gated_by` from TORCAO rule
- [x] 3.4 Remove `gated_by` from DEGRAUS rule
- [x] 3.5 Remove `gated_by` from MONOTONIA_STRUCT rule
- [x] 3.6 Keep `gated_by: ["VALE"]` on RECUPERACAO_SUSTENTADA (no change)
- [x] 3.7 Add RECUPERACAO_LONGA rule (priority 206, no exclusive_group, no gated_by, required_features=["LONG_RECOVERY"], fact_type=STRUCTURE, template_id=`longrec_struct`)
- [x] 3.8 Add VOLATILIDADE_MODERADA rule (priority 407, no exclusive_group, no gated_by, required_features=["VOLATILITY_MODERATE"], fact_type=QUALITY, template_id=`volmod_qual`)

## 4. Implement RuleEvaluation struct and evaluation state tracking

- [x] 4.1 Add `RuleEvaluation` dataclass to `_classifier.py` with fields: `rule_id: str`, `matched_features: list[str]`, `missing_features: list[str]`, `activation_score: float`, `activated: bool`
- [x] 4.2 Define `FEATURE_WEIGHTS` dict in `_classifier.py` mapping feature names to weights (3.0 / 2.0 / 1.5 / 1.0 tiers per design.md D2)
- [x] 4.3 Modify the main evaluation loop to compute `activation_score` for each rule: `sum(weights of satisfied features) / sum(weights of all required + optional features)`
- [x] 4.4 For each evaluated rule, populate `matched_features` and `missing_features` lists from the feature satisfaction check
- [x] 4.5 Append `RuleEvaluation` to an `evaluations` list for every rule that is evaluated (including those that fail gating or required-feature checks)
- [x] 4.6 Skip creating `RuleEvaluation` for rules skipped because their `exclusive_group` was already activated

## 5. Implement R199 fallback (consumes evaluations)

- [x] 5.1 After the main loop, check if any fact with `fact_type == FactType.CLASSIFICATION` was generated
- [x] 5.2 If no classification fact exists, filter `evaluations` to those whose rule has `exclusive_group == "PRIMARY_CLASS"` (excluding INDEFINIDA)
- [x] 5.3 Select the `RuleEvaluation` with highest `activation_score`
- [x] 5.4 If `activation_score >= 0.70`, generate Fact: `id=corresponding generated_fact`, `confidence=activation_score`, `fact_type=CLASSIFICATION`, `derived_from_features=matched_features`, `template_id="fallback_primary"`
- [x] 5.5 If `activation_score < 0.70`, do nothing (INDEFINIDA already generated)
- [x] 5.6 Store `evaluations` list on the classifier result or return it alongside facts for auditability (add to return type or make accessible)

## 6. Update ScoringPolicy

- [x] 6.1 Add `"VOLATILIDADE_MODERADA": (0, 1)` to `SCORING_POLICY` in `_scoring.py`
- [x] 6.2 Add `"RECUPERACAO_LONGA": (1, 2)` to `SCORING_POLICY` in `_scoring.py`

## 7. Add templates

- [x] 7.1 Add `fallback_primary` template to `_templates.py` under `"pt"`: "A curva nao atende plenamente a nenhuma classe geometrica, mas apresenta evidencias parciais de {classe} (confianca: {pct})."
- [x] 7.2 Add `volmod_qual` template: "A volatilidade da curva e moderada, indicando nivel intermediario de oscilacao nas expectativas."
- [x] 7.3 Add `longrec_struct` template: "Observa-se uma recuperacao longa e sustentada ao longo de parte significativa da curva, indicando persistencia direcional."
- [x] 7.4 Update report builder to substitute `{classe}` and `{pct}` placeholders in `fallback_primary` template at render time

## 8. Tests

- [x] 8.1 Test RuleEvaluation captures matched_features, missing_features, activation_score correctly for a partially-satisfied rule
- [x] 8.2 Test RuleEvaluation is NOT created for rules skipped due to exclusive group already activated
- [x] 8.3 Test R199 promotes VALE when activation_score = 0.74 (>= 0.70) and no primary class activated directly
- [x] 8.4 Test R199 does NOT promote when best activation_score = 0.55 (< 0.70)
- [x] 8.5 Test R199 does not execute when a primary class already activated directly
- [x] 8.6 Test R199 selects class with highest activation_score among multiple candidates
- [x] 8.7 Test LONG_RECOVERY True: curve with 80-pt segment, 85% positive deltas, positive slope, amplitude 86% of total
- [x] 8.8 Test LONG_RECOVERY False: segment too short (< max(10, n*0.15))
- [x] 8.9 Test LONG_RECOVERY False: positive delta ratio below 70%
- [x] 8.10 Test LONG_RECOVERY False: negative regression slope in segment
- [x] 8.11 Test LONG_RECOVERY False: segment amplitude below 40% of total
- [x] 8.12 Test VOLATILITY_MODERATE True when 0.01 < volatilidade < 0.05
- [x] 8.13 Test ACHATAMENTO activates when primary class is INDEFINIDA (gate removed)
- [x] 8.14 Test RECUPERACAO_SUSTENTADA does NOT activate when primary class is INDEFINIDA (gate retained)
- [x] 8.15 Test score includes RECUPERACAO_LONGA (+2) and VOLATILIDADE_MODERADA (+0)
- [x] 8.16 Test fallback_primary template renders class name and confidence percentage correctly

## 9. Verification

- [x] 9.1 Run full test suite: `python -m pytest tests/ -v`
- [x] 9.2 Run linter: `ruff check src/`
- [x] 9.3 Bump `RULESET_VERSION` in `_report.py` to "1.1.0"
- [x] 9.4 Manual validation: inject valley+plateau curve data, verify output shows VALE (via R199, ~74%), RECUPERACAO_LONGA, VOLATILIDADE_MODERADA
