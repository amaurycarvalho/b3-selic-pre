## 1. Core Rendering Function

- [x] 1.1 Add `from mpl_toolkits.mplot3d import Axes3D` import at the top of `b3_selic_pre.py`
- [x] 1.2 Implement `render_3d_evolution(fig, date_rates, consolidated=False)` that clears the figure, adds a 3D subplot, interpolates data onto a shared X grid, renders `plot_surface` with RdYlGn_r colormap, overlays 5 black lines with decreasing linewidth, sets axis labels, colorbar, and default camera angle (`view_init(elev=25, azim=-60)`)
- [x] 1.5 Apply X-axis limits: filter data to `day252 <= 756` (detailed) / `0 <= y <= 20` (consolidated) before meshgrid, call `ax.set_xlim`
- [x] 1.6 Add Y-axis upsampling (n×20 rows) before `plot_surface` for smooth gradient between curves
- [x] 1.7 Set Y-axis tick labels with date strings via `ax.set_yticks` / `ax.set_yticklabels`
- [x] 1.8 Add `fig.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)` to avoid tight_layout warnings on 3D axes
- [x] 1.9 Adjust 3D title position: measure text width and shift left by 70% via `t.set_x(0.5 - 0.7 * w_ax)`
- [x] 1.3 Implement helper `_interpolate_rates(records, common_x)` that extracts `day252` and `rate` from `RateRecord` list and returns interpolated values using `numpy.interp` with `left=np.nan, right=np.nan`
- [x] 1.4 Handle consolidated mode: use `average_rate_by_year()` output — years (0..N) are naturally aligned, no interpolation needed

## 2. GUI Integration

- [x] 2.1 Add `self.var_3d = tk.BooleanVar(value=False)` in `SelicPreApp.__init__`
- [x] 2.2 Add `ttk.Checkbutton` labeled "3D" next to "Evolução da curva" checkbox, bound to `self.var_3d`, disabled when evolution is OFF
- [x] 2.3 Bind 3D checkbox state to evolution variable so 3D auto-disables when evolution is unchecked
- [x] 2.4 Update `_redraw_chart()` dispatch: when evolution ON and 3D ON, call `render_3d_evolution(fig, historical_data, consolidated=(view=='consolidated'))`
- [x] 2.5 Set title appropriately for 3D view: "B3 SELIC Pré — Evolução 3D" (or "Detalhada" / "Consolidada" suffix based on view)
- [x] 2.6 Add `root.protocol("WM_DELETE_WINDOW", on_closing)` handler that calls `root.quit()` then `root.destroy()` to ensure process exits on window close

## 3. Build Configuration

- [x] 3.1 Add `'mpl_toolkits.mplot3d'` to `hiddenimports` in `b3-selic-pre.spec`

## 4. Tests

- [x] 4.1 Add test for `render_3d_evolution` with 5-date historical data (consolidated=False) — verify it calls `plot_surface` and returns without error
- [x] 4.2 Add test for `render_3d_evolution` with consolidated=True — verify yearly average rendering
- [x] 4.3 Add test for `_interpolate_rates` helper with mismatched X grids
- [x] 4.4 Add test for the `_redraw_chart` dispatch when 3D checkbox is toggled
- [x] 4.5 Add test for empty `date_rates` dict showing "Sem dados" placeholder
- [x] 4.6 Add test: 3D checkbox disabled when evolution is OFF (initial state)
- [x] 4.7 Add test: 3D checkbox enabled when evolution is ON with data loaded
- [x] 4.8 Add test: 3D checkbox disabled AND reset to False when evolution is turned OFF
