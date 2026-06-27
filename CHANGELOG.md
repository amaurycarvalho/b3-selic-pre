# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2026-06-27

### [ux-refinements](openspec/changes/archive/2026-06-27-ux-refinements/) 26 UI refinements for professional-quality feedback, persistence, and controls

#### Added
- Add determinate/indeterminate progress bars to the statusbar
- Highlight date entry in red on validation failure
- Add placeholder text to date entry
- Add "Hoje" button to reset date to today
- Add tooltips to all interactive controls
- Show data source and last update time in statusbar
- Persist last used date and user preferences to XDG config file
- Add keyboard shortcuts (Ctrl+C, Ctrl+Shift+C, Ctrl+S, F5, Ctrl+E, Ctrl+L)
- Show quick statistics row above chart
- Show placeholder text on empty chart ("Nenhum dado carregado")
- Temporarily show confirm message on copy then revert to prior status
- Add ttk.Separator between top/middle/bottom layout sections
- Add headers and rich-text formatting to analysis panel
- Automatically disable/enable controls based on available data context

#### Changed
- Block all controls during loading and show wait cursor
- Prefix status messages with Unicode icons per severity
- Toggle "Buscar" button text to "Buscando…" during fetch
- Update window title with loaded data context
- Improve export feedback with full file path
- Replace fixed-width sidebar with ttk.PanedWindow for resizable analysis panel

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
