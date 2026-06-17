## ADDED Requirements

### Requirement: Average rate per year computation
The system SHALL provide a function `average_rate_by_year(records)` that computes the arithmetic mean of `min_rate` and `max_rate` for each year, using the output of `consolidate_by_year`.

#### Scenario: Average rate matches midpoint of min and max
- **WHEN** given records that consolidate to `{year: 0, min_rate: 14.0, max_rate: 15.0}`
- **THEN** the function returns `{0: 14.5}`

### Requirement: Multi-date historical rate fetch via GetDownloadFile
The system SHALL provide a function `fetch_rates_download(date_str)` that uses the B3 `GetDownloadFile` endpoint (base64-encoded CSV) and a function `fetch_historical_rates(base_date)` that fetches SELIC Pré rates for 5 dates: the base date and 7, 14, 21, 28 days prior.

#### Scenario: GetDownloadFile returns parsed RateRecords
- **WHEN** `fetch_rates_download("2026-06-09")` is called and the B3 returns valid base64 CSV
- **THEN** it returns a `list[RateRecord]` with `day252`, `day360` and `rate` parsed from the CSV columns

#### Scenario: Fetch returns rates for all 5 dates
- **WHEN** `fetch_historical_rates("2026-06-17")` is called
- **THEN** it returns a dict mapping each of the 5 date strings (today, 7, 14, 21, 28 days ago) to their respective `list[RateRecord]`

#### Scenario: Fetch uses parallel requests with progress callback
- **WHEN** the multi-date fetch is in progress
- **THEN** an optional `progress_callback(completed, total)` is called after each date completes

#### Scenario: Empty GetDownloadFile falls back to GetList
- **WHEN** `GetDownloadFile` returns empty for a historical date
- **THEN** the system falls back to `fetch_reference_rates(date, page_size=100)`

### Requirement: Curve evolution chart rendering
The system SHALL provide a function `render_curve_evolution(fig, date_rates)` that plots 5 superposed curves of average rate per year, with gradient coloring and quiver arrows at key maturities.

#### Scenario: Five curves with gradient are plotted
- **WHEN** `render_curve_evolution` is called with data for 5 dates
- **THEN** the chart shows 5 lines in the range years 0-20, with the oldest curve having the lightest color and the newest (base date) having the darkest color

#### Scenario: Quiver arrows at key maturities
- **WHEN** the evolution chart is rendered
- **THEN** quiver arrows are drawn at maturities 0, 1, 2, 3, 5, 10, 15, 20 showing consecutive rate transitions from oldest to newest date

#### Scenario: Arrow direction indicates rate movement
- **WHEN** rates increased between consecutive dates at a given maturity
- **THEN** the arrow at that maturity points upward (positive V component)
- **WHEN** rates decreased
- **THEN** the arrow points downward (negative V component)

#### Scenario: Base date curve is visually prominent
- **WHEN** the evolution chart is rendered
- **THEN** the base date curve uses a solid line with width >= 2.0 and full opacity

#### Scenario: Historical curves use fading alpha
- **WHEN** the evolution chart is rendered
- **THEN** each historical curve has lower alpha and thinner line width than the next more recent curve

#### Scenario: Y-axis auto-scales to fit all data
- **WHEN** the evolution chart is rendered
- **THEN** the Y-axis range is automatically set to include all 5 curves with margins

#### Scenario: X-axis ranges from year 0 to year 20
- **WHEN** the evolution chart is rendered
- **THEN** the X-axis shows integer ticks from 0 to 20

### Requirement: Legend identifies each date
The evolution chart SHALL display a legend mapping each line color/alpha to its date label.

#### Scenario: Legend shows date labels
- **WHEN** the evolution chart is rendered
- **THEN** the legend contains 5 entries showing each date in ISO format (YYYY-MM-DD)
