# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.4] - 2026-06-29

### [fix-shortcut-detection](openspec/changes/archive/2026-06-29-fix-shortcut-detection/) Fix shortcut detection to check both Desktop and applications paths

#### Fixed

- `shortcut_exists()` now checks both `~/Desktop/` and `~/.local/share/applications/` instead of only the applications entry
- "Criar Atalho Desktop" button now appears whenever either shortcut is missing (instead of only when applications entry is missing)

#### Changed

- Update `shortcut-installer` spec to reflect the corrected dual-path detection behavior

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.8.4...HEAD
[0.8.4]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.4

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
