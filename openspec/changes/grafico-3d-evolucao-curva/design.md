## Context

The app is a single-file Python/tkinter GUI (`b3_selic_pre.py`) that displays SELIC Pré interest rate curves from B3 data. It currently renders 2D line charts via matplotlib. The curve evolution view plots 5 historical curves (today, 7, 14, 21, 28 days ago) as superposed 2D lines with gradient coloring and quiver arrows. The user now wants an optional 3D surface visualization that stacks these curves along a Z axis to better perceive rate evolution over time.

The figure is embedded in tkinter via `FigureCanvasTkAgg`. All rendering functions receive a `matplotlib.figure.Figure` and redraw it in-place via `fig.clf()` + new subplot.

## Goals / Non-Goals

**Goals:**
- Add a "3D" checkbox in the GUI (next to "Evolução da curva") that toggles 3D surface rendering
- Implement `render_3d_evolution(fig, date_rates, consolidated=False)` using `plot_surface`
- Support both detailed (raw rate × business days) and consolidated (yearly average) data sources
- Overlay 5 individual curves as black lines on the surface with decreasing linewidth (today thickest, oldest thinnest)
- Use a unified colormap (RdYlGn_r) where color represents rate magnitude (green=low, red=high)
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
1. Filter records to `day252 <= 756` to match the 2D detailed view's X-axis limit
2. Determine the global X grid as `np.linspace(0, max_day252_filtered, num=200)` where `max_day252_filtered` is the maximum `day252` across all dates after filtering
3. For each curve, `np.interp(common_x, curve_days, curve_rates, left=np.nan, right=np.nan)` to fill missing values with NaN
4. `plot_surface` handles NaN cells gracefully by leaving holes
5. Set `ax.set_xlim(0, 756)` for consistency with the 2D detailed view

### 3. Colormap selection
**Decision**: RdYlGn_r (reversed Red-Yellow-Green) colormap mapped to rate magnitude.

**Rationale**: RdYlGn_r is a diverging colormap where green=low rates, yellow=mid, red=high rates. This is intuitive for financial data — it mirrors the familiar heatmap convention (red = high = caution, green = low = safe). The reversed variant ensures green is at the low end of the scale. Alternatives considered:
- **Viridis**: Perceptually uniform and colorblind-friendly, but less intuitive for rate visualization
- **YlOrRd**: Sequential yellow-to-red, but lacks a low-rate visual cue (green)
- **Blues/Greens**: Used by existing 2D views, but a diverging colormap better emphasizes rate extremes

### 4. Z-axis ordering
**Decision**: Today at Z=0 (front), 28 days ago at Z=4 (back).

The dates list is sorted ascending, then reversed so the most recent (today) is at the front of the 3D view. This presents the evolution naturally: the viewer sees the current curve first, with older curves receding into depth.

### 5. Line overlay styling
**Decision**: 5 black lines plotted via `ax.plot()` over the surface after `plot_surface`.

Linewidths decrease from today to oldest using `(n - 1 - i) * 0.425 + 0.8` (produces `[2.5, 2.075, 1.65, 1.225, 0.8]` for n=5). Black color ensures contrast against the colored surface. Lines are plotted with `alpha=0.7` for a subtle overlay. Lines are plotted in Z-order (from back to front) so the most recent line is visually on top.

### 6. UI integration
**Decision**: New `ttk.Checkbutton` labeled "3D" next to the existing "Evolução da curva" checkbox.

The 3D checkbox's `state` is bound to `evolution_var`: disabled when evolution is OFF, enabled when ON. This prevents rendering a 3D view without evolution data.

### 7. Figure / subplot management
**Decision**: Each render function clears the figure and creates appropriate subplot.

- 3D: `fig.add_subplot(111, projection='3d')`
- 2D: `fig.add_subplot(111)` (current behavior)

When switching between 2D and 3D, `fig.clf()` removes all axes before creating the new one. This is already the established pattern.

### 8. Consolidated mode year filtering
**Decision**: Filter years to 0–20 and set `ax.set_xlim(0, 20)`.

**Rationale**: The consolidated 2D view (`render_curve_evolution`) limits the X-axis to 0–20 years. The 3D view filters data to the same range before generating the meshgrid, preventing `plot_surface` from extending beyond the intended X range. `set_xlim` is also set as a view-level safeguard but data is pre-filtered because matplotlib 3D surface clipping is inconsistent.

### 9. Smooth surface gradient via Y-axis upsampling
**Decision**: Interpolate the grid to `n × 20` rows along the Y (Período) axis before passing to `plot_surface`.

**Rationale**: `plot_surface` assigns one color per face (average of 4 corner Z values). With only n=5 curves, each face spans a large Y distance, producing a single blended color between curves. By upsampling to 100 rows (n×20), adjacent faces differ slightly in color, creating a smooth gradient from one curve's color to the next. Linear interpolation (`numpy.interp`) along each X column preserves the original curve values exactly.

### 10. Title position adjustment for 3D views
**Decision**: After rendering, shift the title left by 70% of its own width using a two-pass render-and-measure approach.

**Rationale**: The 3D chart's colorbar occupies ~20% of the figure width, making a center-aligned title (default `x=0.5`) appear too far right. Measuring the rendered text's actual pixel width and shifting `x = 0.5 - 0.7 * w_ax` compensates for the asymmetry, centering the title visually over the chart area rather than the full figure.

### 11. Default camera angle
**Decision**: `ax.view_init(elev=25, azim=-60)` for a balanced 3D perspective.

The elevation of 25° gives enough vertical relief to see rate variation, while -60° azimuth shows the depth separation between curves clearly.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| **Performance**: `plot_surface` with 200×(n×20) grid and interpolation may be slow on low-end hardware | Grid size can be reduced to 100 X-points or fewer Y-upsample steps if needed. Interpolation is a one-time cost per render |
| **Visual clutter**: The surface + 5 lines + axes may look crowded | Lines are thin (0.8-2.5) and black for subtle overlay. The toolbar allows zoom/rotate to focus |
| **Data gaps**: Different dates have different max maturities, creating holes in the surface | NaN handling in `plot_surface` is well-behaved. The surface will naturally truncate at the shortest curve's max |
| **matplotlib 3D limitations**: The 3D renderer has known z-ordering issues (transparency artifacts) | Use `alpha=0.85` instead of full transparency. Plot lines AFTER the surface so they render on top |
| **PyInstaller build**: `mpl_toolkits.mplot3d` might need explicit hidden import | Update `.spec` file hiddenimports to include `mpl_toolkits.mplot3d` |
