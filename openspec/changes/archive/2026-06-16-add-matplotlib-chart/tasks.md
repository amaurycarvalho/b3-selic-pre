## 1. Dependency & Project Setup

- [x] 1.1 Add `matplotlib` to project dependencies (create `requirements.txt` or document installation instructions)
- [x] 1.2 Install matplotlib and verify import works in the project environment

## 2. Chart Rendering Core

- [x] 2.1 Create `render_chart(fig, records, consolidated=False)` function that draws a raw (green line, DC365 × TAXA) or consolidated (blue/red lines, year × min/max) chart
- [x] 2.2 Apply 30-day tick interval on DC365 X-axis for raw mode and integer year labels for consolidated mode
- [x] 2.3 Apply auto Y-axis scaling with reasonable margins for both modes

## 3. GUI Integration

- [x] 3.1 Replace Treeview import and instantiation with `matplotlib.backends.backend_tkagg.FigureCanvasTkAgg`
- [x] 3.2 Embed `NavigationToolbar2Tk` for zoom/pan interactivity
- [x] 3.3 Wire "Consolidar por ano" checkbox to re-render chart (raw ↔ consolidated) without re-fetching data
- [x] 3.4 Handle empty results: show "Sem dados" message on chart area instead of rendering
- [x] 3.5 Preserve consolidation toggle state across data fetches
- [x] 3.6 Handle window resize to re-draw chart canvas

## 4. Export & Copy

- [x] 4.1 Add "Exportar PNG" button with file-save dialog that calls `fig.savefig()`
- [x] 4.2 Add "Copiar gráfico" button that copies chart image to clipboard (xclip on Linux, fallback message)
- [x] 4.3 Disable export/copy buttons when no data is loaded and show informational message

## 5. Cleanup & Edge Cases

- [x] 5.1 Remove Treeview and its scrollbar from the layout (table no longer exists in GUI)
- [x] 5.2 Remove "Copiar tabela" and "Exportar CSV" buttons (replaced by chart export/copy)
- [x] 5.3 Remove old export/copy handlers (`copy_records`, `export_records`) from `SelicPreApp`

## 6. Tests

- [x] 6.1 Update existing GUI tests: remove tests that reference Treeview, add tests for chart rendering in both modes
- [x] 6.2 Test clipboard copy and PNG export with mock data
- [x] 6.3 Test empty-data state shows message and disables buttons
- [x] 6.4 Test consolidation toggle toggles chart mode correctly
- [x] 6.5 Run full test suite to confirm no regressions in CLI path
