## Why

The current GUI displays SELIC Pré rates as a tabular list (Treeview), which is ineffective for spotting trends and patterns across maturities. A line chart reveals the shape of the yield curve at a glance — both in raw form (rate vs. days) and in yearly-consolidated form (min/max envelope over time).

## What Changes

- Add matplotlib as a project dependency
- Replace the Treeview table with a matplotlib line chart embedded in the tkinter window
- Chart renders raw data as a green line (TAXA × DC365) when consolidation is off
- Chart renders consolidated data as two lines (menor_taxa in blue, maior_taxa in red) when consolidation is on
- Add "Exportar PNG" button to save the chart image to disk
- Add "Copiar gráfico" button to copy the chart image to the system clipboard
- Provide basic interactivity: zoom/pan via matplotlib toolbar
- Remove the Treeview table; tabular data remains accessible via CLI (`--yearly` and export)
- Keep existing CLI behavior unchanged

## Capabilities

### New Capabilities
- `line-chart`: Interactive line chart for SELIC Pré rates, supporting raw and yearly-consolidated views, with PNG export and clipboard copy.

### Modified Capabilities
- `desktop-rate-browser`: Replace tabular display with chart display; add chart export/copy operations.
- `yearly-consolidation`: Visualize consolidated data as a dual-line chart instead of a table.

## Impact

- New dependency: `matplotlib` (added to project requirements)
- Core module `b3_selic_pre.py`: significant GUI refactor — replace Treeview with chart; add export/copy image buttons; integrate matplotlib toolbar
- CLI path: unchanged
- Tests: update GUI tests (table no longer exists); add chart rendering tests
