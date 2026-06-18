## Context

The current UI has three `ttk.Radiobutton` widgets — "Detalhado" (`"raw"`), "Consolidado" (`"consolidated"`), and "Evolução da curva" (`"evolution"`) — bound to `view_var`. They are mutually exclusive. Selecting "Evolução" forces the date to today and fetches 5 historical dates in parallel. The rendering uses `render_curve_evolution` (average-rate-per-year curves with quiver arrows) regardless of the underlying data granularity.

The user wants to decouple evolution from the base view, making it a checkbox overlay, and add a detailed evolution rendering (individual rate points per-date on DU252 × TAXA).

## Goals / Non-Goals

**Goals:**
- Convert "Evolução da curva" from `Radiobutton` to `Checkbutton` with `BooleanVar`
- Keep "Detalhado" and "Consolidado" as the only two radios in the view group (`view_var ∈ {"raw", "consolidated"}`)
- Provide two evolution renderings:
  - Detailed: 5 gradient lines on DU252 × TAXA (one per historical date)
  - Consolidated: existing 5-curve average-per-year chart with quiver arrows
- Evolution checkbox auto-fetches historical data on first check (date = today), caches in `self.historical_data`
- Subsequent toggles only switch display — no re-fetch
- "Copiar dados" follows evolution state: evolution ON → `format_evolution_csv`; OFF → base view CSV
- Bump version to `0.5.0` and update changelog

**Non-Goals:**
- No changes to the data-fetching functions (`fetch_historical_rates`, `fetch_rates_download`)
- No changes to the B3 API interaction layer
- No changes to CLI behavior
- No new external dependencies
- No animation or temporal slider

## Decisions

### Decision 1: Checkbutton replaces Radiobutton, two radios remain

**Decisão**: Remove `self.view_evolution_rb` (lines 629–633 in `b3_selic_pre.py`). Add `self.evolution_var = tk.BooleanVar(value=False)` and a `ttk.Checkbutton` at the same position. The two remaining radios (`self.view_raw_rb`, `self.view_consolidated_rb`) stay unchanged.

```
Layout antes:  ◉ Detalhado  ○ Consolidado  ○ Evolução da curva
Layout depois: ◉ Detalhado  ○ Consolidado   ☐ Evolução da curva
```

**Rationale**: Evolution is no longer a view mode — it's an overlay on top of the base view. Checkbox is the correct widget for an optional toggle that doesn't conflict with the base-mode selection.

### Decision 2: Detailed evolution renders 5 lines on DU252 × TAXA

**Decisão**: New function `render_detailed_evolution(fig, date_rates)` that:
- Iterates `sorted(date_rates.keys())` (5 dates)
- For each date, plots `r.day252` vs `float(r.rate.replace(",", "."))` using the existing `RateRecord` data
- Applies green gradient (`plt.cm.Greens`), alpha ramp (0.3→1.0), linewidth ramp (0.8→2.5) — same pattern as `render_curve_evolution` but with green color map and raw-rate points
- X-axis: DU252 (0–756), ticks every 20
- Legend showing each date label
- Title: "B3 SELIC Pré — Evolução Detalhada"

```python
def render_detailed_evolution(fig, date_rates):
    import numpy as np
    import matplotlib.pyplot as plt

    ax = fig.gca()
    ax.clear()

    if not date_rates:
        ax.text(0.5, 0.5, "Sem dados", ...)
        return

    dates_sorted = sorted(date_rates.keys())
    n = len(dates_sorted)
    colors = plt.cm.Greens(np.linspace(0.3, 0.9, n))
    alphas = np.linspace(0.3, 1.0, n)
    linewidths = np.linspace(0.8, 2.5, n)

    for i, date_str in enumerate(dates_sorted):
        records = date_rates[date_str]
        days = [r.day252 for r in records]
        rates = [float(r.rate.replace(",", ".")) for r in records]
        ax.plot(days, rates, color=colors[i], alpha=alphas[i],
                linewidth=linewidths[i], label=date_str)

    ax.set_xlabel("DU252")
    ax.set_xlim(0, 756)
    ax.set_xticks(range(1, 757, 20))
    ax.set_ylabel("TAXA (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
```

**Rationale**: Reuses existing data structures and follows the established gradient+alpha+linewidth pattern from `render_curve_evolution`. Green color map visually distinguishes from the consolidated evolution (blue).

### Decision 3: Evolution checkbox auto-fetches on first check

**Decisão**: `toggle_evolution(self)` method:
1. If checked (`evolution_var.get() == True`):
   - Set `date_var` to today
   - If `self.historical_data` is not None → just `_redraw_chart()` (no fetch)
   - If `self.historical_data` is None → call `self._fetch_historical_rates(today)` then `_redraw_chart()` on success
2. If unchecked → just `_redraw_chart()` (back to base view)

```python
def toggle_evolution(self):
    if self.evolution_var.get():
        today = date.today().isoformat()
        if self.date_var.get().strip() != today:
            self.date_var.set(today)
        if self.historical_data:
            self._redraw_chart()
        else:
            self._fetch_historical_rates(today)
    else:
        self._redraw_chart()
```

**Rationale**: The user explicitly chose "auto-buscar dados" over "mostrar mensagem". Fetch happens once per session, then toggles are instant.

### Decision 4: `_redraw_chart` checks evolution state first

**Decisão**: `_redraw_chart` evaluates evolution checkbox before the view variable:

```python
def _redraw_chart(self):
    show_evolution = self.evolution_var.get()
    view = self.view_var.get()

    if show_evolution and self.historical_data:
        if view == "consolidated":
            render_curve_evolution(self.figure, self.historical_data)
            title = "B3 SELIC Pré — Evolução Consolidada"
        else:
            render_detailed_evolution(self.figure, self.historical_data)
            title = "B3 SELIC Pré — Evolução Detalhada"
        self.figure.gca().set_title(title, fontsize=14, y=0.92)
    elif view == "consolidated":
        render_chart(self.figure, self.records, consolidated=True)
        self.figure.gca().set_title("B3 SELIC Pré — Consolidado", fontsize=14, y=0.92)
    else:
        render_chart(self.figure, self.records, consolidated=False)
        self.figure.gca().set_title("B3 SELIC Pré", fontsize=14, y=0.92)
    self.canvas.draw_idle()
```

**Rationale**: Evolution takes visual priority over the base view. The radio buttons determine which evolution rendering to show.

### Decision 5: `fetch_rates` simplified, evolution case removed

**Decisão**: Remove the `if self.view_var.get() == "evolution":` block (lines 709–715) from `fetch_rates`. The evolution fetch is now triggered exclusively by `toggle_evolution` when the checkbox is first checked.

**Rationale**: Evolution fetch responsibility moves from "Buscar" button to the checkbox toggle.

### Decision 6: Version bumped to 0.5.0

**Decisão**: `__version__ = "0.5.0"` in `b3_selic_pre.py`. New `[0.5.0]` section in `CHANGELOG.md`.

**Rationale**: The user chose to bump to 0.5.0 rather than add to the existing 0.4.0 entry, indicating this is significant enough for a minor version increment.

## Risks / Trade-offs

- **[Auto-fetch may surprise users]** First checkbox check triggers network requests (5 parallel fetches). **Mitigation**: Status bar shows "Buscando taxas históricas... (N/5 concluídas)" — same feedback as current evolution fetch.
- **[Green gradient confusion]** Detailed evolution uses green (same color as base detailed chart). **Mitigation**: Gradient range (light to dark) plus per-date legend makes temporal ordering clear.
- **[No evolution data for non-today dates]** Evolution always forces date to today. This is preserved from the current behavior — historical fetch only works with today as base.
- **[Radio switch while evolution is ON]** If evolution is ON and user clicks "Consolidado", the chart switches from detailed evolution to consolidated evolution. This is intentional but may surprise users who expect the radio to have no effect when evolution is ON. **Mitigation**: The visual change (green lines → blue curves) is distinct enough to be understood as "evolution of the consolidated view."
