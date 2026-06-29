## Context

Currently `fetch_reference_rates()` in `b3_client.py` loops through pages without exposing progress. The GUI in `gui.py` shows an indeterminate bar for single-date fetches — it spins endlessly because neither the client nor the GUI know how many pages to expect.

The B3 API response includes pagination metadata (`totalCount`, `pageSize`) alongside `results`. The current `normalize_records()` only extracts `results`, discarding this metadata.

## Goals / Non-Goals

**Goals:**
- Single-date fetch shows determinate progress after the first page reveals total pages
- `fetch_reference_rates()` accepts an optional `progress_callback(current, total)`
- Pagination metadata is extracted and exposed by the client layer
- Hybrid approach: indeterminate → determinate transition at page 1
- Historical fetch behavior is unchanged

**Non-Goals:**
- Changing the B3 API response parsing beyond adding pagination metadata
- Refactoring the threading model
- Changing the CLI path (CLI doesn't show progress bars)
- Changing `fetch_rates_download()` (no pagination)

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Where to extract metadata | `fetch_reference_rates()` not `normalize_records()` | `normalize_records()` is a pure data transformer; pagination metadata is a protocol concern. The caller needs raw `totalCount` to set progress bar max. |
| Metadata shape | Return `(records, total_pages)` tuple, or pass via a mutable `FetchContext` | Tuple is simpler and doesn't require new types. But changing return type breaks callers. Better: accept optional `ProgressTracker` object that both collects metadata and reports progress. |
| Progress API | `progress_callback(current, total)` called synchronously after each page | Matches existing pattern in `fetch_historical_rates()`. The GUI thread-safety (`root.after`) is handled in `gui.py`, not in the client. |
| Hybrid transition in GUI | `_set_ui_locked(True)` starts indeterminate; after first callback, `_determinate_bar` replaces it | Clean separation: the GUI owns the progress bar widget swap. The client only reports numbers. |

### Data flow

```
gui.py:fetch_rates()
  │
  ├─ _set_ui_locked(True)
  │    └─ pack _indeterminate_bar, start()
  │
  ├─ threading.Thread
  │    └─ fetch_reference_rates(date, progress_callback=cb)
  │         │
  │         ├─ page 1: fetch + parse → extract totalCount
  │         │    └─ cb(1, total_pages) ← FIRST CALLBACK
  │         │         └─ root.after(0, ...)
  │         │              ├─ _indeterminate_bar.stop(), pack_forget()
  │         │              ├─ _determinate_bar["maximum"] = total_pages
  │         │              ├─ _determinate_bar.pack(), update value=1
  │         │              └─ status: "Buscando taxas… (1/{total_pages})"
  │         │
  │         ├─ page 2: cb(2, total_pages)
  │         │    └─ root.after → _determinate_bar["value"] = 2
  │         │
  │         ├─ page N: cb(N, total_pages)
  │         │
  │         └─ return records
  │
  └─ handle_fetch_success(records)
       └─ _set_ui_locked(False) → bars hidden
```

### Fallback

If the API response lacks `totalCount` (unexpected format), `total_pages = None` and the GUI stays indeterminate — degrading gracefully.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| API changes format and removes `totalCount` | Graceful fallback: stay indeterminate |
| Thread race: user clicks Buscar twice before first page returns | Already guarded by `_set_ui_locked` disabling the button; no change needed |
| `totalCount` is approximate (changes between page 1 and page N) | Unlikely in practice — reference rates are static for a given date. B3 computes them once per day. |
| Progress callback called from non-GUI thread | `gui.py` wraps the callback in `root.after(0, ...)` before touching tk widgets |
