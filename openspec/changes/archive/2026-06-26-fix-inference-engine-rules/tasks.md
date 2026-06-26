## 1. Update Metrics Extraction

- [x] 1.1 Add `indice_minimo_global: int` field to `DetailedMetrics` dataclass in `_metrics.py`
- [x] 1.2 Populate `indice_minimo_global` with `rates.index(taxa_minima)` in `extract_detailed_metrics()`
- [x] 1.3 Set `indice_minimo_global = 0` in the empty-records default return

## 2. Update Thresholds

- [x] 2.1 Rename `suavidade_percentil` to `suavidade_relativo` in `AnalysisThresholds` (default 0.01)
- [x] 2.2 Add `oscilacao_ratio: float = 0.30` for R015
- [x] 2.3 Add `amplitude_reduzida: float = 0.10` for R016
- [x] 2.4 Add `amplitude_elevada: float = 1.50` for R017
- [x] 2.5 Add `curva_invertida_delta: float = 0.10` for R018
- [x] 2.6 Add `steepening_ratio: float = 2.0` for R019

## 3. Fix Existing Rules (R004, R005, R006, R013)

- [x] 3.1 Fix R004 (Vale): calculate position ratio as `indice_minimo_local / total_points` using `len(rates)`; remove hardcoded `max_day=756`, use actual `max(days)` from data (requires passing day list or n_points to the rule)
- [x] 3.2 Fix R005 (Pico): replace `longo.slope < 0` check with >=80% negative deltas after peak position (requires rates array access)
- [x] 3.3 Fix R006 (Recuperação Sustentada): use `np.diff(rates[indice_minimo_global:])` instead of segment-level deltas; check >=80% positive
- [x] 3.4 Fix R013 (Movimento Monótono): use `np.diff(rates)` from the entire curve instead of segment-level deltas; check monotonico_ratio of same-sign deltas
- [x] 3.5 Update R004, R005, R006, R013 function signatures to accept `np.ndarray` of raw rates (and day indices for R004) alongside `DetailedMetrics` and `AnalysisThresholds`

## 4. Make R010 Threshold Relative

- [x] 4.1 Update R010 (Curva Suave): compute `indice_suavidade_relativo = indice_suavidade / amplitude`; handle `amplitude == 0` (flat curve → suave by definition)
- [x] 4.2 Update R011 (Curva Serrilhada): adjust threshold reference to use the new relative logic (serrilhada if `indice_suavidade_relativo > suavidade_relativo * N` or similar; or keep using absolute `indice_suavidade` with `suavidade_serrilhado` threshold)
- [x] 4.3 Update all references from `suavidade_percentil` to `suavidade_relativo` in rules and facade

## 5. Add New Rules (R015–R020)

- [x] 5.1 Implement R015 (Oscilação Elevada): activate when `qtd_mudancas / n >= oscilacao_ratio`; inference `CURVA_OSCILANTE`, score -1, block `geometrica`
- [x] 5.2 Implement R016 (Amplitude Reduzida): activate when `amplitude < amplitude_reduzida`; inference `AMPLITUDE_REDUZIDA`, score 0, block `geometrica`
- [x] 5.3 Implement R017 (Amplitude Elevada): activate when `amplitude > amplitude_elevada`; inference `AMPLITUDE_ELEVADA`, score +1, block `geometrica`
- [x] 5.4 Implement R018 (Curva Invertida): activate when `curto.delta > delta_segmento_relevante` AND `longo.delta < -delta_segmento_relevante`; inference `CURVA_TORCIDA`, score +2, block `geometrica`
- [x] 5.5 Implement R019 (Achamento/Empinamento): achamento when `abs(curto.delta) > abs(longo.delta) * steepening_ratio` (same sign); empinamento when `abs(longo.delta) > abs(curto.delta) * steepening_ratio` (same sign); score +1, block `geometrica`
- [x] 5.6 Implement R020 (Formato-S): activate when `qtd_inflexoes >= 2`; inference `FORMATO_S`, score +1, block `geometrica`
- [x] 5.7 Export all new rule functions in `__init__.py`

## 6. Implement Dual Classification

- [x] 6.1 Determine trend direction in `analyze()` facade: track which of R001/R002/R003 activated
- [x] 6.2 Update `_classificar_score()` to accept `direction: str` parameter (`"asc"`, `"desc"`, or `"plana"`)
- [x] 6.3 Implement dual label table: 5 score ranges × 3 directions = 15 labels
- [x] 6.4 Update `score_label` assignation in `analyze()` to pass direction to classifier

## 7. Integrate into Rule Pipeline

- [x] 7.1 Add R015–R020 to the geometric rules list in `analyze()` facade
- [x] 7.2 Pass raw `rates` array (as `np.ndarray`) to rules that need it (R004, R005, R006, R013)
- [x] 7.3 Update the `RuleResult` construction in new rules to follow existing pattern

## 8. Update Tests

- [x] 8.1 Add test for `indice_minimo_global` in `TestDetailedMetrics`
- [x] 8.2 Update test for R004 (vale position ratio fix)
- [x] 8.3 Update test for R005 (sustained decline check)
- [x] 8.4 Update test for R006 (point-level deltas after minimum)
- [x] 8.5 Update test for R010 (relative threshold with amplitude normalization)
- [x] 8.6 Update test for R013 (point-level deltas across entire curve)
- [x] 8.7 Add tests for R015 (oscilação elevada)
- [x] 8.8 Add tests for R016 (amplitude reduzida)
- [x] 8.9 Add tests for R017 (amplitude elevada)
- [x] 8.10 Add tests for R018 (curva invertida)
- [x] 8.11 Add tests for R019 (achamento/empinamento)
- [x] 8.12 Add tests for R020 (formato-S)
- [x] 8.13 Add tests for dual classification: ascending, descending, and flat score labels
- [x] 8.14 Run full test suite and verify all tests pass

## 9. Verify with Real Data

- [x] 9.1 Run analysis on actual B3 SELIC Pré data and inspect report output
- [x] 9.2 Check that R004, R005, R006, R013 produce sensible results on real curves
- [x] 9.3 Validate that new rules R015–R020 activate appropriately on real data
- [x] 9.4 Calibrate thresholds if needed based on real data observations
