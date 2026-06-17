## Why

Users need a way to copy the raw numerical data behind the chart to the clipboard as CSV, for use in spreadsheets or other analysis tools — the current workflow requires re-querying the CLI or manually transcribing values.

## What Changes

- Add a "Copiar dados" button to the GUI bottom bar, positioned before the existing "Copiar gráfico" button
- When clicked, generate CSV matching the current view mode (raw or consolidated) and copy it to the system clipboard
- Use the same column naming conventions as the CLI output: `DU252,DC365,TAXA` for raw mode and `ANO,MENOR_TAXA,MAIOR_TAXA` for consolidated mode
- Respect existing button enable/disable pattern (disabled when no data loaded)
- No file-save dialog — clipboard-only, matching the existing "Copiar gráfico" pattern

## Capabilities

### New Capabilities
- `data-export`: Copy current view data as CSV to the system clipboard

### Modified Capabilities
- (none)

## Impact

- **Code**: `b3_selic_pre.py` — add a button widget and one handler method in `SelicPreApp`
- **Specs**: `yearly-consolidation/spec.md` already has requirements for CSV copy in consolidated mode; these may need alignment
- **Dependencies**: None (uses tkinter's built-in clipboard API)
