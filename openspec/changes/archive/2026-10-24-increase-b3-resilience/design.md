# Design

## Context

See `proposal.md` for motivation. The current implementation has three constraints that shape the approach:

- `retry_empty` retries only empty results. Exceptions from the opener bypass the loop entirely.
- `COMMUNICATION_EXCEPTIONS` lives in `infrastructure/b3_client.py`, which already imports `b3_list` and `b3_download`; the lower-level modules cannot import it back without creating a cycle.
- The timeout default `30` is repeated across `b3_list.py`, `b3_download.py` and `b3_client.py`.
- `CachedB3Client` stores `ttl_minutes` in each cache entry, and `DiskCache` applies the stored value before the caller's current value.

## Goals / Non-Goals

**Goals:**

- One 60-second timeout value shared by all B3 requests.
- Retry empty responses with the existing six-attempt budget.
- Retry transient communication failures with a separate three-attempt budget.
- Keep data errors immediate and non-retried.
- Preserve fallback from `GetDownloadFile` to `GetList` for past dates, including after a timeout.
- Change the current-date cache TTL default to 360 minutes without a cache schema change.

**Non-Goals:**

- Introducing user-configurable timeout or TTL settings.
- Changing HTTP status handling, pagination, payload format or source selection rules.
- Changing the cache file layout or bumping `SCHEMA_VERSION`.
- Modifying CLI, GUI or MCP contracts.

## Decisions

### 1. Centralize the timeout in the domain constants

Add `DEFAULT_B3_TIMEOUT_SECONDS = 60` to `domain/constants.py` and use it as the default in `b3_list.fetch_reference_rates_page`, `b3_list.fetch_reference_rates`, `b3_download.fetch_rates_download` and `b3_client.fetch_rates_for_date`.

Rationale: the module already owns B3 defaults such as page size and language, and a single constant prevents drift between the endpoints.

Alternative considered: an infrastructure-only constant. Rejected because `b3_client`, `b3_list` and `b3_download` are separate modules and would need an extra shared module for the same value.

### 2. Move transient-error classification next to the retry logic

Define the transport exception tuple in `infrastructure/b3_retry.py` as `TRANSIENT_ERRORS`, then re-export it from `b3_client` as `COMMUNICATION_EXCEPTIONS` so existing imports keep working.

Rationale: `b3_retry` is the lowest-level shared module and can be imported by `b3_list`, `b3_download` and `b3_client` without a cycle.

The tuple keeps the current classes: `urllib.error.URLError`, `http.client.HTTPException`, `TimeoutError`, `ConnectionError`, `ssl.SSLError` and `socket.gaierror`.

### 3. Use one retry loop with independent budgets

Replace the empty-only loop with a loop that tracks two budgets:

- `empty_attempts = 6` for results that are empty.
- `transient_attempts = 3` for exceptions in `TRANSIENT_ERRORS`.

A non-empty result returns immediately. A data exception that is not in `TRANSIENT_ERRORS` propagates on the first occurrence. When either budget is exhausted, the loop raises `CommunicationError` identifying the date and source, chaining the last transient exception when applicable. Backoff remains exponential with jitter and the existing ceilings `(0.5, 1.0, 2.0, 4.0, 4.0)`.

Rationale: a single loop avoids nested retries that could multiply attempts. Independent budgets preserve the existing six-attempt guarantee for empty responses while bounding timeout retries at three.

Alternative considered: retry exceptions with six attempts too. Rejected because with a 60-second timeout a single page could take roughly six minutes; three attempts cap it near three minutes plus backoff.

Alternative considered: two nested retry helpers. Rejected because a timeout inside an empty retry would multiply attempts and make the worst case harder to reason about.

### 4. Apply the retry at the request boundary

Use the retry loop in `_fetch_page` for every `GetList` page and in `fetch_rates_download` for the CSV request. `fetch_rates_for_date` keeps falling back to `GetList` on `CommunicationError`, which now also covers exhausted transient failures.

Rationale: centralizing retry around the HTTP operation keeps pagination, CSV parsing and completeness checks unchanged. Data errors still propagate without triggering a source switch.

### 5. Change the TTL default without migrating entries

Set the `CachedB3Client` default to `ttl_minutes=360`. Keep `DiskCache` reading the stored `ttl_minutes` first. Entries written before this change carry `ttl_minutes: 30` and will expire early once; the subsequent fetch writes the new value.

Rationale: no schema change or cache invalidation is needed, and the one-time early expiry is harmless.

Alternative considered: ignore the stored TTL and always use the caller's TTL. Rejected because it would silently change the meaning of existing metadata and weaken the per-entry configuration contract.

## Risks / Trade-offs

- **Worst-case latency per page** → Three attempts of 60 s plus backoff cap a single page near three minutes. The trade-off is intentional to avoid a single timeout failing the whole fetch. If this becomes excessive, a total deadline can be added in a later change.
- **HTTP 4xx is retried** → `urllib.error.URLError` includes `HTTPError`, so a deterministic client error may be retried three times. The B3 endpoints normally respond with `200` and an empty body, so the impact is low; status-specific handling is left out of scope.
- **Stale current-date data** → A 6-hour TTL may serve older intraday data. SELIC reference rates are daily data and a forced refresh still bypasses the cache.
- **One-time early cache expiry** → Entries with `ttl_minutes: 30` ignore the new default until rewritten. This is expected and avoids a migration step.
- **Test brittleness around exact attempts** → Tests currently assert six calls and exact backoff lists. New tests must distinguish empty budgets from transient budgets to avoid overlapping assertions.

## Migration Plan

1. Deploy the code change; no cache format or config migration is required.
2. Existing current-date entries expire by their stored TTL and are rewritten with 360 minutes on the next successful fetch.
3. Rollback is a code revert. Entries written with `ttl_minutes: 360` remain valid for up to 6 hours, which is acceptable for the previous behavior; deleting the cache directory is an optional immediate reset.
