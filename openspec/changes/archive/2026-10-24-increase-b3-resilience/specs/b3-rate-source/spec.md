# Spec Delta

## MODIFIED Requirements

### Requirement: Source selection by date

The system SHALL select the B3 source by reference date. The current date SHALL use `GetList`. Earlier dates SHALL use `GetDownloadFile` first, with `GetList` as fallback after `GetDownloadFile` retries are exhausted by empty responses or transient failures. The same selection SHALL apply to the GUI, the CLI and the multi-date evolution fetch.

#### Scenario: Current date uses GetList
- **WHEN** the requested reference date is the current date
- **THEN** the system fetches the rates using `GetList` and does not call `GetDownloadFile`

#### Scenario: Earlier date uses GetDownloadFile
- **WHEN** the requested reference date is earlier than the current date and the CSV returns valid records
- **THEN** the system returns the CSV records and does not call `GetList`

#### Scenario: Earlier date falls back to GetList after CSV retries
- **WHEN** the requested reference date is earlier than the current date and `GetDownloadFile` remains empty after all retries
- **THEN** the system tries `GetList` for that date

#### Scenario: Earlier date falls back to GetList after a transient failure
- **WHEN** the requested reference date is earlier than the current date and `GetDownloadFile` exhausts its retries because of a timeout or another transient communication failure
- **THEN** the system tries `GetList` for that date

#### Scenario: Data errors do not trigger source fallback
- **WHEN** `GetDownloadFile` returns a malformed CSV or `GetList` returns an invalid schema
- **THEN** the system reports a data error and does not silently switch to the other source

## ADDED Requirements

### Requirement: B3 request timeout

The system SHALL apply a 60-second timeout to every B3 request, including `GetList` and `GetDownloadFile`, and SHALL use the same value where source selection builds a request.

#### Scenario: GetList uses the 60-second timeout
- **WHEN** the system requests a page from `GetList`
- **THEN** the HTTP request uses a 60-second timeout

#### Scenario: GetDownloadFile uses the 60-second timeout
- **WHEN** the system downloads a CSV from `GetDownloadFile`
- **THEN** the HTTP request uses a 60-second timeout

### Requirement: Retry of transient communication failures

The system SHALL retry transient network and transport failures up to three attempts for both `GetList` and `GetDownloadFile`. The backoff SHALL be exponential with jitter and bounded by a maximum delay per attempt. Data errors SHALL NOT be retried. Exhausted retries SHALL be reported as a communication failure identifying the date and the source.

#### Scenario: Timeout is retried and succeeds
- **WHEN** a request times out on the first attempt and returns valid data on a later attempt
- **THEN** the system returns the valid data without reporting an error

#### Scenario: Persistent timeout becomes a communication failure
- **WHEN** a request times out on every allowed attempt
- **THEN** the system raises a communication failure after three attempts

#### Scenario: Transient network failure is retried
- **WHEN** a request fails with a transient network exception such as a connection reset or DNS failure
- **THEN** the system retries the request before reporting an error

#### Scenario: Data error is not retried
- **WHEN** the response body is not valid JSON, is not valid base64 CSV, or does not contain the expected fields
- **THEN** the system raises a data error after the first attempt

#### Scenario: Transient retry backoff includes jitter
- **WHEN** an attempt fails with a transient communication error and another attempt will be made
- **THEN** the delay before the next attempt includes a random jitter component and respects the capped exponential backoff
