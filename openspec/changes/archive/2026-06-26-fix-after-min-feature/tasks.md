## 1. Modify AFTER_MIN_UP

- [x] 1.1 In `_features.py`, change `AFTER_MIN_UP` window from `rates[min_idx:]` to `rates[min_idx:max_idx+1]` when `max_idx > min_idx`
- [x] 1.2 Add guard: if `max_idx <= min_idx` or window has < 2 points, set `after_min_deltas = []` resulting in `after_min_ratio = 0.0` and `AFTER_MIN_UP = False`

## 2. Modify AFTER_MAX_DOWN

- [x] 2.1 In `_features.py`, change `AFTER_MAX_DOWN` window from `rates[max_idx:]` to `rates[max_idx:min_idx+1]` when `min_idx > max_idx`
- [x] 2.2 Add guard: if `min_idx <= max_idx` or window has < 2 points, set `after_max_deltas = []` resulting in `after_max_ratio = 0.0` and `AFTER_MAX_DOWN = False`

## 3. Tests

- [x] 3.1 Update `test_valley_early` — verify AFTER_MIN_UP uses restricted window (curve with valley, recovery, then long plateau shows True)
- [x] 3.2 Update `test_peak_early` — verify AFTER_MAX_DOWN uses restricted window
- [x] 3.3 Add test: AFTER_MIN_UP is True for valley+recovery+plateau curve (the test data that failed before)
- [x] 3.4 Add test: AFTER_MIN_UP is False when max_idx <= min_idx
- [x] 3.5 Add test: AFTER_MAX_DOWN is False when min_idx <= max_idx
- [x] 3.6 Verify existing VALE/PICO tests still pass

## 4. Verification

- [x] 4.1 Run full test suite: `python -m pytest tests/ -v`
- [x] 4.2 Verify the problematic curve now produces VALE classification
