## Context

Four chart rendering functions use `ax.grid(True, alpha=0.3)` which applies a uniform grid at major tick positions. The major ticks are at 20 DU intervals (raw/details charts) or 1-year intervals (consolidated charts). There is no visual distinction between monthly/quarterly or annual/triennial reference lines.

## Goals / Non-Goals

**Goals:**
- Add solid vertical grid lines at 90 DU intervals (quarterly) in raw and detailed-evolution charts
- Add solid vertical grid lines at 3-year intervals (triennial) in consolidated and consolidated-evolution charts
- Demote existing monthly/annual grid lines to dashed style with alpha=0.15
- No new dependencies

**Non-Goals:**
- No changes to chart data, colors, labels, or legends
- No behavioral requirements changes (purely visual rendering change)

## Decisions

### Decision 1: Minor ticks + split grid over axvline

**Decisão**: Use matplotlib's minor ticks mechanism instead of drawing explicit `ax.axvline` objects.

**Rationale**: Minor ticks integrate with the existing grid system — they draw behind data (correct z-order), don't create Line2D objects (preserving existing test assertions), and allow clean separation of prominent major (solid) and subtle minor (dashed) grid styles.

**Alternativa**: `ax.axvline` loops — rejected because they create Line2D objects that break `ax.get_lines()` count assertions in tests.

### Decision 2: 90 DU for quarterly, 3 years for triennial — swapped to major ticks

**Decisão**: Quarterly (90 DU) and triennial (3-year) marks are set as **major** ticks with solid grid (alpha=0.3). The monthly (20 DU) and annual (1-year) marks become **minor** ticks with dashed grid (alpha=0.15, linestyle="--"). Positions that overlap between the two sets are excluded from the minor set so both grid lines render independently.

**Rationale**: 
- 252 DU / year ÷ 4 ≈ 63 DU per quarter. 90 DU is used because B3's `EVOLUTION_DAYS` are multiples of 7 (7, 14, 21, 28), and 90 is the closest round number to a quarter that provides evenly spaced marks across the full 0–756 range.
- 3-year intervals match the `QUIVER_YEARS` key maturities (1, 2, 3, 5, 10, 15, 20) and provide ~7 marks across 0–20 years.
- Matplotlib does not create separate grid objects for minor ticks at positions that already have major ticks. Swapping hierarchy avoids overlapping positions entirely.

## Risks / Trade-offs

- **[90 DU ≠ exact quarter]** 90 DU is ~3.6 months, not exactly a calendar quarter. **Mitigation**: This is a reference grid, not a calendar. The approximation is close enough for visual orientation. An exact quarter would require calendar date mapping which adds complexity.
- **[Axis limits change if major ticks removed]** Swapping which ticks are major/minor changes `ax.get_xticks()` return value. **Mitigation**: Tests were updated to assert on the correct tick set (major or minor).
