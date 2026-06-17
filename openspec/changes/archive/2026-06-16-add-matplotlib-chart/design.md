## Context

The application fetches SELIC Pré reference rates from B3 and currently displays them in a tkinter Treeview table. Users cannot visually identify trends, yield curve shapes, or rate envelopes across maturities. A matplotlib-based line chart embedded in the tkinter window replaces the table, adding visual analysis without changing the data pipeline or CLI behavior.

The existing data flow is: B3 API → fetch → RateRecord[] → (raw or consolidated) → display. The chart simply replaces the final display step.

## Goals / Non-Goals

**Goals:**
- Embed a matplotlib line chart in the tkinter GUI replacing the Treeview table
- Raw mode: green line (TAXA × DU252, 20-day X-ticks at 1, 21, 41...)
- Consolidated mode: blue (menor_taxa) + red (maior_taxa) lines (year X-axis)
- Matplotlib NavigationToolbar2Tk for zoom/pan
- "Copiar gráfico" button → clipboard via platform-specific tools (xclip/osascript/ctypes)
- "Exportar PNG" button → file-save dialog → `fig.savefig()`
- Toggle "Consolidar por ano" switches chart mode without re-fetch

**Non-Goals:**
- No tabular display in GUI (CLI still provides CSV)
- No time-series animation or real-time updates
- No multi-selection or clickable data points beyond zoom/pan
- No web-based visualization

## Decisions

### Decision 1: matplotlib embed via FigureCanvasTkAgg

**Choice**: `matplotlib.backends.backend_tkagg.FigureCanvasTkAgg` + `NavigationToolbar2Tk`

**Rationale**: Direct tkinter embedding, zero extra dependencies beyond matplotlib itself. `FigureCanvasTkAgg` renders the figure into a tkinter Canvas widget and supports `copy_figure()` for clipboard.

**Alternatives considered**:
- **tkinter Canvas from scratch**: Too much reimplementation for axes, ticks, zoom
- **Pillow drawing on Canvas**: No interactivity
- **plotly + webview**: Heavy dependency, overkill for static yield curve

### Decision 2: Chart replaces table (no coexistence)

**Choice**: The chart fills the area previously occupied by the Treeview. No tab switching.

**Rationale**: Simpler UI, fewer widgets, matches user preference. Tabular data remains accessible via CLI and existing CSV export.

**Trade-off**: Users lose row-level inspection in GUI. Mitigated by keeping CSV export/copy.

### Decision 3: Interactivity via matplotlib toolbar

**Choice**: Embed the standard `NavigationToolbar2Tk` (zoom, pan, home, save).

**Rationale**: Minimal implementation effort, provides essential zoom/pan without custom widget code. The built-in save button is kept but a dedicated "Exportar PNG" button is also added with file dialog for better UX.

### Decision 4: Clipboard copy via platform-specific tools

**Choice**: Use platform-native clipboard mechanisms for image data:
- **Linux**: `xclip` pipes PNG data to X11 clipboard with `image/png` target
- **macOS**: `osascript` writes PNG temp file to clipboard via AppleScript
- **Windows**: `ctypes` + Win32 API allocates DIB memory handle and calls `SetClipboardData(CF_DIB)`

**Rationale**: matplotlib's `canvas.copy_figure()` is unreliable across platforms. PIL/Pillow is used for PNG→BMP conversion on Windows.

**Dependencies**: `Pillow` (image conversion). Platform tools: `xclip` (Linux), `osascript` (macOS, built-in).

### Decision 5: Separate chart rendering function

**Choice**: Isolate chart creation in a `render_chart(fig, records, consolidated=False)` function.

**Rationale**: Keeps GUI code decoupled from chart logic. Easy to test rendering without tkinter. Easy to extend with new chart types.

### Decision 6: Ignore partial years in consolidated chart

**Choice**: Display all years as-is, including partial first/last years. Use integer year labels (0, 1, 2, ...).

**Rationale**: User stated "não se importar com anos parciais." Years are computed as `day360 // 365` which may produce partial bands at edges. No special handling.

### Decision 7: Buttons disabled (grayed out) when no data

**Choice**: Copy and Export buttons use `state=tk.DISABLED` when `self.records` is empty, and are re-enabled after a successful fetch. No status message is shown on click since the button is already inactive.

**Rationale**: Clearer UX than allowing clicks and showing a message. `_update_button_states()` is called in `__init__`, `handle_fetch_success`, and `handle_fetch_error`.

### Decision 8: X-axis limits and tick scales

**Choice**: Fixed X-axis ranges with explicit tick locators:
- **Raw mode**: X-axis from 0 to 756 (DU252), ticks at `[1, 21, 41, ..., 741]` (step 20)
- **Consolidated mode**: X-axis from 0 to 20 (years), ticks at `[0, 1, 2, ..., 20]` (step 1)

**Rationale**: Fixed limits ensure consistent visual frame regardless of data length. The 756 cap (~3 business years) matches typical yield curve relevance; 20-year cap covers the full B3 data range.

### Decision 9: Y-axis auto-scale (reverted)

**Choice**: Removed `ax.set_ylim(bottom=0)`. Y-axis uses matplotlib default auto-scale based on data range.

**Rationale**: Anchoring at zero compressed the rate variation visual (e.g., 14.0%-14.5% became a flat line near the top). Auto-scale better reveals curve shape and rate movements.

## Risks / Trade-offs

- **[Dependency weight]** matplotlib and Pillow add ~15MB to the deployment. **Mitigation**: All are well-established libraries; the project now documents its external dependencies explicitly in `requirements.txt`.
- **[Clipboard fragility]** Clipboard image copy has inconsistent support across OS. **Mitigation**: Platform-specific approaches with try/except fallback chain; fallback message "Use Exportar PNG para salvar o gráfico."
- **[Resize behavior]** tkinter geometry management with embedded matplotlib canvas can be finicky. **Mitigation**: Use `pack(fill=BOTH, expand=True)`; `FigureCanvasTkAgg` handles redraw natively.
- **[Test complexity]** Chart rendering tests require matplotlib with non-interactive backend. **Mitigation**: Test the `render_chart()` function with `matplotlib.use('Agg')`; validate that axes have expected lines and labels rather than pixel-matching.
