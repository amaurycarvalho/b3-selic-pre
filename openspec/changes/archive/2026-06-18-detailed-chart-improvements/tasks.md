## 1. X-axis label and grid marks (detailed chart functions)

- [x] 1.1 In `render_chart` raw path: change `ax.set_xlabel("DU252")` to `ax.set_xlabel("Dias úteis")`
- [x] 1.2 In `render_chart` raw path: change major ticks to nearest-match 66 DU (targets `range(66, 757, 66)`, tolerance 44)
- [x] 1.3 In `render_detailed_evolution`: change `ax.set_xlabel("DU252")` to `ax.set_xlabel("Dias úteis")` (both normal and empty-data paths)
- [x] 1.4 In `render_detailed_evolution`: change major ticks to nearest-match 66 DU (targets `range(66, 757, 66)`, tolerance 44), using only latest date's day252 values (not union across dates)
- [x] 1.5 Apply nearest-match to minor grid ticks (both functions): target every 22 DU (targets `range(1, 757, 22)`), tolerance 22, exclude major positions, using latest date's data in `render_detailed_evolution`
- [x] 1.6 Extract `_nearest_ticks` helper to eliminate code duplication
- [x] 1.7 Change data source for `render_detailed_evolution` grid/quiver from union of all dates to only the latest date's records

## 2. Quiver arrows (both evolution views)

- [x] 2.1 Add quiver loop in `render_detailed_evolution`: iterate over `minor_22du` positions, collect rates via nearest-match per date (tol 22), draw arrows with green gradient
- [x] 2.2 Remove unused `QUIVER_DU252` constant
- [x] 2.3 Add quiver loop in `render_curve_evolution`: iterate over `minor_1yr` positions, collect rates via nearest-match per date (tol 1), draw arrows with blue gradient
- [x] 2.4 Remove unused `QUIVER_YEARS` constant

## 3. Tests

- [x] 3.1 Update `test_render_detailed_evolution_xaxis_du252`: rename to `_xaxis_dias_uteis`, assert label is "Dias úteis"
- [x] 3.2 Update `test_render_detailed_evolution_has_90du_major_ticks`: rename to `has_66du_major_ticks`
- [x] 3.3 Update `test_render_chart_raw_has_90du_major_ticks`: rename to `has_66du_major_ticks`
- [x] 3.4 Add `test_render_detailed_evolution_has_quiver`: create test data with `day252=60` in both dates, assert quiver collections exist
- [x] 3.5 Run all tests and verify no regressions
- [x] 3.6 Update `test_render_chart_consolidated_has_3yr_major_ticks` data to span years 0-6 for nearest-match

## 4. Consolidated chart grid (non-evolution)

- [x] 4.1 Migrate `render_chart` consolidated path from exact `range(0, 21, 3)` to `_nearest_ticks` (major 3yr, minor 1yr, tol 1), matching all other render functions

## 5. Consolidated evolution grid

- [x] 5.1 Refactor `render_curve_evolution` to compute ticks via `_nearest_ticks` (major every 3 years, minor every 1 year, tol 1) using latest date's year values
- [x] 5.2 Replace `QUIVER_YEARS` curated positions with quiver at all `minor_1yr` positions
- [x] 5.3 Apply nearest-match per date lookup for quiver rates in consolidated evolution

## 6. Documentation updates

- [x] 6.1 Update `design.md` with all decision changes and renumbering
- [x] 6.2 Update `CHANGELOG.md` with consolidated evolution and consolidated chart changes
- [x] 6.3 Update `README.md` if necessary

## 7. Version bump

- [x] 5.1 Update `__version__` in `b3_selic_pre.py` from `"0.5.0"` to `"0.5.1"`
- [x] 5.2 Update `CFBundleShortVersionString` and `CFBundleVersion` in `b3-selic-pre.spec` from `"0.5.0"` to `"0.5.1"`
