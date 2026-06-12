## Context

The project currently consists of a single Python script that constructs a B3 reference-rates request, calls the remote endpoint, parses JSON, and prints selected fields to stdout. The date is hardcoded, and fetching, parsing, and presentation are all coupled in one file.

The desktop GUI should make the existing workflow accessible without requiring code edits. Because the codebase is intentionally small, the first design should keep dependencies and architectural ceremony low while leaving room for future packaging or toolkit changes.

## Goals / Non-Goals

**Goals:**
- Separate B3 data access from command-line or GUI presentation.
- Provide a desktop window where users can enter/select a date and fetch SELIC Pré rates.
- Display results in a readable table with user-facing feedback for loading, errors, and empty results.
- Support copying/exporting displayed data in a simple tabular format.
- Keep the implementation lightweight and maintainable for a small Python project.

**Non-Goals:**
- Building a web application or hosted service.
- Supporting multiple B3 datasets beyond SELIC Pré reference rates.
- Adding local persistence, authentication, or background scheduling.
- Producing installer packages in the initial implementation.

## Decisions

### Use a small layered structure

Refactor the current script into three concerns:

- Data client: builds the B3 request, fetches JSON, validates expected fields, and returns normalized records.
- Presentation utilities: format records for CLI display, clipboard text, or CSV export.
- GUI entry point: owns window state, user input, table rendering, and user actions.

This avoids duplicating network logic between CLI and GUI while keeping the project easy to understand.

Alternative considered: keep all GUI logic in the existing script. This is faster initially but would preserve the current coupling and make tests harder.

### Prefer `tkinter` for the MVP

Use Python's standard-library `tkinter` widgets for the first desktop GUI. The current app needs a date input, button, status text, table, and export actions; those are well within `tkinter`'s range.

Alternative considered: PySide6 or customtkinter. They can provide a more polished UI, but they introduce external dependencies and packaging complexity before the core workflow is proven.

### Keep the initial date input text-based

Use a validated `YYYY-MM-DD` date field rather than a calendar picker in the MVP. This keeps the toolkit surface simple and avoids a third-party date-picker dependency.

Alternative considered: add a calendar selector immediately. This improves ergonomics, but it is not necessary for the first usable GUI and can be added later.

### Run network requests without freezing the window

The GUI should execute B3 requests asynchronously relative to the UI event loop, then marshal results back to the main thread before updating widgets. This prevents the desktop window from appearing hung during network latency or endpoint failures.

Alternative considered: perform requests directly in the button handler. That is simpler but creates a poor UX if the B3 endpoint is slow.

### Export plain CSV from the displayed records

CSV export should reflect the currently displayed rows and include stable headers for `day252`, `day360`, and `rate`. This keeps the export aligned with what the user inspected.

Alternative considered: export raw API JSON. Raw JSON is useful for debugging but less friendly for spreadsheet analysis.

## Risks / Trade-offs

- B3 endpoint changes or downtime → isolate request/parse logic and show actionable GUI errors instead of crashing.
- `tkinter` visual polish is limited → accept a practical MVP now and leave toolkit replacement possible behind separated data logic.
- Threading can introduce UI update bugs → restrict widget updates to the GUI main thread.
- Date format mistakes are likely → validate input before requests and show an inline message.
- CSV locale expectations may vary → use a predictable CSV format first and avoid altering numeric values returned by B3.

## Migration Plan

1. Extract the existing B3 request logic into reusable functions while preserving current CLI behavior.
2. Add GUI code that calls the reusable functions.
3. Add export/copy helpers that operate on normalized records.
4. Document how to launch the GUI and CLI.

Rollback is straightforward: keep the original CLI pathway working independently from the GUI entry point.

## Open Questions

- Should the GUI default date be today's date or the latest known business date?
- Should packaging into a standalone executable be a follow-up change?
- Should future versions support additional B3 reference-rate datasets?
