## Why

The application is functionally complete but lacks UI polish expected from professional financial tools. Feedback during loading is minimal, controls remain active during operations, and there is no keyboard workflow, persistence, or visual feedback differentiation beyond basic text. These 26 refinements raise perceived quality to match desktop analytical tools without adding external dependencies or altering the visual identity.

## What Changes

- Block all controls during loading and show wait cursor
- Add determinate/indeterminate progress bars to the statusbar
- Prefix status messages with Unicode icons per severity
- Highlight date entry in red on validation failure
- Toggle "Buscar" button text to "Buscando…" during fetch
- Add placeholder text to date entry
- Add "Hoje" button to reset date to today
- Add tooltips to all interactive controls
- Update window title with loaded data context
- Show data source and last update time in statusbar
- Persist last used date and user preferences to XDG config file
- Add keyboard shortcuts (Ctrl+C, Ctrl+Shift+C, Ctrl+S, F5, Esc, Ctrl+E, Ctrl+L)
- Improve export feedback with full file path
- Show quick statistics row above chart
- Show placeholder text on empty chart ("Nenhum dado carregado")
- Temporarily show confirm message on copy then revert to prior status
- Add ttk.Separator between top/middle/bottom layout sections
- Replace fixed-width sidebar with ttk.PanedWindow for resizable analysis panel
- Add headers and rich-text formatting to analysis panel
- Automatically disable/enable controls based on available data context
- No breaking changes, no new external dependencies

## Capabilities

### New Capabilities
- `loading-state`: Wait cursor, full UI lock, and progress bars (determinate for historical, indeterminate for single fetch)
- `statusbar-enhancements`: Unicode severity icons, data source label, last-update timestamp
- `input-enhancements`: Date validation highlight, placeholder text, "Hoje" reset button
- `buscar-cancel`: Toggle button text to "Buscando…" during fetch
- `tooltips`: Contextual tooltips on all interactive widgets
- `keyboard-shortcuts`: Ctrl+C, Ctrl+Shift+C, Ctrl+S, F5, Ctrl+E, Ctrl+L
- `persistence`: XDG-compliant settings file for last date and user preferences
- `window-title`: Dynamic title with date and record count
- `chart-enhancements`: Quick stats row, empty-state placeholder, chart-update status feedback
- `analysis-panel`: Section headers, rich-text formatting, PanedWindow resizable layout
- `copy-confirm`: Temporary confirmation message with automatic revert to prior status
- `layout-separators`: ttk.Separator between top/middle/bottom window sections
- `contextual-controls`: Dynamic enable/disable of controls based on available data

### Modified Capabilities
<!-- No existing specs to modify — all capabilities are new additions to the GUI layer. -->

## Impact

- **Target**: Release 0.8.0
- **Primary file**: `src/b3_selic_pre/presentation/gui.py` — significant changes to `__init__`, `set_loading`, `set_status`, `fetch_rates`, `_update_button_states`, `copy_data`, `copy_chart`, `export_chart`, and the sidebar layout
- **Supporting files**: New `settings.py` for XDG persistence; `charts.py` for quick stats and empty-state placeholder
- **Tests**: `tests/test_b3_selic_pre_gui.py` — updates for new widgets and behavior
- **Dependencies**: Zero new external dependencies (tkinter native widgets only, stdlib `json`+`pathlib` for persistence)
