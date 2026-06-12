## 1. Core Data Layer

- [x] 1.1 Extract B3 request payload construction into a reusable function
- [x] 1.2 Extract B3 HTTP fetch and JSON parsing into a reusable client function
- [x] 1.3 Normalize returned records to stable `day252`, `day360`, and `rate` fields
- [x] 1.4 Preserve command-line output using the refactored data layer

## 2. Desktop GUI

- [x] 2.1 Create a `tkinter` desktop entry point with date input, fetch button, status label, and results table
- [x] 2.2 Validate `YYYY-MM-DD` input before starting network requests
- [x] 2.3 Run B3 fetches without blocking the GUI event loop
- [x] 2.4 Render fetched rows in the table and clear stale rows for empty results
- [x] 2.5 Display loading, success, validation, empty-result, and request-failure states

## 3. Export and Copy

- [x] 3.1 Add tabular text or CSV formatting for displayed records
- [x] 3.2 Add copy-to-clipboard behavior for populated results
- [x] 3.3 Add CSV export behavior for populated results
- [x] 3.4 Show a no-data message when users copy or export with an empty table

## 4. Documentation and Verification

- [x] 4.1 Document how to run the CLI and desktop GUI
- [x] 4.2 Add focused tests for payload construction, record normalization, date validation, and export formatting where practical
- [x] 4.3 Manually verify the GUI query, error, copy, and export flows
