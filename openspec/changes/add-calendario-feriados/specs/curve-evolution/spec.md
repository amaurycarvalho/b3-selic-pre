# Spec Delta

## MODIFIED Requirements

### Requirement: Multi-date historical rate fetch via GetDownloadFile
The system SHALL provide a function `fetch_rates_download(date_str)` that uses the B3 `GetDownloadFile` endpoint (base64-encoded CSV) and a function `fetch_historical_rates(base_date)` that fetches SELIC Pré rates for 5 dates: the base date and 7, 14, 21, 28 days prior. The base date SHALL already be resolved to a business day. Each of the 7, 14, 21 and 28-day targets SHALL be resolved to the previous business day when it falls on a weekend or holiday, and targets that resolve to the same date SHALL be deduplicated. The base date SHALL use `GetList` when it is the current date. Earlier dates SHALL use `GetDownloadFile` as the primary source and `GetList` only as a fallback after the CSV retries are exhausted. Every date SHALL use the empty-response retry policy and the completeness validation defined by the B3 rate source contract. A date that remains unavailable after all retries and fallback SHALL be reported and SHALL NOT be cached.

#### Scenario: GetDownloadFile returns parsed RateRecords
- **WHEN** `fetch_rates_download("2026-06-09")` is called and the B3 returns valid base64 CSV
- **THEN** it returns a `list[RateRecord]` with `day252`, `day360` and `rate` parsed from the CSV columns

#### Scenario: Fetch returns rates for all 5 dates
- **WHEN** `fetch_historical_rates("2026-06-17")` is called and all 5 resolved dates have data
- **THEN** it returns a dict mapping each of the 5 resolved date strings to their respective `list[RateRecord]`

#### Scenario: Fetch uses parallel requests with progress callback
- **WHEN** the multi-date fetch is in progress
- **THEN** an optional `progress_callback(completed, total)` is called after each date completes

#### Scenario: Today uses GetList
- **WHEN** the base date is the current date
- **THEN** that date is fetched with `GetList` and not with `GetDownloadFile`

#### Scenario: Empty GetDownloadFile falls back to GetList
- **WHEN** `GetDownloadFile` remains empty for a historical date after all retries
- **THEN** the system falls back to `fetch_reference_rates(date, page_size=100)` with retry and completeness validation

#### Scenario: Unavailable date is reported and not cached
- **WHEN** a historical date remains empty after `GetDownloadFile` retries and the `GetList` fallback
- **THEN** the date is reported as unavailable and no cache entry is written for it

#### Scenario: Incomplete GetList collection is rejected
- **WHEN** the `GetList` fallback collects fewer records than `page.totalRecords` after the allowed retries
- **THEN** the system reports a communication failure for that date instead of using the partial collection

#### Scenario: Holiday target is resolved before any request
- **WHEN** a 7, 14, 21 or 28-day target falls on a holiday or weekend
- **THEN** the target is replaced by the previous business day
- **THEN** no request is made for the non-business date

#### Scenario: Duplicate resolved targets are collapsed
- **WHEN** two targets resolve to the same business day
- **THEN** the evolution mapping contains a single entry for that date
