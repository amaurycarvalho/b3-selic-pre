## Context

The quiver arrows in both evolution charts currently draw all 4 transition arrows at every tick position, clustering them in a narrow band that causes visual clash. The solution uses an offset/step pattern: each tick shows exactly one transition arrow, cycling through the 4 transitions + 1 gap.

## Goals / Non-Goals

**Goals:**
- Each tick shows exactly ONE transition arrow, cycling through transitions via `(tick_idx - 1) % 5`
- Curve evolution chart uses 1-year intervals (actual integer years from data)
- Detailed evolution chart uses existing 22 DU intervals
- Maintain existing color gradients and direction logic

**Non-Goals:**
- No change to minor grid line positions (remain at 1 year / 22 DU)
- No change to arrow styling (width, zorder, U component)

## Decisions

### Decision 1: Integer-year arrow positions (curve evolution)

Use `all_years` (integer years 0-20 from base date) for arrow placement. Rate lookup uses exact year match (`if year in yearly_rates`), avoiding the tolerance ambiguity issue that caused random arrow angles with half-year positions.

### Decision 2: Per-curve offset and step 5

Each transition arrow is assigned to a tick position by `(tick_idx - 1) % 5`:
- tick_idx % 5 == 1: T0→T1 (oldest curve, offset 1)
- tick_idx % 5 == 2: T1→T2 (offset 2)
- tick_idx % 5 == 3: T2→T3 (offset 3)
- tick_idx % 5 == 4: T3→T4 (offset 4)
- tick_idx % 5 == 0: no arrow (newest curve, no next transition)

This gives ~4 arrows per transition type across the 21-year range.

### Decision 3: Single arrow per tick

One quiver call per tick with single-element lists `[X]`, `[Y]`, `[U]`, `[V]`. Color indexed from the gradient array by transition index.

### Decision 4: Detailed evolution keeps 22 DU positions with same offset/step

The detailed evolution chart keeps existing 22 DU minor tick positions (~34 positions), applying the same `(tick_idx - 1) % 5` offset pattern. Rate lookup uses nearest-match within tolerance 22.

## Risks / Trade-offs

- [Reduced visibility per transition] Each transition type appears at ~4 positions instead of ~20. Mitigation: 4 data points per transition across the 0-20 year range are sufficient to show trend direction.
- [Ticks without arrows] Every 5th position has no arrow (tick_idx % 5 == 0 gaps). These are evenly distributed and do not impair readability.
