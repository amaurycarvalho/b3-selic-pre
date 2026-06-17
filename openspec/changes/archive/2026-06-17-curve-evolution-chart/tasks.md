## 1. Core Data Functions

- [x] 1.1 Implement `average_rate_by_year(records)` that returns `dict[int, float]` mapping year to average rate (midpoint of min_rate and max_rate from `consolidate_by_year`)
- [x] 1.2 Write unit tests for `average_rate_by_year` covering single year, multiple years, edge cases (empty list, single record)

## 2. Historical Fetch via GetDownloadFile

- [x] 2.1 Create `_days_ago(base_date: str, days: int)` helper that subtracts N calendar days from a date string (replaces `_weeks_ago`)
- [x] 2.2 Implement `fetch_rates_download(date_str)` using B3's `GetDownloadFile` endpoint (returns `list[RateRecord]` parsed from base64-encoded CSV)
- [x] 2.3 Implement `fetch_historical_rates(base_date, progress_callback)` using `concurrent.futures.ThreadPoolExecutor` with 4 workers to fetch 5 dates (28, 21, 14, 7, 0 days ago)
- [x] 2.4 Implement fallback: if `GetDownloadFile` returns empty, retry with `fetch_reference_rates(date, page_size=100)`
- [x] 2.5 Write tests for `fetch_rates_download` with mocked B3 endpoint (base64 CSV)
- [x] 2.6 Write tests for `fetch_historical_rates` with mocked endpoints returning 5 dates

## 3. Curve Evolution Chart Rendering

- [x] 3.1 Implement `render_curve_evolution(fig, date_rates_dict)` that plots 5 superposed average-rate curves with gradient coloring (oldest → lightest, newest → darkest)
- [x] 3.2 Add quiver arrows at key maturities (0, 1, 2, 3, 5, 10, 15, 20) with horizontal offset for consecutive transitions and color gradient
- [x] 3.3 Add legend mapping line colors to ISO date labels
- [x] 3.4 Style base date curve with linewidth=2.5 and full opacity; historical curves with decreasing alpha (0.3→0.9) and linewidth (0.8→2.0)
- [x] 3.5 Write tests for `render_curve_evolution` using matplotlib Agg backend (verify axes labels, number of lines, presence of quiver)

## 4. GUI: Radio Buttons

- [x] 4.1 Replace `consolidate_var` (BooleanVar) with `view_var` (StringVar) initialized to `"raw"`
- [x] 4.2 Replace checkbox with three `ttk.Radiobutton` widgets: "Detalhado", "Consolidado", "Evolução da curva"
- [x] 4.3 Implement `toggle_view()` to dispatch to the appropriate render function based on `view_var` value
- [x] 4.4 Preserve view state across data fetches

## 5. GUI: Evolution Mode Integration

- [x] 5.1 Modify `fetch_rates()` to detect evolution mode and call `fetch_historical_rates()` instead of single-date fetch
- [x] 5.2 Add progress callback to update status bar with "Buscando taxas históricas... (N/5 concluídas)" during evolution fetch
- [x] 5.3 Implement `handle_historical_fetch_success(historical_data)` to store per-date records and render evolution chart
- [x] 5.4 Handle partial failures in historical fetch: report which date(s) failed, still render with available dates
- [x] 5.5 Auto-set date to today when switching to evolution mode
- [x] 5.6 Show prompt "Clique em Buscar para carregar dados históricos" when user switches to evolution mode without historical data

## 6. GUI: 30-day Query Limit

- [x] 6.1 Validate input date in `fetch_rates()` for raw/consolidated modes: reject dates older than 30 days from today
- [x] 6.2 Show error message "Data muito antiga. Informe uma data nos últimos 30 dias." in status bar
- [x] 6.3 Evolution mode bypasses 30-day validation (historical fetch handles old dates via fallback)

## 7. GUI: DatePicker Calendar

- [x] 7.1 Implement `DatePicker` popup calendar class using pure tkinter (month/year navigation, clickable day grid)
- [x] 7.2 Add calendar button (📅) next to the date entry in the GUI top frame
- [x] 7.3 On day selection, set `date_var` to `YYYY-MM-DD` format

## 8. GUI: Chart Title Position

- [x] 8.1 Move chart title down to `y=0.92` in `_redraw_chart()` for all three view modes (avoids overlap with matplotlib toolbar)

## 9. GUI: Data Export in Evolution Mode

- [x] 9.1 Implement `format_evolution_csv(historical_data)` that produces CSV with columns `DATA;ANO;TAXA_MEDIA` for all 5 dates
- [x] 9.2 Modify `copy_data()` to dispatch to evolution CSV formatter when in evolution mode
- [x] 9.3 Write tests for `format_evolution_csv`

## 10. GUI: Chart Export in Evolution Mode

- [x] 10.1 Verify that "Copiar gráfico" and "Exportar PNG" work correctly with the evolution chart

## 11. Version Bump

- [x] 11.1 Update `__version__` in `b3_selic_pre.py` from `"0.2.3"` to `"0.3.0"`

## 12. Final Verification

- [x] 12.1 Run existing test suite to ensure no regressions (35 tests pass)
- [x] 12.2 Run full manual test: fetch in raw mode → switch to consolidated → switch to evolution → fetch evolution data → copy data → copy chart → export PNG
- [x] 12.3 Verify quiver arrows render correctly for both upward and downward rate movements
