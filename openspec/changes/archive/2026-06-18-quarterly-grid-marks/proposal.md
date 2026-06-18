## Why

The current charts have a uniform grid with no temporal reference marks, making it hard to visually align data points with calendar quarters (detailed chart) or multi-year periods (consolidated chart). Adding minor grid lines at 90-DU (quarterly) and 3-year intervals provides quick visual orientation without cluttering the chart.

## What Changes

- **Detailed chart (raw + detailed evolution)**: add minor vertical grid lines every 90 DUs (business days ≈ 1 quarter) with dashed style and reduced alpha
- **Consolidated chart (consolidated + consolidated evolution)**: add minor vertical grid lines every 3 years with dashed style and reduced alpha
- **Grid refactored**: split `ax.grid(True, alpha=0.3)` into separate major/minor grid calls to support different styles per tier

## Capabilities

### New Capabilities
*(none — purely visual change, no new behavioral capability)*

### Modified Capabilities
*(none — no spec-level behavior changes, only rendering implementation)*

## Impact

- `b3_selic_pre.py`: 4 rendering functions (`render_chart` raw path, `render_chart` consolidated path, `render_curve_evolution`, `render_detailed_evolution`) — each gets minor tick configuration and split grid calls
- No new dependencies, no API changes, no CLI changes
- No breaking changes
