## Why

The single-date fetch currently uses an indeterminate (spinning) progress bar, which gives no indication of actual progress. Users can't tell if the operation is progressing or stalled when fetching multiple pages from the B3 API. A determinate progress bar would provide real-time feedback on how many pages remain.

## What Changes

- `fetch_reference_rates()` in `b3_client.py` gains an optional `progress_callback` parameter, called after each page with `(current_page, total_pages)`
- Pagination metadata (`totalCount`, `pageSize`) is extracted from the API response to calculate total pages
- `gui.py` single-date fetch switches from indeterminate to determinate progress bar, using a hybrid approach:
  - Show indeterminate bar during first page load
  - Once the first response reveals total pages, switch to determinate bar for remaining pages
- Historical fetch's determinate behavior is unchanged

## Capabilities

### New Capabilities
*(none — this modifies an existing capability)*

### Modified Capabilities
- `loading-state`: Requirement "Indeterminate progress for single fetch" is upgraded to determinate progress with hybrid start.

## Impact

- `src/b3_selic_pre/infrastructure/b3_client.py` — `fetch_reference_rates()` signature and `normalize_records()` behavior
- `src/b3_selic_pre/presentation/gui.py` — `fetch_rates()` threading and progress bar logic
- `tests/test_b3_selic_pre.py` — may need updates for changed b3_client behavior
- No breaking API changes — `progress_callback` is optional
