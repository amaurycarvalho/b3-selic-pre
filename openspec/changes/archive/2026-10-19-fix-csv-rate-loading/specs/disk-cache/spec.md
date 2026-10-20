## ADDED Requirements

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
