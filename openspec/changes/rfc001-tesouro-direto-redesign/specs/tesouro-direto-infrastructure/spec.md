## ADDED Requirements

### Requirement: Fetch dataset metadata via CKAN API
The system SHALL fetch Treasury Direct dataset metadata using the CKAN JSON API instead of HTML scraping.

#### Scenario: API returns structured metadata
- **WHEN** the system requests `GET /api/3/action/package_show?id=vendas-do-tesouro-direto`
- **THEN** the response SHALL contain dataset title, author, version, last update date, and resource URLs

#### Scenario: API uses urllib with opener injection
- **WHEN** `fetch_tesouro_metadata()` is called
- **THEN** it SHALL accept an `opener` parameter defaulting to `urllib.request.urlopen` for testability

#### Scenario: Response is parsed as JSON
- **WHEN** the API response is received
- **THEN** the system SHALL parse it with `json.loads()` and extract the `result` object

### Requirement: Extract resource URLs from CKAN response
The system SHALL extract CSV and PDF resource URLs from the CKAN package_show response.

#### Scenario: CSV resource URL is extracted
- **WHEN** the `resources` array in the CKAN response contains a resource with format "CSV"
- **THEN** the system SHALL extract its `url` and `id` fields

#### Scenario: PDF metadata resource URL is extracted
- **WHEN** the `resources` array contains a resource with format "PDF" and label "Metadados"
- **THEN** the system SHALL extract its `url` field

#### Scenario: Missing CSV resource raises error
- **WHEN** no CSV resource is found in the CKAN response
- **THEN** the system SHALL raise a `ValueError` with message "Recurso CSV não encontrado no dataset."

### Requirement: Download CSV file
The system SHALL download the Treasury Direct CSV file from the extracted resource URL.

#### Scenario: Successful download saves file to disk
- **WHEN** the CSV URL is valid and the server responds with HTTP 200
- **THEN** the system SHALL save the file contents to the specified local path

#### Scenario: Download supports streaming with progress callback
- **WHEN** the CSV is downloaded with `stream=True`
- **THEN** the system SHALL invoke an optional `progress_callback(bytes_received, total_bytes)` for GUI feedback

#### Scenario: Download uses timeout
- **WHEN** the download request is made
- **THEN** it SHALL use a configurable timeout (default: 60 seconds)

#### Scenario: Download failure raises error
- **WHEN** the server responds with a non-200 status code
- **THEN** the system SHALL raise a `ValueError` with the HTTP status code in the message

### Requirement: Conditional download via HTTP caching headers
The system SHALL use `ETag` and `If-Modified-Since` headers to avoid re-downloading unchanged CSV files.

#### Scenario: ETag matches cached version
- **WHEN** the server responds with HTTP 304 Not Modified
- **THEN** the system SHALL reuse the locally cached CSV file without downloading

#### Scenario: ETag header is stored after download
- **WHEN** a CSV file is downloaded successfully
- **THEN** the system SHALL store the `ETag` and `Last-Modified` response headers for future conditional requests

### Requirement: Tesouro disk cache with XDG paths
The system SHALL cache Tesouro Direto data in an XDG-compliant directory separate from B3 rate data.

#### Scenario: Cache directory is XDG-compliant
- **WHEN** the system runs on Linux
- **THEN** the cache SHALL be stored at `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`

#### Scenario: CSV file is cached by download date
- **WHEN** the CSV is downloaded and cached
- **THEN** the file SHALL be stored as `vendastesourodireto.csv` in the tesouro cache directory

#### Scenario: Metadata is cached alongside CSV
- **WHEN** dataset metadata is fetched from CKAN API
- **THEN** it SHALL be cached as `metadata.json` in the tesouro cache directory

#### Scenario: Cache TTL enforced for today
- **WHEN** the cached CSV is older than 6 hours
- **THEN** the system SHALL treat it as expired and attempt conditional re-download

#### Scenario: Corrupted cache is self-healing
- **WHEN** the cached metadata JSON is invalid or the cached CSV is empty
- **THEN** the system SHALL delete the corrupted file and re-fetch from the source

### Requirement: TesouroDiretoClient wraps fetch logic
The system SHALL provide a `TesouroDiretoClient` class exposing a clean interface for fetching Tesouro Direto data.

#### Scenario: Client returns both metadata and records
- **WHEN** `TesouroDiretoClient.fetch_movimentacoes()` is called
- **THEN** it SHALL return a tuple of `(metadata: dict, records: list[MovimentacaoTesouroDireto])`

#### Scenario: Client uses cache when available
- **WHEN** valid cached data exists (within TTL)
- **THEN** the client SHALL return cached data without making any HTTP requests

#### Scenario: Client force-refresh bypasses cache
- **WHEN** `TesouroDiretoClient.fetch_movimentacoes(force=True)` is called
- **THEN** the system SHALL skip cache and download fresh data from the source
