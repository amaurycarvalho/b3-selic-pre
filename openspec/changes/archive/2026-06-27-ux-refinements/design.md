## Context

The GUI currently provides minimal feedback during network operations (only the "Buscar" button is disabled), no keyboard workflow, no persistence, and no visual differentiation beyond plain text. The previous change (`add-statusbar-feedback`) introduced a dedicated statusbar area with color-coded messages. This change builds on that foundation with 26 refinements across the entire interface.

The project uses only standard `tkinter`/`ttk` and matplotlib. No new dependencies are allowed.

## Goals / Non-Goals

**Goals:**
- Complete UI lock and wait cursor during all network operations
- Determinate progress bar for historical fetch, indeterminate for single fetch
- Unicode severity icons in status messages (⏳ ✓ ⚠ ✖)
- Visual date validation feedback (red highlight on invalid input)
- Tooltips on all interactive widgets
- Keyboard shortcuts for common operations
- XDG-compliant persistence of last date and user preferences
- Dynamic window title reflecting loaded data
- Quick statistics row above the chart
- Rich-text analysis panel with section headers and color-coded values
- Resizable sidebar via ttk.PanedWindow
- Contextual enable/disable of all controls based on available data

**Non-Goals:**
- No auto-clear for status messages (copy-confirm uses timed revert instead)
- No animation or transition effects
- No icon/bitmap additions (Unicode only)
- No external dependencies or theme changes

## Decisions

1. **Single `_set_ui_locked()` method** for all loading-state toggling, instead of scattered `config(state=...)` calls. Centralizes the list of widgets to lock/unlock, sets cursor, and manages progress bar visibility. The existing `set_loading()` is refactored to delegate to this method.

2. **Two progress bars in statusbar**: an indeterminate `ttk.Progressbar` (visible during single fetch) and a determinate one (visible during historical fetch with callbacks updating the value). Only one is shown at a time.

3. **Custom ttk.Style for error state** on the date entry, rather than creating a separate `tk.Entry` or using `tkinter.messagebox`. A temporary style `Error.TEntry` with `fieldbackground="#ffe0e0"` is applied on validation failure and reverted after correction.

4. **Tooltip as a utility class** rather than inline bindings. A `Tooltip` class wrapping `tk.Toplevel(overrideredirect=True)` with `<Enter>`/`<Leave>` bindings and configurable delay. Standard approach used in many tkinter applications.

5. **Root-level bindings** for keyboard shortcuts, with `<Control-c>`, `<Control-s>` etc. bound on `self.root`. Need to avoid conflicts with the matplotlib `NavigationToolbar2Tk` bindings (which use the same keys). The tkinter event system gives priority to focused widget bindings over root bindings, so matplotlib's entry fields capture their own keys first.

6. **Settings via `platformdirs`-style** manual implementation (no dependency). Use `pathlib.Path` + `json`:
   - Linux: `~/.config/b3-selic-pre/settings.json`
   - Windows: `%APPDATA%/b3-selic-pre/settings.json`
   - macOS: `~/Library/Application Support/b3-selic-pre/settings.json`
   A single `settings.py` module handles read/write with a dict interface.

7. **PanedWindow replaces the grid layout** in `middle_frame`. The chart is the left pane, the sidebar is the right pane. When sidebar is hidden, the chart pane occupies the full width. This changes `_toggle_sidebar` from `grid`/`grid_forget` to `add`/`forget` on the PanedWindow.

8. **Analysis panel formatting** uses a `Text` widget with pre-configured `tag_configure` calls for bold headers, colored values, and section separators. The `_update_analysis` method inserts text with tags instead of plain insertion.

9. **Copy confirmation** saves the previous status text and color before showing the copy message, then schedules a `root.after(2000, restore)` callback to revert. Queued restore is cancelled on any subsequent `set_status()` call.

10. **Quick stats** as a single-line `ttk.Frame` with `ttk.Label` widgets for record count, highest/lowest rate, and maturity count. The frame is **always packed** in the layout (between top separator and pane) — no `pack_forget`/`pack` toggle. When no data is loaded, labels show empty text (`""`). `_update_stats()` only updates label text, preventing re-layout issues that could clip the statusbar.

11. **Window geometry persistence and centering**: On first run (no `window_geometry` in settings), the window defaults to `1100x660` and is centered via `_center_window()` (screen center calculation in a `root.after(10, ...)` callback, executed after the window is mapped). On subsequent runs, `window_geometry` and `window_maximized` are restored. A `<Configure>` handler with 500ms debounce saves geometry changes. Final state is also saved on `WM_DELETE_WINDOW`.

12. **Automatic historical fetch on Buscar/Hoje**: When the evolution checkbox is on, `fetch_rates()` invalidates `self.historical_data = None`. `handle_fetch_success()` detects `evolution_var=True` + `historical_data=None` and automatically triggers `_fetch_historical_rates()` — no manual checkbox toggle needed. A `_historical_fetching` guard flag prevents duplicate fetch calls. The UI stays locked (transitions from indeterminate to determinate progress bar) through the full sequence.

13. **Weekend handling**: `_nearest_business_day()` steps back from Saturday/Sunday (`weekday() >= 5`) to the preceding Friday. Applied in both `fetch_rates()` and `toggle_evolution()`. Prevents the B3 API from returning identical weekend data for all EVOLUTION_DAYS, which caused overlapping curves.

14. **Future date validation**: `fetch_rates()` rejects dates after today with an `"Data futura"` error message.

15. **Evolution curve rendering**: Alpha range adjusted from `0.3→1.0` to `0.6→1.0`, linewidth from `0.8→2.5` to `1.5→2.5` — ensuring older curves are visible even when rates are close. No markers or linestyle changes. Quiver width kept at original `0.004`.

16. **Initial control state**: "Detalhado" radio button and "Evolução da curva" checkbox start disabled (consistent with other controls), enabled only after data is loaded via `_update_button_states()`.

## Risks / Trade-offs

- **Risk**: PanedWindow changes `middle_frame` layout, potentially breaking the chart sizing. → Mitigation: Test with and without sidebar, with various data loads.
- **Risk**: Keyboard shortcuts may conflict with the matplotlib toolbar's built-in bindings (e.g., Ctrl+C for copy). → Mitigation: Use root-level bindings; matplotlib's bindings fire on figure-level; tkinter's event propagation ensures root-level bindings don't fire when the matplotlib toolbar has focus.
- **Trade-off**: Copy confirm's 2-second timer means the message disappears even if the user hasn't read it. Acceptable for transient feedback.
- **Risk**: Persistence module might not have write permission in the XDG directory. → Mitigation: Gracefully fall back to in-memory settings if write fails; no crash.
- **Trade-off**: All widgets use the same Tooltip class with a fixed 500ms delay. Could be made configurable, but overengineering for now.
- **Risk**: Weekend adjustment to Friday may skip Thursday data if Friday is a holiday. → Mitigation: Acceptable for a desktop tool; B3 holidays are rare enough that manual date entry handles it.
- **Trade-off**: Stats frame always takes ~16px vertical space even when empty. → Acceptable — window height is 660px, and avoids re-layout clipping of the statusbar.
