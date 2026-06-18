## 1. Core Engine: New rendering function

- [x] 1.1 Add `render_detailed_evolution(fig, date_rates)` function in `b3_selic_pre.py`: plots 5 gradient green lines on DU252 × TAXA, with legend and auto-scaled axes
- [x] 1.2 Write unit tests for `render_detailed_evolution` covering: 5-date rendering, empty date_rates, correct gradient/alpha/linewidth application
- [x] 1.3 Run existing tests to confirm no regressions

## 2. GUI: Replace radiobutton with checkbox

- [x] 2.1 Remove `self.view_evolution_rb` and the `"evolution"` value from `self.view_var` (line 551 — change to default `"raw"`)
- [x] 2.2 Add `self.evolution_var = tk.BooleanVar(value=False)` and a `ttk.Checkbutton` at the same layout position
- [x] 2.3 Implement `toggle_evolution(self)` method: auto-set date to today, first-check triggers `_fetch_historical_rates`, subsequent toggles only `_redraw_chart`
- [x] 2.4 Update `_redraw_chart(self)` to check `evolution_var` before `view_var`: detailed evolution or consolidated evolution depending on radio selection
- [x] 2.5 Simplify `toggle_view(self)` — remove evolution-specific logic (date setting, data check messages)
- [x] 2.6 Remove the `if view == "evolution"` special case from `fetch_rates(self)` (lines 709–715)
- [x] 2.7 Update `copy_data(self)` to use `evolution_var` instead of `view_var == "evolution"`
- [x] 2.8 Run existing tests to confirm no regressions

## 3. Version and changelog

- [x] 3.1 Bump `__version__` to `"0.5.0"` in `b3_selic_pre.py`
- [x] 3.2 Add `[0.5.0]` changelog entry documenting the radiobutton→checkbox change, detailed evolution rendering, lazy one-time fetch, and version bump
