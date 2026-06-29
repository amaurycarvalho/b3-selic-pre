## 1. Dependencies and Icon Loading

- [x] 1.1 Add `tkcalendar` to `pyproject.toml` dependencies
- [x] 1.2 Add `tkcalendar` to `b3-selic-pre.spec` hidden imports and datas
- [x] 1.3 Add icon loading block in `SelicPreApp.__init__` — load `document-open-recent`, `view-refresh`, `edit-copy`, `content-loading` as `tk.PhotoImage` stored in `self.icons` dict

## 2. DateEntry Widget

- [x] 2.1 Replace `ttk.Entry` (date_entry), `📅` button (cal_button), and `_open_calendar` with `tkcalendar.DateEntry` in top_frame
- [x] 2.2 Remove `DatePicker` class (lines 74–144)
- [x] 2.3 Remove `cal_button` from `_lockable_widgets` and `_setup_tooltips`
- [x] 2.4 Remove `_setup_date_placeholder` and its call — no longer needed with DateEntry
- [x] 2.5 Change label text from "Data (YYYY-MM-DD):" to "Data de referência:"
- [x] 2.6 Bind `<Return>` on DateEntry to `fetch_rates` (if not default behavior)
- [x] 2.7 Remove `cal_button` from tooltips dict

## 3. Icon Buttons and Layout Reorganization

- [x] 3.1 Replace `today_button` text "Hoje" → icon `document-open-recent`, resize button
- [x] 3.2 Replace `fetch_button` text "Buscar" → icon `view-refresh`, resize button
- [x] 3.3 Move `data_button` ("Copiar dados") from bottom_frame to top_frame, positioned after fetch_button; replace text with icon `edit-copy`
- [x] 3.4 Add Tooltips for all icon buttons
- [x] 3.5 Update `_set_ui_locked` to swap fetch_button icon between `view-refresh` and `content-loading`; remove `configure(text=...)` calls for fetch_button
- [x] 3.6 Move "Buscando…" status message to statusbar in `_set_ui_locked`
- [x] 3.7 Adjust top_frame packing and padding to accommodate moved/added buttons

## 4. Middle Row (Radiobuttons + Checkboxes + Stats)

- [x] 4.1 Create `middle_frame` between top_frame separator and chart pane, with reduced vertical padding
- [x] 4.2 Pack radiobuttons and checkboxes on LEFT side of middle_frame (same order as before: Detalhado, Consolidado, Evolução, 3D, Análise)
- [x] 4.3 Create a single `ttk.Label` for stats on RIGHT side of middle_frame, with anchor `tk.E`
- [x] 4.4 Update `_update_stats` to render pipe-separated compact string: `f"Data: {date} | {n} reg | {maior:.2f}% | {menor:.2f}% | {venc} venc"`
- [x] 4.5 Remove `stats_frame` and its individual label dict (replaced by middle_frame stats label)
- [x] 4.6 Remove `bottom_frame` and all its remaining children

## 5. Matplotlib Toolbar Integration

- [x] 5.1 After creating `NavigationToolbar2Tk`, pack a `ttk.Button` with `edit-copy` icon into the toolbar frame
- [x] 5.2 Wire button to `self.copy_chart` method
- [x] 5.3 Add Tooltip: "Copia o gráfico como imagem"

## 6. Remove Exportar PNG Button

- [x] 6.1 Remove `export_button` creation and packing from bottom_frame
- [x] 6.2 Remove `export_button` from `_lockable_widgets`, `_update_button_states`, and `_setup_tooltips`
- [x] 6.3 Remove `export_chart` method (lines 754–767) — or keep as internal utility but unbind `Control-s`
- [x] 6.4 Remove `Control-s` binding from `_setup_shortcuts`

## 7. Freeze Window Title

- [x] 7.1 Remove `root.title()` call from `handle_fetch_success` (line 673–674)
- [x] 7.2 Remove `root.title()` call from `handle_historical_fetch_success` (line 695–696)
- [x] 7.3 Remove `root.title()` call from `handle_fetch_error` (line 707)
- [x] 7.4 Keep only the initial `root.title(f"B3 SELIC Pré v{__version__}")` in `__init__`

## 8. Cleanup and Verification

- [x] 8.1 Update `_lockable_widgets` list to reflect all changes (remove export_button, cal_button; keep data_button in new position)
- [x] 8.2 Update `_setup_tooltips` and `_setup_shortcuts` as needed
- [x] 8.3 Remove unused imports (`DatePicker` class no longer needed — check if `from calendar import monthcalendar, month_name` is still referenced)
- [x] 8.4 Run tests: `python -m pytest tests/` (160/160 passed)
- [x] 8.5 Launch GUI and verify all changes visually (requires display)
