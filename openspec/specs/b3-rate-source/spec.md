# B3 Rate Source

## Purpose

Define como a aplicação escolhe e carrega as taxas referenciais da B3, garantindo que a data corrente use o `GetList`, datas anteriores usem o `GetDownloadFile` e que respostas vazias, parciais ou malformadas não sejam tratadas como dados válidos.

## Requirements

### Requirement: Source selection by date

The system SHALL select the B3 data source based on the requested reference date. The current date SHALL use `GetList`. Dates earlier than the current date SHALL use `GetDownloadFile` as the primary source, with `GetList` used only as a fallback after `GetDownloadFile` retries are exhausted. The same selection SHALL be used by the GUI, the CLI and the multi-date evolution fetch.

#### Scenario: Current date uses GetList
- **WHEN** the requested reference date is the current date
- **THEN** the system fetches the rates using `GetList` and does not call `GetDownloadFile`

#### Scenario: Earlier date uses GetDownloadFile
- **WHEN** the requested reference date is earlier than the current date and the CSV returns valid records
- **THEN** the system returns the CSV records and does not call `GetList`

#### Scenario: Earlier date falls back to GetList after CSV retries
- **WHEN** the requested reference date is earlier than the current date and `GetDownloadFile` remains empty after all retries
- **THEN** the system tries `GetList` for that date

#### Scenario: Data errors do not trigger source fallback
- **WHEN** `GetDownloadFile` returns a malformed CSV or `GetList` returns an invalid schema
- **THEN** the system reports a data error and does not silently switch to the other source

### Requirement: Retry and classification for empty responses

The system SHALL treat an HTTP `200` response with an empty body as a possible transient failure and SHALL retry the request up to six attempts. The backoff between attempts SHALL be exponential with jitter, bounded by a maximum delay per attempt. The retry SHALL apply to both `GetDownloadFile` and `GetList`. Invalid JSON, invalid CSV or an unexpected response schema SHALL NOT be retried. After the retries are exhausted, a persistent empty response SHALL be reported as a communication failure.

#### Scenario: Transient empty response is retried and succeeds
- **WHEN** an endpoint returns an empty body on the first attempt and valid data on a subsequent attempt
- **THEN** the system returns the valid data without reporting an error

#### Scenario: Persistent empty response becomes a communication failure
- **WHEN** an endpoint returns an empty body on every allowed attempt
- **THEN** the system raises a communication failure identifying the date and the source, and does not return an empty result as success

#### Scenario: Invalid payload is a data error
- **WHEN** the response body is not valid JSON, is not valid base64 CSV, or does not contain the expected fields
- **THEN** the system raises a data error and does not retry

#### Scenario: Retry budget is bounded
- **WHEN** an endpoint keeps returning empty bodies
- **THEN** the system stops after six attempts and does not retry indefinitely

#### Scenario: Retry backoff includes jitter
- **WHEN** an attempt fails with an empty body and another attempt will be made
- **THEN** the delay before the next attempt includes a random jitter component and respects the capped exponential backoff

### Requirement: GetList pagination and completeness

The system SHALL read pagination metadata from the `page` object (`pageNumber`, `pageSize`, `totalRecords`, `totalPages`) and SHALL fetch every page from 1 through `totalPages`. An expected page that returns an empty `results` list SHALL be retried. After collecting all pages, the system SHALL compare the number of collected records with `totalRecords` and SHALL fail explicitly when they differ. A page count above the configured maximum SHALL be rejected.

#### Scenario: All pages are fetched
- **WHEN** the first page reports `totalPages` greater than 1
- **THEN** the system fetches pages 1 through `totalPages` and returns the combined records

#### Scenario: Empty expected page is retried
- **WHEN** a page expected to contain records returns an empty `results` list
- **THEN** the system retries that page before declaring the collection complete

#### Scenario: Incomplete collection is rejected
- **WHEN** the collected record count differs from `totalRecords` after the allowed retries
- **THEN** the system raises a communication failure with the expected and collected counts

#### Scenario: Excessive page count is rejected
- **WHEN** `totalPages` exceeds the configured maximum
- **THEN** the system rejects the query without continuing pagination

#### Scenario: Zero records is treated as empty
- **WHEN** `totalRecords` is zero
- **THEN** the system treats the response as empty and applies the empty-response retry policy

### Requirement: CSV parsing

The system SHALL parse `GetDownloadFile` CSV using line splitting that supports both `\n` and `\r\n`, SHALL strip whitespace from every field, and SHALL return rate values without a trailing carriage return. The header line SHALL be ignored and blank lines SHALL be skipped. Every data line SHALL contain the description, business-day, calendar-day and rate columns; malformed lines SHALL produce a data error instead of being silently discarded.

#### Scenario: CRLF CSV is parsed correctly
- **WHEN** the CSV uses `\r\n` line endings
- **THEN** the parsed `rate` values contain no `\r` and the records can be converted to numbers

#### Scenario: Blank lines are ignored
- **WHEN** the CSV contains empty lines between data lines
- **THEN** the system skips them and parses all remaining data lines

#### Scenario: Malformed line raises a data error
- **WHEN** a data line does not contain a valid business-day, calendar-day and rate triple
- **THEN** the system raises a data error and does not return a partial result as success
