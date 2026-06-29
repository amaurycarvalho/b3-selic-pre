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

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.8.3...HEAD
[0.8.3]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.3

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
