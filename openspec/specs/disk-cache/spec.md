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

### Requirement: Only complete, non-empty results are cached

The system SHALL write a cache entry only when the fetched result is non-empty and has passed the completeness validation for its source. An empty result or a partial result SHALL NOT be written to the cache, even when the request used `force=True`.

#### Scenario: Empty result is not cached
- **WHEN** the B3 returns an empty result after all retries
- **THEN** no cache entry is created or updated for that date

#### Scenario: Partial GetList result is not cached
- **WHEN** the collected record count differs from `page.totalRecords`
- **THEN** the partial result is not written to the cache

#### Scenario: Complete result is cached
- **WHEN** the result is non-empty and passes the completeness validation
- **THEN** the result is written to the cache as before

### Requirement: Empty or incomplete cache entries are treated as misses

The system SHALL treat an existing cache entry as a miss when its record list is empty or when its completeness metadata marks it as incomplete. A miss SHALL delete the invalid entry and fetch the date again. Cache entries written before this change, which have no completeness metadata, SHALL be invalidated and re-fetched once so that previously truncated curves are not served indefinitely.

#### Scenario: Empty cached record list is a miss
- **WHEN** the cache contains an entry whose record list is empty
- **THEN** the system deletes that entry and fetches the date again

#### Scenario: Incomplete cached entry is a miss
- **WHEN** the cache contains an entry marked as incomplete
- **THEN** the system deletes that entry and fetches the date again

#### Scenario: Legacy cache entry is invalidated
- **WHEN** the cache contains an entry without completeness metadata
- **THEN** the system treats it as a miss, deletes it and fetches the date again

#### Scenario: Force refresh does not persist an empty result
- **WHEN** the caller requests a forced refresh and the fresh result is empty or partial
- **THEN** the previous valid cache entry is not overwritten with the empty or partial result

### Requirement: Current-date results are cached

The system SHALL cache a successful, non-empty result for the current date using the configured TTL. Subsequent requests for the current date within the TTL SHALL be served from the cache without contacting the B3 source. When the current-date cache entry is older than the TTL, the system SHALL discard it and fetch the date again.

#### Scenario: Today's GetList result is cached
- **WHEN** the current date is fetched successfully via `GetList` and the result is complete
- **THEN** the result is written to the cache with the configured TTL

#### Scenario: Next request uses today's cache
- **WHEN** the current date is requested again before the TTL expires
- **THEN** the system returns the cached records and does not call `GetList`

#### Scenario: Expired current-date cache is refreshed
- **WHEN** the current-date cache entry is older than the TTL
- **THEN** the system deletes it and fetches the current date from `GetList` again

### Requirement: Leitura de cache sem mutação

O sistema SHALL oferecer leitura do cache em modo somente leitura. Nesse modo, uma entrada ausente, vencida, corrompida ou incompleta SHALL ser tratada como miss, sem remover, renomear ou alterar o arquivo.

A leitura somente leitura NÃO SHALL acessar a rede nem disparar download.

#### Scenario: Entrada corrompida é miss sem remoção

- **WHEN** um arquivo de cache contém JSON inválido em modo somente leitura
- **THEN** a leitura SHALL devolver miss
- **THEN** o arquivo SHALL permanecer no disco

#### Scenario: Entrada incompleta é miss

- **WHEN** uma entrada não satisfaz os metadados de completude
- **THEN** a leitura SHALL devolver miss
- **THEN** o arquivo NÃO SHALL ser removido

#### Scenario: Leitura não acessa a rede

- **WHEN** uma data não está no cache em modo somente leitura
- **THEN** a leitura SHALL devolver miss
- **THEN** nenhuma requisição SHALL ser feita à B3

### Requirement: Escrita atômica de cache

A gravação de uma entrada de cache SHALL ser atômica. Um leitor concorrente SHALL ver a entrada anterior completa ou a nova entrada completa, nunca um conteúdo parcial.

A escrita atômica SHALL preservar a validação de completude e a política de não gravar resultados vazios ou parciais.

#### Scenario: Leitor concorrente não vê conteúdo parcial

- **WHEN** uma entrada de cache está sendo gravada enquanto outro processo lê a mesma data
- **THEN** o leitor SHALL ver a entrada anterior ou a nova
- **THEN** o leitor NÃO SHALL interpretar a entrada como corrompida por causa da escrita

#### Scenario: Resultado vazio não é gravado

- **WHEN** uma carga termina sem registros
- **THEN** nenhuma entrada de cache SHALL ser criada ou substituída
