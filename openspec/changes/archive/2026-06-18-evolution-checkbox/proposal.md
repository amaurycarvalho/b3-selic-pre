## Why

The current "Evolução da curva" is a radiobutton mutually exclusive with "Detalhado" and "Consolidado", forcing users to lose their base view to see evolution. Making it a checkbox decouples the two concerns — users can toggle evolution on/off while keeping their preferred base view (detailed or consolidated), and the evolution data is fetched once and cached for the session.

## What Changes

- **Radiobutton → Checkbox**: "Evolução da curva" becomes a standalone `ttk.Checkbutton` independent from the two-view radiobutton group ("Detalhado", "Consolidado")
- **Detailed evolution chart**: New `render_detailed_evolution(fig, date_rates)` function plots 5 lines on DU252 × TAXA with gradient coloring (one curve per historical date), complementing the existing consolidated evolution
- **Lazy one-time fetch**: First check of the evolution checkbox auto-triggers `fetch_historical_rates()` (date = today) without requiring the user to click "Buscar"; subsequent toggles only switch the display
- **Two evolution renderings**: Radio "Detalhado" + evolution ON → detailed evolution; Radio "Consolidado" + evolution ON → consolidated evolution (existing quiver chart)
- **Copiar dados follows view**: Evolution ON copies evolution CSV; OFF copies base view data
- **Version bump**: `__version__` → `"0.5.0"`
- **BREAKING**: `view_var` values drop `"evolution"` — now only `"raw"` / `"consolidated"`

## Capabilities

### New Capabilities
- `curve-evolution-detailed`: renders 5 overlay lines (one per historical date) on DU252 × TAXA with gradient coloring, legend, and auto-scaled axes

### Modified Capabilities
- `desktop-rate-browser`: chart toggle mechanism changes from 3 mutually exclusive radios to 2 radios + 1 checkbox; evolution fetch becomes auto-triggered by checkbox; copy-data follows evolution state
- `curve-evolution`: adds `render_detailed_evolution` as an alternative rendering path alongside the existing consolidated evolution

## Impact

- `b3_selic_pre.py`: `__version__`, new function `render_detailed_evolution`, `SelicPreApp` constructor (remove evolution RB, add Checkbutton + `evolution_var`), `toggle_view` simplified, new `toggle_evolution`, `_redraw_chart` logic, `fetch_rates` simplified, `copy_data` updated
- `CHANGELOG.md`: new `[0.5.0]` section
- `openspec/specs/desktop-rate-browser/spec.md`: delta spec updates for toggle behavior
- `openspec/specs/curve-evolution/spec.md`: delta spec for detailed evolution rendering
