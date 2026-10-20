## Purpose

Allow users to visualize how the SELIC Pré interest rate curve has moved over time by superimposing multiple historical curves and showing arrow indicators for rate changes at key maturities.

## Requirements

### Requirement: Average rate per year computation
The system SHALL provide a function `average_rate_by_year(records)` that computes the arithmetic mean of `min_rate` and `max_rate` for each year, using the output of `consolidate_by_year`.

#### Scenario: Average rate matches midpoint of min and max
- **WHEN** given records that consolidate to `{year: 0, min_rate: 14.0, max_rate: 15.0}`
- **THEN** the function returns `{0: 14.5}`

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

### Requirement: Curve evolution chart rendering
The system SHALL provide a function `render_curve_evolution(fig, date_rates)` that plots 5 superposed curves of average rate per year, with gradient coloring and quiver arrows at key maturities.

#### Scenario: Five curves with gradient are plotted
- **WHEN** `render_curve_evolution` is called with data for 5 dates
- **THEN** the chart shows 5 lines in the range years 0-20, with the oldest curve having the lightest color and the newest (base date) having the darkest color

#### Scenario: Quiver arrows at key maturities
- **WHEN** the evolution chart is rendered
- **THEN** quiver arrows are drawn at maturities 0, 1, 2, 3, 5, 10, 15, 20 showing consecutive rate transitions from oldest to newest date
- **AND** at most one arrow is drawn per tick position, cycling through transitions by offset (offset 1, step 5)

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

### Requirement: Detailed evolution rendering as alternative view
The system SHALL provide `render_detailed_evolution(fig, date_rates)` alongside the existing `render_curve_evolution` as an alternative rendering path for curve evolution data, selected based on the active radio button when evolution is enabled.

#### Scenario: Detailed evolution is selected via radio button
- **WHEN** evolution checkbox is ON and "Curva curta" radio is selected
- **THEN** `render_detailed_evolution` is called instead of `render_curve_evolution`

### Requirement: 3D rendering mode available from consolidated evolution
When the evolution checkbox and 3D checkbox are both ON and the "Curva longa" radio is selected, the system SHALL render the consolidated evolution data as a 3D surface instead of 2D lines.

#### Scenario: 3D checkbox enables 3D consolidated rendering
- **WHEN** evolution checkbox is ON
- **AND** 3D checkbox is ON
- **AND** "Curva longa" radio is selected
- **THEN** `render_3d_evolution(fig, historical_data, consolidated=True)` is called instead of `render_curve_evolution`

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
