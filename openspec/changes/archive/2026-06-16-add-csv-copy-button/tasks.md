## 1. GUI: Add button and handler

- [x] 1.1 Add `copy_button` widget to `bottom_frame` before the existing `copy_chart` button, labeled "Copiar dados"
- [x] 1.2 Add `copy_button` to `_update_button_states()` so it's disabled when no data loaded
- [x] 1.3 Implement `copy_data()` method: generate CSV via `format_cli_rows()` or `format_yearly_rows()` depending on `self.consolidate_var`, copy to clipboard via `self.root.clipboard_clear()` + `self.root.clipboard_append()`, display status `Dados copiados para a área de transferência.`

## 2. Tests

- [x] 2.1 Test that `copy_button` exists and is disabled when no data
- [x] 2.2 Test that `copy_button` is enabled after data is loaded
- [x] 2.3 Test that `copy_button` is disabled after error clears data
- [x] 2.4 Test raw mode CSV copy produces correct columns and data
- [x] 2.5 Test consolidated mode CSV copy produces correct columns and data
