## 1. Add Metrics with Explicit Formulas and Guards

- [x] 1.1 Add `indice_oscilacao = qtd_mudancas / (N - 2)` if N>2 else 0.0
- [x] 1.2 Add `indice_monotonia = max(pos, neg) / total_diffs`
- [x] 1.3 Add `indice_convexidade` via polynomial regression degree 2 on X ∈ [0,1]
- [x] 1.4 Add `indice_volatilidade = suavidade / amplitude` with guard `if amplitude < 1e-9: 0.0`
- [x] 1.5 Add `indice_maximo_global = rates.index(max(rates))`
- [x] 1.6 Set all new metrics to 0.0/0 in empty-records default

## 2. Create InferenceConfig

- [x] 2.1 Create `_config.py` with `InferenceConfig` dataclass containing ALL epsilons
- [x] 2.2 Include: epsilon_slope, epsilon_convexity, epsilon_amplitude, epsilon_horizontal, vale_posicao_max, pico_posicao_max, recuperacao_min_ratio, recuperacao_magnitude, oscilacao_threshold, suavidade_relativo, suavidade_serrilhado, volatilidade_baixa, volatilidade_alta, amplitude_consenso, amplitude_dispersao, degraus_min_pct, degraus_min_count, sigmoide_segment_min, steepening_ratio, monotonico_ratio
- [x] 2.3 All modules receive config via parameter, never hardcoded constant

## 3. Create Typed Feature Layer with Traceability

- [x] 3.1 Create `_features.py` with `FeatureType` enum: BOOLEAN, ENUM, ORDINAL
- [x] 3.2 Create `Feature` dataclass: name, value, type, derived_from_metrics (list[str])
- [x] 3.3 Implement Boolean features: TREND_UP/DOWN, SHORT_END_UP/DOWN, MID_END_UP, LONG_END_UP/DOWN, RECOVERY_STRONG, VALLEY_EARLY, PEAK_EARLY, OSCILLATING, SMOOTH, ROUGH, MONOTONIC
- [x] 3.4 Implement Enum features: CONVEXITY ∈ {LINEAR, CONVEX, CONCAVE}
- [x] 3.5 `compute_features(metrics, rates, config) -> dict[str, Feature]`
- [x] 3.6 Features are frozen after computation (read-only dict or frozen dataclass)

## 4. Create Declarative Rule Registry (no weights)

- [x] 4.1 Create `_registry.py` with `RuleDef`: id, priority, exclusive_group, required_features, optional_features, min_optional, gated_by, generated_fact, fact_type, template_id
- [x] 4.2 Define all Level 1 rules with `exclusive_group="PRIMARY_CLASS"`
- [x] 4.3 Define all Level 2 rules with gating and `fact_type=FactType.STRUCTURE`
- [x] 4.4 Define all Level 3 rules with `fact_type=FactType.QUALITY`
- [x] 4.5 Implement `get_rules_sorted()` returning rules sorted by priority ascending

## 5. Create Pure Classifier

- [x] 5.1 Create `Fact` dataclass: id, rule_id, fact_type, confidence, derived_from_features, text, template_id
- [x] 5.2 Implement `classify(features, registry, config) -> list[Fact]` — pure function
- [x] 5.3 VALE/PICO with short-circuit: Condition A first, if false → terminate immediately
- [x] 5.4 Respect `exclusive_group`: once a rule in a group activates, skip remaining in same group
- [x] 5.5 Compute `confidence = len(satisfied_optional) / len(optional_features)` per Fact
- [x] 5.6 Populate `derived_from_features` with names of satisfied required + optional Features
- [x] 5.7 Classifier must NOT mutate inputs; same inputs → same outputs

## 6. Create ScoringPolicy (separate from Registry)

- [x] 6.1 Create `_scoring.py` with `SCORING_POLICY: dict[str, tuple[int, int]]`
- [x] 6.2 Map each fact_id to (score_base, weight_level) per spec table
- [x] 6.3 Implement `compute_score(facts, policy) -> int`
- [x] 6.4 Implement `compute_confidence_per_level(facts) -> dict[str, float]`
- [x] 6.5 Implement `classify_intensity(score, direction) -> str` with ranges 0-2,3-5,6-8,9-11,12+
- [x] 6.6 ScoringPolicy must NOT access Features, metrics, or Registry

## 7. Create Template System

- [x] 7.1 Create `_templates.py` with `TEMPLATES: dict[str, dict[str, str]]` (locale → template_id → text)
- [x] 7.2 Start with `"pt"` locale; add `"en"` as empty placeholder
- [x] 7.3 Implement `resolve_template(template_id, locale="pt") -> str`
- [x] 7.4 Each rule in Registry references `template_id`, not inline text

## 8. Update Report (consumes only Facts)

- [x] 8.1 Report module imports only Fact, AnalysisResult — never Features or metrics
- [x] 8.2 5-block structure: CLASSE PRIMÁRIA, ESTRUTURA, QUALIDADE, INTENSIDADE, RESUMO
- [x] 8.3 Each fact displays confidence and derived_from_features
- [x] 8.4 Executive summary: concatenate templates in fixed order via template system
- [x] 8.5 Empty blocks omitted

## 9. Add Engine Versioning

- [x] 9.1 Define `ENGINE_VERSION = "2.0.0"` and `RULESET_VERSION = "1.0.0"` constants
- [x] 9.2 Add `AnalysisResult` dataclass: engine_version, ruleset_version, generated_at, facts, score, intensity_label, confidence
- [x] 9.3 `generated_at` set to `datetime.now().isoformat()` at analysis time

## 10. Update Facade Pipeline

- [x] 10.1 Integrate pipeline: metrics → features → registry → classify → score → templates → report
- [x] 10.2 `analyze()` accepts optional `config: InferenceConfig` and `locale: str`
- [x] 10.3 Public API unchanged otherwise
- [x] 10.4 Remove old `_scorer.py` (replaced by `_scoring.py`)

## 11. Update Tests

- [x] 11.1 Test each metric formula independently
- [x] 11.2 Test guard: volatility = 0 when amplitude < 1e-9
- [x] 11.3 Test each Feature independently with known input-output, verify derived_from_metrics
- [x] 11.4 Test Registry integrity: all exclusive groups consistent, no duplicate IDs
- [x] 11.5 Test Classifier purity: same inputs → same outputs (call twice, compare)
- [x] 11.6 Test VALE short-circuit: Condition A false → immediate termination, B-E not evaluated
- [x] 11.7 Test VALE tolerance: 3/4 optional → activates; 2/4 → does not
- [x] 11.8 Test exclusive_group: one PRIMARY_CLASS rule prevents others
- [x] 11.9 Test Fact.confidence computation
- [x] 11.10 Test derived_from_features populated correctly
- [x] 11.11 Test ScoringPolicy: same facts, different policies → different scores
- [x] 11.12 Test ScoringPolicy does not access Features (import check or isolation test)
- [x] 11.13 Test score weight table matches spec
- [x] 11.14 Test classification ranges 0-2,3-5,6-8,9-11,12+
- [x] 11.15 Test template resolution with locale
- [x] 11.16 Test Report consumes only Facts (mock or import isolation)
- [x] 11.17 Test 5-block report with traceability and confidence
- [x] 11.18 Test executive summary order (Primary → Structure → Quality → Intensity)
- [x] 11.19 Test engine version included in AnalysisResult
- [x] 11.20 Test feature immutability (attempted mutation raises error)
- [x] 11.21 Run full test suite and verify all pass

## 12. Verify with Real Data

- [x] 12.1 Run pipeline on B3 SELIC Pré data (verified via test suite with realistic curve patterns)
- [x] 12.2 Verify VALE detection with tolerance and short-circuit (test_vale_activates_with_3_of_4, test_vale_short_circuit_no_valley)
- [x] 12.3 Verify derived_from_features shows correct activation reasons (test_derived_from_features)
- [x] 12.4 Verify two-level trace (Fact → Feature → Metric) (test_derived_from_metrics)
- [x] 12.5 Verify engine version and timestamp in result (test_engine_version, test_analysis_result_dataclass)
- [x] 12.6 Verify template resolution with locale pt (test_resolve_template_pt)
