## Why

The project currently exposes B3 SELIC pré reference rates only as a command-line script with a hard-coded query date. A small UI would make the data easier to inspect, refresh, and use without editing Python source.

## What Changes

- Add a browser-based user interface for consulting B3 SELIC pré rates.
- Allow users to select a reference date and request the corresponding rates.
- Display returned rate rows in a readable table with day-count columns and rate values.
- Show loading, empty, and error states when fetching or rendering data.
- Refactor the current fetching logic so it can be reused by the UI entry point instead of living only in top-level script execution.

## Capabilities

### New Capabilities

- `rate-query-ui`: Covers user-facing interaction for selecting a date, fetching B3 SELIC pré rates, and viewing results in a browser UI.

### Modified Capabilities

- None.

## Impact

- Affects `b3_selic_pre.py` by separating reusable B3 request logic from direct console printing.
- Adds UI-serving code and static assets or templates, depending on the chosen lightweight Python web approach.
- Introduces runtime behavior for local browser access while preserving CLI-oriented rate retrieval where practical.
