## 1. Core Rendering Function

- [ ] 1.1 Add `from mpl_toolkits.mplot3d import Axes3D` import at the top of `b3_selic_pre.py`
- [ ] 1.2 Implement `render_3d_evolution(fig, date_rates, consolidated=False)` that clears the figure, adds a 3D subplot, interpolates data onto a shared X grid, renders `plot_surface` with Viridis colormap, overlays 5 black lines with decreasing linewidth, sets axis labels, colorbar, and default camera angle (`view_init(elev=25, azim=-60)`)
- [ ] 1.3 Implement helper `_interpolate_rates(records, common_x)` that extracts `day252` and `rate` from `RateRecord` list and returns interpolated values using `numpy.interp` with `left=np.nan, right=np.nan`
- [ ] 1.4 Handle consolidated mode: use `average_rate_by_year()` output — years (0..N) are naturally aligned, no interpolation needed

## 2. GUI Integration

- [ ] 2.1 Add `self.var_3d = tk.BooleanVar(value=False)` in `SelicPreApp.__init__`
- [ ] 2.2 Add `ttk.Checkbutton` labeled "3D" next to "Evolução da curva" checkbox, bound to `self.var_3d`, disabled when evolution is OFF
- [ ] 2.3 Bind 3D checkbox state to evolution variable so 3D auto-disables when evolution is unchecked
- [ ] 2.4 Update `_redraw_chart()` dispatch: when evolution ON and 3D ON, call `render_3d_evolution(fig, historical_data, consolidated=(view=='consolidated'))`
- [ ] 2.5 Set title appropriately for 3D view: "B3 SELIC Pré — Evolução 3D" (or "Detalhada" / "Consolidada" suffix based on view)

## 3. Build Configuration

- [ ] 3.1 Add `'mpl_toolkits.mplot3d'` to `hiddenimports` in `b3-selic-pre.spec`

## 4. Tests

- [ ] 4.1 Add test for `render_3d_evolution` with 5-date historical data (consolidated=False) — verify it calls `plot_surface` and returns without error
- [ ] 4.2 Add test for `render_3d_evolution` with consolidated=True — verify yearly average rendering
- [ ] 4.3 Add test for `_interpolate_rates` helper with mismatched X grids
- [ ] 4.4 Add test for the `_redraw_chart` dispatch when 3D checkbox is toggled
- [ ] 4.5 Add test for empty `date_rates` dict showing "Sem dados" placeholder
