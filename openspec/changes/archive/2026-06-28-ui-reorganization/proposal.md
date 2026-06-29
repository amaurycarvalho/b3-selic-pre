## Why

The current UI wastes vertical space with too many panel rows, uses text-based buttons that look dated, relies on a custom calendar popup instead of a native DateEntry widget, and duplicates the PNG export button already present in matplotlib's native toolbar. These changes modernize the interface and recover screen real estate for the chart.

## What Changes

- Replace `ttk.Entry` + calendar popup button + custom `DatePicker` class with `tkcalendar.DateEntry`
- Change label from "Data (YYYY-MM-DD):" to "Data de referência:"
- Replace button text with 24×24 icon images (Hoje → `document-open-recent`, Buscar → `view-refresh`, Copiar dados → `edit-copy`, Copiar gráfico → `edit-copy`)
- Show `content-loading` icon on fetch button during loading; move "Buscando…" text to the statusbar
- Move "Copiar dados" button to top_frame, to the right of "Buscar"
- Move "Copiar gráfico" button into matplotlib's `NavigationToolbar2Tk`
- **Remove** "Exportar PNG" button (redundant with native toolbar save button)
- Merge radiobuttons/checkboxes and stats summary into a single reduced-height row
- Display stats as a compact pipe-separated string on the right side of the radio/checkbox row
- Freeze window title to `B3 SELIC Pré v{version}` (remove dynamic title updates on data load)
- Add `tkcalendar` to project dependencies; update PyInstaller spec accordingly

## Capabilities

### New Capabilities

- `ui-refresh`: All visual and layout changes to the main GUI window — DateEntry widget, icon buttons, reorganized panels, frozen title, and toolbar integration

### Modified Capabilities

*(none — no prior specs exist)*

## Impact

- `src/b3_selic_pre/presentation/gui.py`: major layout and widget changes
- `src/b3_selic_pre/presentation/charts.py`: no changes expected
- `pyproject.toml`: add `tkcalendar` dependency
- `b3-selic-pre.spec`: add `tkcalendar` to hidden imports and datas
- `src/b3_selic_pre/presentation/settings.py`: no changes expected
- All 24×24 icons in `src/b3_selic_pre/icons/` will be loaded at runtime via `PhotoImage`
