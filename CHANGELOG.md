# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-06-17

### Added

- Exibição da versão na barra de título da janela e flag `--version` no CLI

### Fixed

- Correção do glob de upload no workflow de release para anexar os binários à release (`b3-selic-pre-*/` → `b3-selic-pre-*/*`)
- Remoção do `b3-selic-pre.desktop` dos assets da release (continha caminhos absolutos locais)

## [0.2.0] - 2026-06-16

### Added

- GitHub Actions workflow for automated PyInstaller builds (Windows, Linux, macOS)
- GitHub Release publishing with binary assets
- PyInstaller `.spec` file for reproducible builds
- `CHANGELOG.md` for tracking version history
