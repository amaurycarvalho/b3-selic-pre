## Context

The app is a single-file Python/tkinter GUI (`b3_selic_pre.py`) that displays SELIC Pré interest rate curves from B3 data. It currently renders 2D line charts via matplotlib. The curve evolution view plots 5 historical curves (today, 7, 14, 21, 28 days ago) as superposed 2D lines with gradient coloring and quiver arrows. The user now wants an optional 3D surface visualization that stacks these curves along a Z axis to better perceive rate evolution over time.

The figure is embedded in tkinter via `FigureCanvasTkAgg`. All rendering functions receive a `matplotlib.figure.Figure` and redraw it in-place via `fig.clf()` + new subplot.

## Goals / Non-Goals

**Goals:**
- Add a "3D" checkbox in the GUI (next to "Evolução da curva") that toggles 3D surface rendering
- Implement `render_3d_evolution(fig, date_rates, consolidated=False)` using `plot_surface`
- Support both detailed (raw rate × business days) and consolidated (yearly average) data sources
- Overlay 5 individual curves as black lines on the surface with decreasing linewidth (today thickest, oldest thinnest)
- Use a unified colormap (viridis) where color represents rate magnitude
- Disable the 3D checkbox when evolution is OFF

**Non-Goals:**
- No changes to the 2D evolution rendering (unchanged when 3D is OFF)
- No changes to the data fetching or data model
- No interactive 3D controls beyond the standard matplotlib toolbar rotation
- No animation of the surface over time

## Decisions

### 1. plot_surface over plot_trisurf
**Decision**: `plot_surface` from `mpl_toolkits.mplot3d`.

**Rationale**: The 5 curves share a natural grid structure after interpolation (curves × X-axis points). `plot_surface` produces a clean rectangular mesh. `plot_trisurf` uses Delaunay triangulation which would create unpredictable triangle geometries with only 5 curves and may look messy.

### 2. Interpolation strategy for detailed view
**Decision**: Use `numpy.interp` to interpolate each curve onto a shared X grid.

For consolidated view, years (0..max_year) are naturally aligned — no interpolation needed.

For detailed view, each date has different `day252` values:
1. Determine the global X grid as `np.linspace(0, max_day252, num=200)` where `max_day252` is the maximum `day252` across all dates
2. For each curve, `np.interp(common_x, curve_days, curve_rates, left=np.nan, right=np.nan)` to fill missing values with NaN
3. `plot_surface` handles NaN cells gracefully by leaving holes

### 3. Colormap selection
**Decision**: Viridis colormap mapped to rate magnitude.

**Rationale**: Viridis is perceptually uniform, colorblind-friendly, and works well for continuous data. The color mapping reflects rate values directly on the surface, complementing the Z-axis height. Alternatives considered:
- **Plasma**: Warmer, also good, but less standard for financial data
- **YlOrRd**: Intuitive for rates (red=high) but not perceptually uniform
- **Blues/Greens**: Used by existing 2D views, but a unified colormap for 3D is clearer

### 4. Z-axis ordering
**Decision**: Today at Z=0 (front), 28 days ago at Z=4 (back).

The dates list is sorted ascending, then reversed so the most recent (today) is at the front of the 3D view. This presents the evolution naturally: the viewer sees the current curve first, with older curves receding into depth.

### 5. Line overlay styling
**Decision**: 5 black lines plotted via `ax.plot()` over the surface after `plot_surface`.

Linewidths decrease from today to oldest using `np.linspace(2.5, 0.8, 5)`. Black color ensures contrast against the colored surface. Lines are plotted in Z-order (from back to front) so the most recent line is visually on top.

### 6. UI integration
**Decision**: New `ttk.Checkbutton` labeled "3D" next to the existing "Evolução da curva" checkbox.

The 3D checkbox's `state` is bound to `evolution_var`: disabled when evolution is OFF, enabled when ON. This prevents rendering a 3D view without evolution data.

### 7. Figure / subplot management
**Decision**: Each render function clears the figure and creates appropriate subplot.

- 3D: `fig.add_subplot(111, projection='3d')`
- 2D: `fig.add_subplot(111)` (current behavior)

When switching between 2D and 3D, `fig.clf()` removes all axes before creating the new one. This is already the established pattern.

### 8. Default camera angle
**Decision**: `ax.view_init(elev=25, azim=-60)` for a balanced 3D perspective.

The elevation of 25° gives enough vertical relief to see rate variation, while -60° azimuth shows the depth separation between curves clearly.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| **Performance**: `plot_surface` with 200×5 grid and interpolation may be slow on low-end hardware | Grid size can be reduced to 100 points if needed. Interpolation is a one-time cost per render |
| **Visual clutter**: The surface + 5 lines + axes may look crowded | Lines are thin (0.8-2.5) and black for subtle overlay. The toolbar allows zoom/rotate to focus |
| **Data gaps**: Different dates have different max maturities, creating holes in the surface | NaN handling in `plot_surface` is well-behaved. The surface will naturally truncate at the shortest curve's max |
| **matplotlib 3D limitations**: The 3D renderer has known z-ordering issues (transparency artifacts) | Use `alpha=0.85` instead of full transparency. Plot lines AFTER the surface so they render on top |
| **PyInstaller build**: `mpl_toolkits.mplot3d` might need explicit hidden import | Update `.spec` file hiddenimports to include `mpl_toolkits.mplot3d` |
