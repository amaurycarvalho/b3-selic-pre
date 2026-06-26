# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [auto-analysis-commentary](openspec/changes/auto-analysis-commentary/) Rule-based inference engine that analyzes SELIC Pré rate curves and generates natural-language reports in a collapsible side panel

## [0.7.0] - 2026-06-26

### [grafico-3d-evolucao-curva](openspec/changes/archive/2026-06-26-grafico-3d-evolucao-curva/) 3D surface visualization of curve evolution

#### Added

- Add a "3D" checkbox alongside the existing "Evolução da curva" checkbox in the GUI (disabled when evolution is OFF)
- When evolution is ON and 3D is ON, render the 5 curves as a 3D surface plot using `plot_surface` instead of the standard 2D line chart
- The 3D view works with both "Detalhado" and "Consolidado" radio states — raw rate data or yearly averages
- Each curve occupies a distinct Z position (today=0, 28d ago=4)
- The 5 individual curves are drawn as black lines overlaid on the surface, with decreasing linewidth (today thickest, oldest thinnest)
- Surface uses a unified colormap (RdYlGn_r — red=high rate, yellow=mid, green=low) where color represents rate magnitude
- Requires `mpl_toolkits.mplot3d` for 3D projection support

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.7.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
