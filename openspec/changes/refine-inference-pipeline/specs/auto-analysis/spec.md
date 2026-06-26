## MODIFIED Requirements

### Requirement: ScoringPolicy independent of Rule Registry
The system SHALL store rule weights in a separate ScoringPolicy module, not in the Rule Registry. The Registry SHALL define only rule logic (required features, generated fact, template_id, exclusive_group). The ScoringPolicy SHALL map `fact_id → (score_base, weight_level)`. This allows different scoring policies without modifying rules.

#### Scenario: Two scoring policies produce different scores
- **WHEN** Conservative policy assigns VALE weight (1, 2) and Aggressive policy assigns (3, 3)
- **THEN** the same Facts produce different total scores without any rule changes

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

### Requirement: Exclusive groups in Registry
The system SHALL support `exclusive_group` in RuleDef. When a rule from a group activates, all other rules in the same group SHALL be skipped. Example: `ASCENDENTE` and `DESCENDENTE` belong to `"PRIMARY_CLASS"` — only one may be chosen.

#### Scenario: Exclusive group prevents contradictions
- **WHEN** `ASCENDENTE` activates in group `"PRIMARY_CLASS"`
- **THEN** `DESCENDENTE` and `PLANA` in the same group SHALL NOT be evaluated

### Requirement: Confidence per Fact
Each Fact SHALL carry a `confidence` field computed as `satisfied_optional / total_optional`. For rules without optional features, confidence SHALL be 1.0. Confidence SHALL be displayed in the report.

#### Scenario: Partial confidence
- **WHEN** VALE activates with 3 of 4 optional conditions
- **THEN** `fact.confidence` SHALL be 0.75

#### Scenario: Full confidence
- **WHEN** a rule with no optional features activates
- **THEN** `fact.confidence` SHALL be 1.0

### Requirement: InferenceConfig centralizes all thresholds
The system SHALL define all epsilon thresholds in a single `InferenceConfig` dataclass. Every module that needs a threshold SHALL receive it via `InferenceConfig`, never via hardcoded constant. The dataclass SHALL include: `epsilon_slope`, `epsilon_convexity`, `epsilon_amplitude`, `epsilon_horizontal`, `vale_posicao_max`, `pico_posicao_max`, `recuperacao_min_ratio`, `recuperacao_magnitude`, and all other configurable limits.

#### Scenario: All thresholds in one place
- **WHEN** a user wants to adjust the slope threshold
- **THEN** they SHALL pass `InferenceConfig(epsilon_slope=0.0001)` without modifying any source file

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

### Requirement: Complete score weight table in ScoringPolicy
The ScoringPolicy SHALL define the following mapping:

| Fact ID | Score Base | Weight Level |
|---------|-----------|-------------|
| ASCENDENTE, DESCENDENTE, VALE, PICO, SIGMOIDE | +2 | ×3 |
| OSCILANTE | +1 | ×3 |
| PLANA, INDEFINIDA | 0 | ×3 |
| RECUPERACAO_SUSTENTADA | +1 | ×2 |
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

Classification labels: 0–2 Estável, 3–5 Moderada, 6–8 Relevante, 9–11 Significativa, 12+ Estrutural.

### Requirement: Report structure — 5 blocks with traceability
The system SHALL generate a report with 5 blocks: (1) CLASSE PRIMÁRIA, (2) ESTRUTURA, (3) QUALIDADE, (4) INTENSIDADE, (5) RESUMO. Each fact SHALL display its confidence and `derived_from_features` trace. The summary SHALL concatenate templates in fixed order (Primary → Structure → Quality → Intensity). Empty blocks SHALL be omitted.
