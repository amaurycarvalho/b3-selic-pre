## ADDED Requirements

### Requirement: Average rate computation from consolidated data
The system SHALL provide a function `average_rate_by_year(records)` that derives the arithmetic mean of `min_rate` and `max_rate` for each year from the output of `consolidate_by_year`.

#### Scenario: Average rate equals midpoint
- **WHEN** consolidated data contains `{year: 1, min_rate: 14.0, max_rate: 15.0}`
- **THEN** `average_rate_by_year` returns `{1: 14.5}`
