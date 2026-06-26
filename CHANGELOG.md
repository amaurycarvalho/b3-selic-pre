# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-06-26

### [improve-quiver-arrow-layout](openspec/changes/archive/2026-06-26-improve-quiver-arrow-layout/) Redesign quiver arrow layout with offset/step pattern to eliminate visual overlap

#### Changed

- Redesign quiver arrow placement to show at most one arrow per tick position, cycling through curve transitions by offset (offset 1, step 5)
- Apply the new layout to both `render_curve_evolution` (1-year intervals) and `render_detailed_evolution` (22 DU intervals)

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.6.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
