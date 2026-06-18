## Why

The detailed chart (DU252 × TAXA) has usability gaps: the x-axis label "DU252" is not intuitive for non-specialist users, the quarterly grid marks at 90 DU (~4.5 months) don't align with a natural calendar quarter (~60 business days), and the detailed evolution view lacks quiver arrows showing rate direction — a feature already present in the consolidated evolution view.

## What Changes

- **X-axis label**: Change from "DU252" to "Dias úteis" in both the raw detailed chart and the detailed evolution chart
- **Grid marks**: Change quarterly (major) grid marks from every 90 DU to every 60 DU, which better approximates a calendar quarter in business days
- **Quiver arrows in detailed evolution**: Add quiver arrows at each quarterly position (60, 120, ..., 720) showing rate change direction between historical curves, matching the consolidated evolution behavior
- **Documentation**: Update CHANGELOG.md, README.md, and existing spec files to reflect the new behavior

## Capabilities

### New Capabilities

None — all changes modify existing capabilities.

### Modified Capabilities

- `line-chart`: X-axis tick mark scenario in raw mode — change from 20-day intervals to 60-DU quarterly major ticks with 20-DU minor grid
- `curve-evolution-detailed`: X-axis label, tick marks, and addition of quiver arrow requirement

## Impact

- `b3_selic_pre.py`: `render_chart` raw path and `render_detailed_evolution` — x-axis label text, grid range constants, and new quiver loop
- `tests/test_b3_selic_pre.py`: Update existing tick/label assertions, add quiver test
- `openspec/specs/line-chart/spec.md`: Update raw mode X-axis scenario
- `openspec/specs/curve-evolution-detailed/spec.md`: Update X-axis scenario, add quiver scenario
- `CHANGELOG.md`: New [0.5.1] section
- `README.md`: Update detailed mode description
