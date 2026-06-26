## REMOVED Requirements

### Requirement: Metric extraction from detailed rate data — IndiceTendencia
The `indice_tendencia` field computed as `delta_final / amplitude` is removed from `DetailedMetrics`, replaced by `slope_global` (linear regression coefficient over all points).

**Reason**: `IndiceTendencia` uses only endpoint values and is sensitive to outliers at curve extremes, producing unreliable direction classification for curves with valleys or peaks near the endpoints.

**Migration**: Use `DetailedMetrics.slope_global` for direction detection. Existing tests referencing `indice_tendencia` must use `slope_global` instead.

### Requirement: Flat rule evaluation architecture (R001–R020 as independent functions)
The flat rule evaluation where 20 rules (R001–R020) compete independently in the same evaluation plane is removed. Rules are replaced by a 5-level hierarchical classifier.

**Reason**: Flat evaluation produces contradictory outputs (e.g., "curva plana" + "curva com vale" + "formato sigmoide" simultaneously). There is no mutual exclusion between semantically conflicting concepts.

**Migration**: Use the new `_classifier.py` 5-level hierarchical engine. The facade `analyze()` function maintains the same public API contract.

### Requirement: AnalysisThresholds dataclass
The `AnalysisThresholds` frozen dataclass in `_thresholds.py` is removed. Thresholds are integrated as named constants within the classifier module.

**Reason**: With the hierarchical architecture, thresholds are level-specific and don't benefit from a single flat dataclass. User-customizable thresholds are exposed as keyword arguments to `analyze()`.

**Migration**: Pass threshold overrides as keyword arguments to `analyze()` instead of constructing an `AnalysisThresholds` instance.

## MODIFIED Requirements

### Requirement: Metric extraction from detailed rate data
The system SHALL extract quantitative metrics from a list of `RateRecord` objects. Metrics SHALL include: initial rate, final rate, maximum rate, minimum rate, index of the global minimum, **linear regression slope over all points (`slope_global`)**, standard deviation of successive rate differences, and count of direction changes. The `indice_tendencia` field is removed.

#### Scenario: Metrics computed from valid records
- **WHEN** the system receives a non-empty list of RateRecord objects
- **THEN** all metrics are computed deterministically using numpy operations
- **AND** `slope_global` SHALL be `numpy.polyfit(days, rates, 1)[0]` — the coefficient of the best-fit line through all points

#### Scenario: Empty records produce zero/None metrics
- **WHEN** the system receives an empty list
- **THEN** all metrics SHALL return safe defaults (0.0, None, or empty)
- **AND** `slope_global` SHALL be 0.0

### Requirement: Aggregate score computation with direction-aware classification
The system SHALL compute an aggregate score using weighted contributions from 3 hierarchical levels: Level 1 (Primary, weight ×3), Level 2 (Structural, weight ×2), Level 3 (Quality, weight ×1). The system SHALL also compute per-level confidence as the ratio of activated rules to applicable rules. The score SHALL be classified into intensity labels based on the direction determined by the primary class.

#### Scenario: Weighted score from all levels
- **WHEN** primary class is VALE (base +2, weight ×3 = +6) and RECUPERACAO activates (+1, weight ×2 = +2) and SUAVE activates (+1, weight ×1 = +1)
- **THEN** total score is 9

#### Scenario: Per-level confidence computed
- **WHEN** Level 2 has 3 applicable rules and 2 activated
- **THEN** Level 2 confidence SHALL be 0.67 (67%)

## ADDED Requirements

### Requirement: Hierarchical 5-level classification architecture
The system SHALL classify curves using a 5-level hierarchical architecture instead of flat rule evaluation. Level 1 (Primary Classification) SHALL be mutually exclusive. Level 2 (Structural Characteristics) SHALL be gated by the primary class. Level 3 (Curve Quality) SHALL always evaluate all rules independently.

#### Scenario: Hierarchy enforces mutual exclusion
- **WHEN** a curve satisfies both VALE and ASCENDENTE conditions
- **THEN** VALE SHALL be chosen (higher priority) and ASCENDENTE SHALL not be evaluated

### Requirement: Level 1 — Primary Classification
The system SHALL classify each curve into exactly one primary class, evaluated in priority order: OSCILANTE > VALE > PICO > SIGMOIDE > ASCENDENTE > DESCENDENTE > PLANA. The first class whose conditions are satisfied SHALL be selected.

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

### Requirement: Level 2 — Structural Characteristics (gated)
The system SHALL evaluate structural rules only when enabled by the primary class. OSCILANTE and PLANA SHALL enable no structural rules.

#### Scenario: Recovery only evaluated for VALE
- **WHEN** primary class is VALE
- **THEN** RECUPERACAO rule SHALL be evaluated (longo.delta > 0 AND medio.delta > 0)

#### Scenario: Recovery not evaluated for ASCENDENTE
- **WHEN** primary class is ASCENDENTE
- **THEN** RECUPERACAO rule SHALL NOT be evaluated (not applicable)

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

### Requirement: Confidence metric per level
The system SHALL compute confidence for each level as the ratio of activated rules to applicable (evaluated) rules in that level. Level 1 SHALL always have 100% confidence (exactly one class chosen). If no rules are applicable in a level, confidence SHALL be reported as "N/A".

#### Scenario: Partial structural confidence
- **WHEN** Level 2 has 3 applicable rules and 2 activate
- **THEN** Level 2 confidence SHALL be 67%

#### Scenario: No applicable rules
- **WHEN** primary class is PLANA and Level 2 has 0 applicable rules
- **THEN** Level 2 confidence SHALL be "N/A"

### Requirement: Report with FORMA / INTENSIDADE separation
The system SHALL generate a report with separate sections: FORMA (primary class + structural characteristics), QUALIDADE (curve quality attributes), and INTENSIDADE (weighted score + confidence + intensity label).

#### Scenario: Full report with all sections
- **WHEN** analysis completes with a VALE curve, RECUPERACAO, and SUAVE
- **THEN** the report SHALL contain FORMA section with "Vale" and "Recuperação sustentada"
- **AND** QUALIDADE section with "Curva suave"
- **AND** INTENSIDADE section with score, confidence percentages, and intensity label
