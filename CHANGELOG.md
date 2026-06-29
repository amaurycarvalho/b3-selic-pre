# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.3] - 2026-06-29

### [gui-as-default](openspec/changes/archive/2026-06-29-gui-as-default/) GUI becomes default invocation mode; --today flag added

#### Added

- `--today` flag to print today's reference rates as CSV

#### Changed

- **BREAKING**: `b3-selic-pre` (no arguments) now opens the GUI instead of printing CSV to stdout

### [progress-single-fetch](openspec/changes/archive/2026-06-29-progress-single-fetch/) Determinate progress bar for single-date fetch

#### Added

- `fetch_reference_rates()` gains optional `progress_callback` parameter for page-by-page progress reporting
- Pagination metadata (`totalCount`) extracted from B3 API response for total page calculation

#### Changed

- Single-date fetch progress bar switches from indeterminate to determinate after first page reveals total pages (hybrid approach)

## [0.8.1] - 2026-06-28

### [ui-reorganization](openspec/changes/archive/2026-06-28-ui-reorganization/) UI reorganization with DateEntry, icon buttons, compact layout and frozen title

#### Added

- Add `tkcalendar` to project dependencies

#### Changed

- Replace ttk.Entry, calendar popup and custom DatePicker with tkcalendar.DateEntry
- Change date label from "Data (YYYY-MM-DD):" to "Data de referência:"
- Replace text buttons with 24x24 icon images
- Show content-loading icon on fetch button during loading; move "Buscando…" text to statusbar
- Move "Copiar dados" button to top frame
- Move "Copiar gráfico" button into matplotlib toolbar
- Merge radiobuttons/checkboxes and stats summary into a single reduced-height row
- Display stats as compact pipe-separated format on right side of control row
- Freeze window title (remove dynamic title updates on data load)

#### Removed

- Remove "Exportar PNG" button (redundant with native matplotlib toolbar save button)

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.8.3...HEAD
[0.8.3]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.3
[0.8.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
