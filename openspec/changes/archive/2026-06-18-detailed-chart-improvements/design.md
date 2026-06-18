## Context

The detailed chart (`render_chart` raw path and `render_detailed_evolution`) currently uses "DU252" as the x-axis label, which is technical jargon. The quarterly grid marks are at 90 DU intervals (~4.5 months), but 60 DU (~3 months, ~60 business days) is more intuitive as a "quarter" reference. The detailed evolution view lacks the quiver arrows that the consolidated evolution view has, creating an inconsistency.

## Goals / Non-Goals

**Goals:**
- Replace x-axis label "DU252" with "Dias úteis" in both detailed rendering functions
- Change quarterly (major) grid marks from 90 DU to ~66 DU intervals (nearest-match)
- Change minor grid marks from ~20 DU to ~22 DU intervals (nearest-match)
- Add quiver arrows at minor tick positions in both evolution views (`render_detailed_evolution` and `render_curve_evolution`)
- Apply `_nearest_ticks` pattern to consolidated evolution for consistent grid/quiver behavior
- Update existing tests and documentation

**Non-Goals:**
- No changes to data fetching or processing
- No new dependencies
- No changes to the GUI layout or interaction

## Version management

Three files must have their version bumped on each release:

| File | Field |
|------|-------|
| `b3_selic_pre.py` | `__version__` (line ~17) |
| `b3-selic-pre.spec` | `CFBundleShortVersionString` and `CFBundleVersion` (lines ~74-75) |
| `CHANGELOG.md` | New `## [version]` section with release date |

Without updating all three, the version string in the GUI title bar (`B3 SELIC Pré v{__version__}`), the macOS `.app` bundle metadata, and the changelog will be inconsistent.

## Decisions

### Decision 1: 66 DU as the new quarterly interval (revised from 60 DU)

**Decisão**: Change major grid marks from `range(90, 757, 90)` to `range(66, 757, 66)` with nearest-match tolerance 44.

**Rationale**: 66 business days (~3 × 22 business days) approximates a calendar quarter more accurately than 90 DU (4.5 months) or 60 DU (~2.7 months). The 0–756 range yields up to 11 targets (66, 132, ..., 726). With tolerance 44 (2/3 of interval), nearest-match maps each target to the closest real data point (e.g., 63←66, 126←132, 189←198, 252←264, 336←330, 378←396, 504←462, 630←594, 756←726).

**Revised from**: The original specification used 60 DU interval (tolerance 40). After implementation, the interval was adjusted to 66 DU for a more accurate quarter approximation.

### Decision 2: Quiver arrows at minor tick positions (not major quarterly)

**Decisão**: Draw quiver arrows at the same positions as the minor grid ticks (nearest-match at ~22 DU / ~1 year intervals), not at major quarterly positions.

**Rationale**: The quiver arrows show rate direction at the finest grid granularity. In the detailed evolution, minor ticks at 22 DU (≈ monthly) capture short-end movements at 1, 21, 42 DU that major 66-DU ticks would miss. In the consolidated evolution, minor ticks every 1 year provide dense directional information. Using minor positions for both the dashed grid lines and the arrows ensures visual alignment between grid marks and directional indicators.

**Revised from**: The original specification placed quiver arrows at fixed 60-DU quarterly targets. This was iteratively refined: first to nearest-match 60 DU, then to minor 22 DU positions with nearest-match per date for the detailed view, and finally applied to the consolidated view using minor 1-year positions with the same nearest-match per date lookup.

### Decision 3: Direct rate lookup instead of averaging

**Decisão**: For each DU252 position, look up the exact rate from each date's records rather than averaging.

**Rationale**: In the detailed chart, each DU252 position has a single rate value per date (no min/max consolidation). A dict lookup `{r.day252: float(r.rate.replace(",", ".")) for r in records}` is sufficient. This differs from the consolidated version which uses `average_rate_by_year` because the consolidated data has multiple records per year that need averaging.

### Decision 4: Nearest-match for minor (dashed) grid ticks

**Decisão**: Apply the same nearest-match logic to minor grid ticks: target every 22 DU from 1 to 756, tolerance 22, excluding positions already used by major ticks.

**Rationale**: 22 business days approximates a calendar month. Using `_nearest_ticks(all_days, range(1, 757, 22), 22, set(major_66du))` maps each target to the closest actual day252 value within 22 DU and deduplicates against major positions. With realistic B3 maturities, this produces dashed lines at the short-end positions 1, 21, and 42.

### Decision 5: Shared `_nearest_ticks` helper function

**Decisão**: Extract the nearest-match logic into a reusable function `_nearest_ticks(all_values, targets, tolerance, exclude_set=None)` used by both `render_chart` and `render_detailed_evolution` for both major and minor grids.

**Rationale**: The same pattern (find nearest data point to each target within tolerance, deduplicate) was replicated across both major and minor ticks in two different functions. A single helper ensures consistent behavior and eliminates code duplication.

### Decision 6: Single-date data basis for grid and quiver (not union across dates)

**Decisão**: In `render_detailed_evolution`, use only the latest date's day252 values (`date_rates[dates_sorted[-1]]`) for computing grid ticks and quiver positions, instead of the union across all historical dates.

**Rationale**: Different historical dates may return different sets of maturities (due to `fetch_rates_download` vs `fetch_reference_rates` differences or B3 API pagination with `page_size=100`). The union across dates creates a superset that causes nearest-match to pick different positions than `render_chart` (which uses a single date). Using only the latest date (typically today) guarantees both charts produce identical grid ticks.

### Decision 7: `_nearest_ticks` in all render functions (including consolidated chart)

**Decisão**: Apply `_nearest_ticks` grid computation to all four render functions: `render_chart` raw, `render_chart` consolidated, `render_detailed_evolution`, and `render_curve_evolution`. The consolidated evolution additionally uses minor-position quiver arrows and a single-date data basis.

**Rationale**: The `render_chart` consolidated path was the last holdout using exact `range(0, 21, 3)` / `range(0, 21)` ticks. Migrating it to `_nearest_ticks` with tolerance 1 ensures all four functions share the same helper, producing consistent behavior. Though consolidated data always has integer years (making exact and nearest-match identical in practice), the migration eliminates a special case and future-proofs against non-integer year values.

**Changes**: All four render functions now use `_nearest_ticks` for major and minor grid computation; `QUIVER_YEARS` and `QUIVER_DU252` constants removed.

### Decision 8: Nearest-match per date for quiver rate lookup

**Decisão**: For each quiver arrow position, find the nearest data point within tolerance in each date's own dataset, rather than doing an exact `dict.get(pos)` lookup.

**Rationale**: Different historical dates may have slightly different maturity sets (e.g., one date has day252=21 while another has 20 or 22). An exact lookup returns `None` for dates without the exact position, reducing arrow density or producing gaps. Finding the nearest data point within tolerance (22 DU for detailed, 1 year for consolidated) ensures each date contributes a meaningful rate, producing longer arrow chains with consistent direction information.

## Risks / Trade-offs

- **[Test data mismatch]** The existing `_make_date_rates` test helper uses limited year coverage (0-1). **Mitigation**: Updated the consolidated evolution test (`test_render_curve_evolution_has_3yr_major_ticks`) to use separate data spanning years 0-6.
- **[Real B3 maturities ≠ multiples of 22]** B3 standard maturities (1, 7, 14, 21, 28, 42, 63, ...) are not exact multiples of 22. **Mitigation**: Nearest-match within 22 DU tolerance maps each minor target to the closest available data point.
- **[Few arrows at short end]** With real B3 data, only 3 minor positions exist (1, 21, 42). **Mitigation**: This is expected — the short end is where rates fluctuate most, making 3 directional arrows informative without cluttering the chart.
- **[Different maturities across dates]** Historical dates may return different maturity sets (download vs API, pagination). **Mitigation**: Use only the latest date's data for grid computation; use nearest-match per date for quiver lookups.
