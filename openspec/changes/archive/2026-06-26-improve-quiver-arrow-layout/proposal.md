## Why

The quiver arrows in both evolution charts are stacked with a fixed horizontal offset (t * 0.06) at each tick position, causing visual overlap and clutter between the 4 consecutive transition arrows. This makes it difficult to distinguish rate change direction between consecutive curve pairs at the same maturity.

## What Changes

- Redesign quiver arrow placement to show at most one arrow per tick position, cycling through curve transitions by offset (offset 1, step 5)
- Apply the new layout to both `render_curve_evolution` (1-year intervals) and `render_detailed_evolution` (22 DU intervals)
- Maintain existing arrow colors (Blues/Greens gradient), direction logic (V = rate difference), width, and zorder

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `curve-evolution`: Quiver arrow layout changes — one arrow per year, cycling through transitions by offset (offset 1, step 5), using exact year match for rate lookup
- `curve-evolution-detailed`: Same offset/step arrow layout applied to the detailed evolution chart (22 DU tick positions)

## Impact

- `b3_selic_pre.py`: Quiver X-offset computation in `render_curve_evolution` (line 349) and `render_detailed_evolution` (line 417)
- Existing spec scenarios for quiver arrows need delta spec updates
