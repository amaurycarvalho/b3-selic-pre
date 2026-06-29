## Context

The GUI (`SelicPreApp` in `gui.py`, ~780 lines) uses pure tkinter/ttk with embedded matplotlib. The current layout is 5 horizontal bands (top frame, stats, chart pane, bottom frame with buttons + radiobuttons/checkboxes, statusbar). This design reorganizes the layout to 4 bands, replacing several widgets with more modern alternatives.

All icons are 24×24 PNGs in `src/b3_selic_pre/icons/`. The project is packaged via PyInstaller (`b3-selic-pre.spec`).

## Goals / Non-Goals

**Goals:**
- Replace custom DatePicker with `tkcalendar.DateEntry` (dropdown calendar)
- Replace text buttons with icon-only buttons
- Move "Copiar dados" to top row, "Copiar gráfico" into matplotlib toolbar, remove "Exportar PNG"
- Merge stats and radiobuttons/checkboxes into one row with compact pipe-separated stats
- Freeze window title
- Keep all existing functionality (copy, fetch, analysis, evolution, 3D, etc.)
- Maintain PyInstaller build compatibility

**Non-Goals:**
- No changes to chart rendering logic (`charts.py`)
- No changes to data fetching or analysis logic
- No changes to the CLI
- No changes to settings persistence

## Decisions

### 1. tkcalendar.DateEntry over custom DatePicker
**Choice**: Replace `ttk.Entry` + `📅` button + `DatePicker` class with `tkcalendar.DateEntry`.
- Eliminates ~70 lines of custom calendar code
- Provides native dropdown calendar UX
- Handles date validation and locale natively
- **Trade-off**: New dependency `tkcalendar` must be added to `pyproject.toml` and included in PyInstaller spec (`hiddenimports`, `datas`)

### 2. Icon loading strategy
**Choice**: Load all icons in `__init__` and store as `self.icons` dict, keyed by button name.
```python
self.icons = {}
for name in ['document-open-recent', 'view-refresh', 'edit-copy', 'content-loading']:
    path = resources.files('b3_selic_pre') / 'icons' / f'{name}.png'
    self.icons[name] = tk.PhotoImage(file=str(path))
```
- 24×24 PNGs → no resizing needed
- Reference kept on `self` to prevent garbage collection

### 3. Buscar loading state
**Choice**: Swap icon from `view-refresh` to `content-loading` during fetch. Remove text change on button; write "Buscando…" to statusbar instead.
- `_set_ui_locked()`: `self.fetch_button.configure(image=self.icons['content-loading'])`
- On unlock: restore `view-refresh` icon
- Statusbar already distinguishes message types; "Buscando…" fits naturally

### 4. Custom button in matplotlib toolbar
**Choice**: After creating `NavigationToolbar2Tk`, add a `ttk.Button` directly into the toolbar frame.
```python
self.toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
self.copy_toolbar_btn = ttk.Button(
    self.toolbar, image=self.icons['edit-copy'],
    command=self.copy_chart,
)
self.copy_toolbar_btn.pack(side=tk.LEFT, padx=(2, 0))
```
- Simple, no subclassing needed
- `toolbar` is a `tk.Frame` packed `side=BOTTOM, fill=X` — adding a `ttk.Button` with `side=LEFT` places it after native buttons
- Tooltip added via existing `Tooltip` system

### 5. Layout reorganization
**Choice**: Eliminate `bottom_frame`, create `middle_frame` between `top_frame` and chart pane.
- `middle_frame` packs radiobuttons/checkboxes on the LEFT and stats on the RIGHT
- Stats rendered as a single `StringVar` label with pipe-separated format: `"Data: 2026-06-28 | 42 reg | 13,25% | 12,50% | 5 venc"`
- `middle_frame` padding reduced to `(12, 4)` for compact height

```
middle_frame flow:
  LEFT: [Detalhado] [Consolidado] [Evolução] [3D] [Análise]
  RIGHT: [Data: X | Reg: Y | Maior: Z | Menor: W | Venc: V]
```

### 6. Frozen window title
**Choice**: Set title once in `__init__`. Remove all runtime `root.title()` calls in `handle_fetch_success`, `handle_historical_fetch_success`, and `handle_fetch_error`.

### 7. _lockable_widgets update
The `_lockable_widgets` list must be updated to reflect removed/moved widgets (remove `export_button`, keep `data_button` reference even though moved to top_frame).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| tkcalendar not available on all platforms (Linux/Win/macOS) | tkcalendar is pure-Python + tkinter; works cross-platform. Pin version. |
| PyInstaller build fails if tkcalendar not explicitly included | Add to `hiddenimports` and ensure `datas` in spec file |
| Icons may not render in PyInstaller frozen build | Use `resources.files()` (already works for `b3_selic_pre.png`); icons dir is already in `package-data` |
| matplotlib toolbar styling (tk.Frame) vs ttk button visual mismatch | Accept minor visual difference. Can switch to `tk.Button` if needed. |
| Removing "Exportar PNG" may confuse users accustomed to it | Native toolbar save button provides same functionality; "Copiar gráfico" now in toolbar as well |
