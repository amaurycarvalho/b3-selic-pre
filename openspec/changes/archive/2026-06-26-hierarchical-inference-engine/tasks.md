## 1. Update Metrics Extraction

- [x] 1.1 Add `slope_global: float` field to `DetailedMetrics` dataclass in `_metrics.py`
- [x] 1.2 Compute `slope_global = np.polyfit(days, rates, 1)[0]` in `extract_detailed_metrics()`
- [x] 1.3 Remove `indice_tendencia: float` from `DetailedMetrics`
- [x] 1.4 Remove `indice_tendencia` calculation (`delta_final / amplitude`) from `extract_detailed_metrics()`
- [x] 1.5 Set `slope_global = 0.0` in the empty-records default return

## 2. Create Hierarchical Classifier

- [x] 2.1 Create `_classifier.py` with `InferenceResult`, `LevelResult` dataclasses
- [x] 2.2 Implement `classify_primary()` — Level 1 classification with priority order OSCILANTE > VALE > PICO > SIGMOIDE > ASC > DESC > PLANA
- [x] 2.3 Implement OSCILANTE condition: `qtd_mudancas / n >= 0.15`
- [x] 2.4 Implement VALE condition: global minimum position < 50%, final > initial, >=80% recovery deltas
- [x] 2.5 Implement PICO condition: global maximum position > 0 and < 50%, >=80% negative deltas after peak
- [x] 2.6 Implement SIGMOIDE condition: >=2 inflections with each segment > 15% of curve
- [x] 2.7 Implement ASCENDENTE condition: `slope_global > 0.00005`
- [x] 2.8 Implement DESCENDENTE condition: `slope_global < -0.00005`
- [x] 2.9 Implement PLANA condition: `amplitude < 0.10` AND `|delta_final| < 0.05` AND `|slope_global| < 0.00005`

## 3. Implement Level 2 — Structural Characteristics (Gated)

- [x] 3.1 Define gating table: which structural rules are enabled per primary class
- [x] 3.2 Implement RECUPERACAO rule (gated: only for VALE)
- [x] 3.3 Implement ACHATAMENTO/EMPINAMENTO rules (gated: VALE, ASC, DESC)
- [x] 3.4 Implement TORCAO rule (gated: PICO, DESC)
- [x] 3.5 Implement MONOTONIA rule (gated: ASC, DESC)
- [x] 3.6 Implement MUDANCA_ESTRUTURAL rule with stricter condition (slope diff > 30%, gated: SIGMOIDE)
- [x] 3.7 Implement `evaluate_structural(primary_class, metrics)` dispatcher

## 4. Implement Level 3 — Curve Quality (Always Evaluated)

- [x] 4.1 Implement SUAVE rule: `indice_suavidade / amplitude <= 0.01` or `amplitude == 0`
- [x] 4.2 Implement SERRILHADA rule: `indice_suavidade >= 0.15`
- [x] 4.3 Implement CONSENSO rule: `amplitude < 0.10`
- [x] 4.4 Implement DISPERSAO rule: `amplitude > 1.50`
- [x] 4.5 Implement `evaluate_quality(metrics)` function

## 5. Implement Level 4 — Weighted Score and Confidence

- [x] 5.1 Define score weights: Level 1 ×3, Level 2 ×2, Level 3 ×1
- [x] 5.2 Assign base scores per primary class: ASC/DESC/VALE/PICO/SIGMOIDE = +2, OSCILANTE = +1, PLANA = 0, INDEFINIDA = 0
- [x] 5.3 Implement `compute_score()` with weighted sum
- [x] 5.4 Implement `compute_confidence()` per level: activated / applicable
- [x] 5.5 Implement `classify_intensity(score, direction)` producing intensity label

## 6. Implement Level 5 — Report Assembly

- [x] 6.1 Update `_report.py` to support FORMA / QUALIDADE / INTENSIDADE sections
- [x] 6.2 Generate FORMA section: primary class name + structural characteristics text
- [x] 6.3 Generate QUALIDADE section: quality rule texts
- [x] 6.4 Generate INTENSIDADE section: weighted score + confidence percentages + intensity label
- [x] 6.5 Handle edge case: no quality rules activated → omit QUALIDADE section

## 7. Update Facade

- [x] 7.1 Update imports in `__init__.py`: import from `_classifier.py` instead of `_rules.py`
- [x] 7.2 Integrate `run_inference()` call in `analyze()`
- [x] 7.3 Integrate `evaluate_structural()` and `evaluate_quality()` via `run_inference()`
- [x] 7.4 Integrate `compute_score()` and `compute_confidence()` via `run_inference()`
- [x] 7.5 Update `analyze()` to accept threshold overrides as keyword arguments
- [x] 7.6 Emit placeholder for consolidated/evolution modes unchanged
- [x] 7.7 Remove `AnalysisThresholds` from `__all__`

## 8. Remove Old Files

- [x] 8.1 Delete `_rules.py` (replaced by `_classifier.py`)
- [x] 8.2 Delete `_thresholds.py` (thresholds integrated into `_classifier.py`)

## 9. Update Tests

- [x] 9.1 Add test for `slope_global` in `TestDetailedMetrics`
- [x] 9.2 Add tests for each primary class (OSCILANTE, VALE, PICO, SIGMOIDE, ASC, DESC, PLANA)
- [x] 9.3 Add test for PLANA requiring ALL 3 conditions
- [x] 9.4 Add test for priority order (VALE overrides ASCENDENTE)
- [x] 9.5 Add tests for gating: structural rules only fire for correct primary class
- [x] 9.6 Add tests for weighted score computation
- [x] 9.7 Add tests for confidence per level
- [x] 9.8 Add tests for intensity classification with direction
- [x] 9.9 Add tests for report FORMA/QUALIDADE/INTENSIDADE sections
- [x] 9.10 Add test for MUDANCA_ESTRUTURAL stricter condition (slope diff > 30%)
- [x] 9.11 Add test for SIGMOIDE minimum segment size (15%)
- [x] 9.12 Run full test suite and verify all pass (116/116)

## 10. Verify with Real Data

- [x] 10.1 Run analysis on actual B3 SELIC Pré data with new hierarchical engine
- [x] 10.2 Verify primary class is sensible (no more false PLANA on ascending curves — INDEFINIDA when no pattern)
- [x] 10.3 Verify no contradictory statements in report (exclusive primary class)
- [x] 10.4 Verify FORMA/QUALIDADE/INTENSIDADE separation in report output
- [x] 10.5 Calibrate `slope_global` threshold (0.00005) if needed based on real data
