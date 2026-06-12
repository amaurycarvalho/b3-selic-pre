## Why

The project currently exposes B3 SELIC reference-rate data only through a small script with a hardcoded date and terminal output. A desktop GUI will make the data easier to query, inspect, copy, and export without requiring users to edit Python code.

## What Changes

- Add a desktop user interface for querying B3 SELIC Pré reference rates by date.
- Display returned rates in a tabular view with day-count columns and rate values.
- Show clear loading, success, empty-result, and error states for B3 API requests.
- Allow users to copy or export the displayed results for downstream analysis.
- Refactor the current script logic into reusable data-fetching code that can be shared by the GUI and command-line entry points.

## Capabilities

### New Capabilities
- `desktop-rate-browser`: Desktop GUI for selecting a reference date, fetching B3 SELIC Pré rates, viewing results, and exporting tabular data.

### Modified Capabilities

None.

## Impact

- Affected code: `b3_selic_pre.py` will need to separate fetch/parsing logic from presentation concerns.
- New code: desktop GUI module or entry point, plus tests around fetch/presentation boundaries where practical.
- Dependencies: may introduce a GUI dependency if a toolkit outside the Python standard library is selected.
- External systems: continues to use the B3 reference rates endpoint currently called by the project.
