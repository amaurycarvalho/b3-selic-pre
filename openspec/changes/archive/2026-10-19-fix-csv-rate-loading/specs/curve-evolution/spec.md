## MODIFIED Requirements

### Requirement: Multi-date historical rate fetch via GetDownloadFile
The system SHALL provide a function `fetch_rates_download(date_str)` that uses the B3 `GetDownloadFile` endpoint (base64-encoded CSV) and a function `fetch_historical_rates(base_date)` that fetches SELIC Pré rates for 5 dates: the base date and 7, 14, 21, 28 days prior. The base date SHALL use `GetList` when it is the current date. Earlier dates SHALL use `GetDownloadFile` as the primary source and `GetList` only as a fallback after the CSV retries are exhausted. Every date SHALL use the empty-response retry policy and the completeness validation defined by the B3 rate source contract. A date that remains unavailable after all retries and fallback SHALL be reported and SHALL NOT be cached.

#### Scenario: GetDownloadFile returns parsed RateRecords
- **WHEN** `fetch_rates_download("2026-06-09")` is called and the B3 returns valid base64 CSV
- **THEN** it returns a `list[RateRecord]` with `day252`, `day360` and `rate` parsed from the CSV columns

#### Scenario: Fetch returns rates for all 5 dates
- **WHEN** `fetch_historical_rates("2026-06-17")` is called and all 5 dates have data
- **THEN** it returns a dict mapping each of the 5 date strings (today, 7, 14, 21, 28 days ago) to their respective `list[RateRecord]`

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

## ADDED Requirements

### Requirement: Evolution charts tolerate empty and missing data

The evolution chart renderers and the GUI view-model SHALL handle an empty historical mapping, empty per-date record lists and missing dates without raising an exception. If no usable historical date exists, the chart SHALL show the empty-data message or fall back to the active base view. If some dates are available, the chart SHALL render the available curves and the status bar SHALL identify the unavailable dates.

#### Scenario: Empty historical mapping renders the empty state
- **WHEN** `render_curve_evolution`, `render_detailed_evolution` or `render_3d_evolution` receives an empty mapping
- **THEN** the chart shows the empty-data message and no exception is raised

#### Scenario: A date with an empty record list is skipped
- **WHEN** the historical mapping contains a date whose record list is empty
- **THEN** that date is not plotted and the remaining dates are rendered without an exception

#### Scenario: All dates empty falls back to the base view
- **WHEN** the GUI has evolution active but no historical date contains records
- **THEN** the view-model selects the active base view and the chart shows the empty-data message

#### Scenario: Missing dates are reported
- **WHEN** the historical mapping has fewer than five usable dates
- **THEN** the status bar lists the unavailable dates and the available curves remain visible
