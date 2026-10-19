## REMOVED Requirements

### Requirement: Multi-date historical rate fetch via GetDownloadFile

**Reason**: The CSV download is no longer the primary data source. The B3 `GetList` API provides the same rate records with page metadata, and the CSV path has a line-ending parsing defect.

**Migration**: Use the new "Multi-date historical rate fetch via GetList" requirement. The CSV download remains only as a temporary fallback for dates outside the `GetDate` window.

## ADDED Requirements

### Requirement: Multi-date historical rate fetch via GetList

The system SHALL provide a function `fetch_historical_rates(base_date)` that fetches SELIC Pré rates for 5 dates: the base date and 7, 14, 21, 28 days prior. The fetch SHALL use the B3 `GetList` API as the primary source, SHALL use `GetDate` to determine whether each date is available, and SHALL use the CSV download only as a temporary fallback for dates outside the `GetDate` window.

#### Scenario: GetList returns parsed RateRecords

- **WHEN** `GetList` returns a valid page for a historical date
- **THEN** the system returns a `list[RateRecord]` with `day252`, `day360` and `rate` parsed from the JSON fields

#### Scenario: Fetch returns rates for all 5 dates

- **WHEN** `fetch_historical_rates("2026-06-17")` is called and all 5 dates are available
- **THEN** it returns a dict mapping each of the 5 date strings (base date, 7, 14, 21, 28 days prior) to their respective `list[RateRecord]`

#### Scenario: Fetch uses parallel requests with progress callback

- **WHEN** the multi-date fetch is in progress
- **THEN** an optional `progress_callback(completed, total)` is called after each date completes
- **AND** at most 5 date fetches run concurrently

#### Scenario: Date outside the API window uses CSV fallback

- **WHEN** one of the 5 dates is not in the `GetDate` window
- **THEN** the system attempts the temporary CSV fallback for that date
- **AND** includes the CSV records in the result when the fallback succeeds

#### Scenario: Date unavailable from both sources

- **WHEN** a date is outside the `GetDate` window and the CSV fallback is empty
- **THEN** the multi-date fetch reports the unavailable date
- **AND** does not silently substitute a different date

#### Scenario: API communication failure is reported

- **WHEN** a date inside the `GetDate` window fails with `CommunicationError` after retries
- **THEN** the multi-date fetch reports the failed date
- **AND** does not mask the failure with the CSV fallback
