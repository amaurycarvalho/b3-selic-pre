## 1. Settings Module

- [x] 1.1 Create `src/b3_selic_pre/presentation/settings.py` with XDG path resolution (Linux: `~/.config/b3-selic-pre/settings.json`, Windows: `%APPDATA%`, macOS: `~/Library/Application Support`)
- [x] 1.2 Implement `Settings` class with `read()`/`write()` methods using `json` + `pathlib`, with graceful fallback on missing/corrupt file or permission errors
- [x] 1.3 Integrate into `SelicPreApp.__init__`: load settings on startup, pre-fill `date_var`, `view_var`, `evolution_var`, `var_3d`, `sidebar_var`
- [x] 1.4 Save settings whenever user changes a preference (view toggle, evolution, 3D, sidebar, date changes) and on data load

## 2. Loading State & Progress Bars

- [x] 2.1 Refactor `set_loading()` into `_set_ui_locked(locked: bool)` that iterates a list of all interactive widgets to enable/disable
- [x] 2.2 Add `root.config(cursor="watch")` / `root.config(cursor="")` to `_set_ui_locked`
- [x] 2.3 Add indeterminate `ttk.Progressbar` to statusbar area; show during single fetch, hide after completion
- [x] 2.4 Add determinate `ttk.Progressbar`; connect to historical fetch progress callback, update value as steps complete
- [x] 2.5 Toggle "Buscar" button text to "Buscando…" in `_set_ui_locked(True)` and restore in `_set_ui_locked(False)`

## 3. Statusbar Enhancements

- [x] 3.1 Add Unicode icon prefix mapping to `_msg_colors` (info: "⏳", success: "✓", warning: "⚠", error: "✖")
- [x] 3.2 Update `set_status()` to prepend the icon before the message string
- [x] 3.3 Add data source indicator: store source type during fetch and display in statusbar after load
- [x] 3.4 Add last-update timestamp shown after successful data load

## 4. Layout Refinements

- [x] 4.1 Add `ttk.Separator` between `top_frame` and `middle_frame`
- [x] 4.2 Replace `middle_frame` grid layout with `ttk.PanedWindow(orient=HORIZONTAL)`, adding chart_frame as left pane and sidebar_frame as right pane
- [x] 4.3 Update `_toggle_sidebar` to use `pane.add()` / `pane.forget()` instead of `grid()` / `grid_forget()`

## 5. Input Enhancements

- [x] 5.1 Add custom `Error.TEntry` style with `fieldbackground="#ffe0e0"`; apply to date entry on validation error, revert on next successful validation
- [x] 5.2 Add placeholder behavior to date entry: show gray "AAAA-MM-DD" via focus-in/focus-out events; clear on focus, restore when empty and unfocused
- [x] 5.3 Add "Hoje" button next to the date entry that sets today's date and triggers fetch

## 6. Tooltips

- [x] 6.1 Implement `Tooltip` class using `tk.Toplevel(overrideredirect=True)` with `<Enter>`/`<Leave>` bindings and 500ms delay
- [x] 6.2 Add tooltips to all interactive widgets (buttons, radio buttons, checkboxes, date entry, calendar button)

## 7. Keyboard Shortcuts

- [x] 7.1 Bind `Ctrl+C` to `copy_data`
- [x] 7.2 Bind `Ctrl+Shift+C` to `copy_chart`
- [x] 7.3 Bind `Ctrl+S` to `export_chart`
- [x] 7.4 Bind `F5` to `fetch_rates`
- [x] 7.5 Bind `Ctrl+E` to toggle evolution checkbox
- [x] 7.6 Bind `Ctrl+L` to toggle analysis sidebar

## 8. Chart Enhancements

- [x] 8.1 Add quick stats `ttk.Frame` between top_frame and chart; show date, record count, highest/lowest rate, maturity count when data is loaded; hide when empty
- [x] 8.2 Update `render_chart` in `charts.py` to show "Nenhum dado carregado.\nInforme uma data e clique em Buscar." instead of "Sem dados"

## 9. Copy Confirm

- [x] 9.1 Save prior status text and foreground color before displaying copy confirmation
- [x] 9.2 Schedule `root.after(2000, restore)` to revert status text and foreground after 2 seconds

## 10. Window Title

- [x] 10.1 Update `root.title()` in `handle_fetch_success` to show date and record count
- [x] 10.2 Update `root.title()` in `handle_historical_fetch_success` to show date range and total records
- [x] 10.3 Revert `root.title()` to base version string on error or data clear

## 11. Analysis Panel

- [x] 11.1 Add `tag_configure` calls for bold headers, green/orange/red confidence values in the sidebar Text widget
- [x] 11.2 Update `_update_analysis` to insert text with tags (bold for section headers, colored for confidence and indicators)

## 12. Contextual Controls

- [x] 12.1 Extend `_update_button_states()` to also manage radio buttons ("Consolidado" disabled without data), checkboxes ("Análise" disabled without data), and evolution availability

## 13. Evolution Curve Visibility

- [x] 13.1 Adjust alpha range from `0.3→1.0` to `0.6→1.0` in both evolution renderers (`render_curve_evolution`, `render_detailed_evolution`)
- [x] 13.2 Adjust linewidth range from `0.8→2.5` to `1.5→2.5` for better visibility
- [x] 13.3 Keep quiver width at original `0.004` (no marker or linestyle changes)

## 14. Auto-Trigger Evolution on Buscar/Hoje

- [x] 14.1 In `fetch_rates()`, invalidate `self.historical_data = None` when evolution checkbox is on
- [x] 14.2 In `handle_fetch_success()`, detect `evolution_var` + `not historical_data` + records and auto-call `_fetch_historical_rates()`
- [x] 14.3 Add `_historical_fetching` guard flag to prevent duplicate fetches
- [x] 14.4 Skip `_set_ui_locked(False)` in `handle_fetch_success` when historical fetch follows; lock transitions from indeterminate to determinate bar smoothly

## 15. Weekend and Date Validation

- [x] 15.1 Add `_nearest_business_day()` helper: steps back from Saturday/Sunday to Friday
- [x] 15.2 Apply weekend adjustment in `fetch_rates()` and `toggle_evolution()`
- [x] 15.3 Add future date rejection (`parsed > date.today()`) in `fetch_rates()` with error message

## 16. Window Geometry Persistence

- [x] 16.1 Save `window_geometry` and `window_maximized` to Settings
- [x] 16.2 On first run: default `1100x660` + screen-center via `_center_window()`
- [x] 16.3 On subsequent runs: restore geometry and maximized state
- [x] 16.4 Bind `<Configure>` with 500ms debounce to save position/size
- [x] 16.5 Save final state on `WM_DELETE_WINDOW` close

## 17. Stats Frame Layout Stability

- [x] 17.1 Keep stats_frame always packed in layout (no `pack_forget`/`pack` toggle)
- [x] 17.2 Start with empty label text `""`; `_update_stats()` only updates text
- [x] 17.3 Increase default window height to `660px` to accommodate all widgets

## 18. Initial Control Enable State

- [x] 18.1 Add `view_raw_rb` and `evolution_cb` to `_update_button_states()` — start disabled, enabled after data load

## 19. Progress Bar Cleanup

- [x] 19.1 Add `_indeterminate_bar.stop()` before `pack_forget()` in `_set_ui_locked()` locked branch to prevent orphan animation

## 20. Update Tests

- [x] 20.1 Update `tests/test_b3_selic_pre_gui.py` to pass with new widgets and behavior
