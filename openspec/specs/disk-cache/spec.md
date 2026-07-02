# Disk Cache

## Purpose
Cache respostas da API B3 em disco para evitar downloads redundantes da mesma data.

## Requirements

### Requirement: Disk cache for B3 API responses
The system SHALL cache B3 API responses on disk so that the same date is not downloaded again.

#### Scenario: Cache hit returns cached data
- **WHEN** the user requests a date that has been previously downloaded and the cache is still valid
- **THEN** the system SHALL return the cached data without making an HTTP request

#### Scenario: Cache miss fetches from B3
- **WHEN** the user requests a date that is not in the cache
- **THEN** the system SHALL download the data from B3, store it in the cache, and return the result

#### Scenario: Cache populated after successful download
- **WHEN** the system successfully downloads data for a date
- **THEN** the system SHALL write the data to the cache for future reuse

### Requirement: TTL for current date only
The system SHALL apply a configurable TTL (Time-To-Live) only to the current date's cached data.

#### Scenario: Past date cache is always valid
- **WHEN** the cache contains data for a past date (before today)
- **THEN** the system SHALL treat it as valid regardless of age

#### Scenario: Today's cache expires after TTL
- **WHEN** the cached data for today is older than the TTL (default: 30 minutes)
- **THEN** the system SHALL treat it as expired and re-fetch from B3

#### Scenario: TTL is configurable
- **WHEN** the system is initialized with a custom TTL value
- **THEN** the system SHALL use that value instead of the default 30 minutes

### Requirement: Corrupted cache file handling
The system SHALL handle corrupted cache files gracefully.

#### Scenario: Corrupted JSON is deleted and refetched
- **WHEN** a cache file contains invalid JSON
- **THEN** the system SHALL delete the corrupted file, download fresh data from B3, and cache the new response

### Requirement: Force refresh bypasses cache
The system SHALL allow callers to bypass the cache and force a fresh download.

#### Scenario: Force refresh downloads even if cache is valid
- **WHEN** the caller passes `force=True`
- **THEN** the system SHALL skip cache lookup and download directly from B3, updating the cache afterward

### Requirement: Cache directory follows XDG specification
The system SHALL store cache files in an XDG-compliant directory.

#### Scenario: Linux uses XDG_CACHE_HOME
- **WHEN** the system runs on Linux
- **THEN** the cache SHALL be stored at `$XDG_CACHE_HOME/b3-selic-pre/rates/` (fallback: `~/.cache/b3-selic-pre/rates/`)

#### Scenario: Windows uses LOCALAPPDATA
- **WHEN** the system runs on Windows
- **THEN** the cache SHALL be stored at `%LOCALAPPDATA%/b3-selic-pre/cache/rates/`

#### Scenario: macOS uses Caches directory
- **WHEN** the system runs on macOS
- **THEN** the cache SHALL be stored at `~/Library/Caches/b3-selic-pre/rates/`

### Requirement: Automatic housekeeping of old cache files
The system SHALL periodically remove cache files older than a configurable threshold.

#### Scenario: Old cache files are removed during load
- **WHEN** the system successfully loads data for any date
- **THEN** the system SHALL check all cache files and remove those whose date is older than `max_age_days` (default: 365)

#### Scenario: max_age_days is configurable
- **WHEN** the system is initialized with a custom `max_age_days`
- **THEN** the system SHALL use that value instead of the default 365

#### Scenario: Corrupted filenames are ignored
- **WHEN** a filename in the cache directory does not match the YYYY-MM-DD format
- **THEN** the system SHALL silently skip it during housekeeping

### Requirement: CachedB3Client class
The system SHALL provide a `CachedB3Client` class that wraps B3 fetch functions with caching logic.

#### Scenario: CachedB3Client provides same interface as direct functions
- **WHEN** code uses `CachedB3Client.fetch_reference_rates(date)`
- **THEN** it SHALL return the same result as `b3_client.fetch_reference_rates(date)` with caching applied

#### Scenario: CachedB3Client handles historical fetch with per-date caching
- **WHEN** `CachedB3Client.fetch_historical_rates(base_date)` is called
- **THEN** each date SHALL be checked individually in cache before downloading

#### Scenario: CachedB3Client is used by both CLI and GUI
- **WHEN** the CLI or GUI requests data
- **THEN** they SHALL use `CachedB3Client` instead of calling `b3_client` functions directly

### Requirement: Cache source indicator
The system SHALL indicate whether data was served from cache or fetched from B3.

#### Scenario: Cache source shown in GUI status bar
- **WHEN** data is served from cache
- **THEN** the status bar SHALL display "Cache" followed by the date(s)
- **WHEN** data is fetched from B3
- **THEN** the status bar SHALL display "API B3", "Arquivo oficial B3", or "Histórico B3" accordingly
