## 1. Core: consolidate_by_year function

- [x] 1.1 Implement `consolidate_by_year(records)` that groups by `day360 // 365` and computes min/max rate per group
- [x] 1.2 Add tests for `consolidate_by_year` with single-year and multi-year record sets

## 2. CLI: --yearly flag

- [x] 2.1 Add `--yearly` argument to argparse in `parse_args()`
- [x] 2.2 Implement `format_yearly_rows(consolidated)` that outputs `ANO,MENOR_TAXA,MAIOR_TAXA` CSV
- [x] 2.3 Wire `--yearly` in `main()` to call `consolidate_by_year` + `format_yearly_rows` instead of raw path
- [x] 2.4 Add tests for CLI `--yearly` output format

## 3. GUI: Consolidar por ano checkbox

- [x] 3.1 Add `ttk.Checkbutton` "Consolidar por ano" to the bottom frame (or top frame)
- [x] 3.2 Implement `render_consolidated()` that populates the Treeview with ANO/MENOR TAXA/MAIOR TAXA columns
- [x] 3.3 Wire checkbox state change to toggle between `render_records` and `render_consolidated`
- [x] 3.4 Ensure re-fetch respects checkbox state (re-render in active mode)
- [x] 3.5 Add GUI tests for checkbox toggle and view switching

## 4. Export/Copy respect active view

- [x] 4.1 Modify `copy_records` to detect checkbox state and format accordingly
- [x] 4.2 Modify `export_records` to detect checkbox state and format accordingly
- [x] 4.3 Add tests for copy/export in consolidated mode
