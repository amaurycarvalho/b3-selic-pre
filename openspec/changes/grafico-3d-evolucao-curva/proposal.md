## Why

The current curve evolution view shows 5 superposed 2D line charts. While functional, it doesn't convey the temporal progression intuitively — the human eye struggles to separate overlapping lines and perceive the rate trajectory across time. A 3D surface visualization stacks the curves along a time axis (Z) and connects adjacent curves with a colored surface, making the evolution immediately visible as a 3D topography of interest rates over time.

## What Changes

- Add a "3D" checkbox alongside the existing "Evolução da curva" checkbox in the GUI (disabled when evolution is OFF)
- When evolution is ON and 3D is ON, render the 5 curves as a 3D surface plot using `plot_surface` instead of the standard 2D line chart
- The 3D view works with both "Detalhado" and "Consolidado" radio states — raw rate data or yearly averages
- Each curve occupies a distinct Z position (today=0, 28d ago=4)
- The 5 individual curves are drawn as black lines overlaid on the surface, with decreasing linewidth (today thickest, oldest thinnest)
- Surface uses a unified colormap (e.g., viridis) where color represents rate magnitude
- Requires `mpl_toolkits.mplot3d` for 3D projection support
- Existing 2D evolution views remain unchanged when 3D is OFF

## Capabilities

### New Capabilities
- `curve-evolution-3d`: 3D surface rendering of curve evolution data, with stacked curves along Z axis, surface interpolation between adjacent curves, and unified colormap by rate magnitude

### Modified Capabilities
- `curve-evolution`: Consolidated evolution view now has an alternative 3D rendering path using yearly averaged data
- `curve-evolution-detailed`: Detailed evolution view now has an alternative 3D rendering path using raw rate data

## Impact

- **File modified**: `b3_selic_pre.py` (single-file app) — new rendering function, modified `_redraw_chart` dispatch, new GUI widgets
- **New dependency**: `mpl_toolkits.mplot3d` (ships with matplotlib, no pip install needed)
- **Test file**: `tests/test_b3_selic_pre.py` — new tests for 3D rendering function
- **Build spec**: `b3-selic-pre.spec` — may need hidden import for `mpl_toolkits.mplot3d`
- **No API changes**: no new endpoints, no data model changes
