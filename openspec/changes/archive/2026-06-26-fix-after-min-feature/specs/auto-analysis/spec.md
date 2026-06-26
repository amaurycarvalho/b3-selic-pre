## MODIFIED Requirements

### Requirement: AFTER_MIN_UP feature computation window
The system SHALL compute the `AFTER_MIN_UP` feature using only the recovery zone between the last occurrence of the global minimum and the global maximum. The window start SHALL be `last_min = max(i for i, r in enumerate(rates) if r == rates[min_idx])` — the LAST index where the rate equals the minimum value. When `max_idx > last_min`, the analysis window SHALL be `rates[last_min:max_idx+1]`. When `max_idx <= last_min`, `AFTER_MIN_UP` SHALL be False (no recovery zone exists).

The `after_min_ratio` SHALL be computed as `non_negative_deltas / len(deltas)` over this restricted window, where a delta is non-negative if `rates[k+1] - rates[k] >= 0`. Zero deltas SHALL count as recovery (rate did not decrease). The feature SHALL be True when `after_min_ratio >= config.recuperacao_min_ratio`.

#### Scenario: Valley with recovery then plateau
- **WHEN** min_idx=39, last_min=48, max_idx=138, and the recovery zone from last_min to max contains 90 deltas with 21 strictly positive and 66 zero (all >= 0)
- **THEN** after_min_ratio SHALL be 87/90 ≈ 0.97
- **AND** AFTER_MIN_UP SHALL be True (0.97 >= 0.80)

#### Scenario: Valley floor excluded from window
- **WHEN** the minimum value 14.03 appears at indices [39..48] (10 records)
- **THEN** last_min SHALL be 48 and the window SHALL start at index 48, excluding the 9 zero-deltas of the valley floor

### Requirement: AFTER_MAX_DOWN feature computation window
The system SHALL compute the `AFTER_MAX_DOWN` feature using only the descent zone between the last occurrence of the global maximum and the global minimum. The window start SHALL be `last_max = max(i for i, r in enumerate(rates) if r == rates[max_idx])`. When `min_idx > last_max`, the analysis window SHALL be `rates[last_max:min_idx+1]`. When `min_idx <= last_max`, `AFTER_MAX_DOWN` SHALL be False (no descent zone exists).

The `after_max_ratio` SHALL be computed as `non_positive_deltas / len(deltas)` over this restricted window, where a delta is non-positive if `rates[k+1] - rates[k] <= 0`. Zero deltas SHALL count as descent (rate did not increase). The feature SHALL be True when `after_max_ratio >= config.recuperacao_min_ratio`.

#### Scenario: Peak with descent
- **WHEN** last_max=25, min_idx=150, and the descent zone contains 124 deltas with 110 strictly negative and 10 zero (all <= 0)
- **THEN** after_max_ratio SHALL be 120/124 ≈ 0.97
- **AND** AFTER_MAX_DOWN SHALL be True (0.97 >= 0.80)
