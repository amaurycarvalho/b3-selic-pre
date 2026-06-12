## 1. Refactor Rate Retrieval

- [ ] 1.1 Move B3 payload encoding and URL construction into reusable functions
- [ ] 1.2 Add a function that fetches and returns normalized rate rows for a given date
- [ ] 1.3 Guard CLI execution behind a main entry point while preserving console output
- [ ] 1.4 Add local validation for `YYYY-MM-DD` reference dates

## 2. Add Local UI Service

- [ ] 2.1 Add a standard-library HTTP server entry mode for local browser use
- [ ] 2.2 Implement a JSON endpoint that accepts a date and returns `results`
- [ ] 2.3 Return clear client errors for invalid dates
- [ ] 2.4 Return safe server errors when B3 retrieval fails

## 3. Build Browser Interface

- [ ] 3.1 Add an HTML UI with a date input and fetch action
- [ ] 3.2 Render `day252`, `day360`, and `rate` values in a results table
- [ ] 3.3 Show loading state and prevent duplicate in-flight submissions
- [ ] 3.4 Show empty-results and error messages

## 4. Verify Behavior

- [ ] 4.1 Verify CLI output still prints B3 rows
- [ ] 4.2 Verify the UI can fetch and render rows for a valid date
- [ ] 4.3 Verify invalid date input is rejected before calling B3
- [ ] 4.4 Verify failed B3 retrieval displays a safe error response
