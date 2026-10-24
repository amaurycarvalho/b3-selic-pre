# Spec Delta

## MODIFIED Requirements

### Requirement: TTL for current date only
The system SHALL apply a configurable TTL (Time-To-Live) only to the current date's cached data.

#### Scenario: Past date cache is always valid
- **WHEN** the cache contains data for a past date (before today)
- **THEN** the system SHALL treat it as valid regardless of age

#### Scenario: Today's cache expires after TTL
- **WHEN** the cached data for today is older than the TTL (default: 6 hours)
- **THEN** the system SHALL treat it as expired and re-fetch from B3

#### Scenario: TTL is configurable
- **WHEN** the system is initialized with a custom TTL value
- **THEN** the system SHALL use that value instead of the default 6 hours
