## 1. Expose pagination metadata in the client layer

- [x] 1.1 Modify `fetch_reference_rates_page()` to extract `totalCount` from API response and return it alongside records
- [x] 1.2 Add optional `progress_callback(current, total)` parameter to `fetch_reference_rates()`
- [x] 1.3 Call `progress_callback(page_number, total_pages)` after each page fetch

## 2. Update GUI for hybrid determinate progress

- [x] 2.1 In `fetch_rates()`, wrap `progress_callback` in `root.after(0, ...)` for thread safety
- [x] 2.2 Add `_on_fetch_progress()` that switches from indeterminate to determinate bar when total pages known
- [x] 2.3 Update determinate bar value and page count on each callback
- [x] 2.4 Show page count in status message: "Buscando taxas… (2/5 páginas)"

## 3. Verify

- [x] 3.1 Run full test suite (87 passed: 65 unit + 22 GUI)
- [x] 3.2 Manual check: single-date fetch shows determinate progress advancing per page
