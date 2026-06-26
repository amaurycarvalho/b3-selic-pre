# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [auto-analysis-commentary](openspec/changes/auto-analysis-commentary/) Rule-based inference engine that analyzes SELIC Pré rate curves and generates natural-language reports in a collapsible side panel

## [0.7.1] - 2026-06-26

### [clean-arch-pyproject](openspec/changes/archive/2026-06-26-clean-arch-pyproject/) Reestruturar monolito para Clean Architecture com src/ layout e pyproject.toml

#### Changed

- Decompor `b3_selic_pre.py` em pacote `src/b3_selic_pre/` com camadas domain, application, infrastructure, presentation
- Criar `pyproject.toml` unificando metadados, dependências e entry point — substitui `requirements.txt`
- Mover `icons/` para dentro do pacote como `package_data`
- Atualizar `b3-selic-pre.spec` para apontar para o novo entry point (`__main__.py`)
- Atualizar `Makefile` para usar `pip install -e .` e `python -m b3_selic_pre`
- Atualizar `.github/workflows/test.yml` e `release.yml` para o novo build
- Atualizar `README.md` com novos comandos de uso
- Atualizar skills OpenSpec (release-version, release-push) com novos paths
- Atualizar todos os imports e `mock.patch` nos testes (`tests/`)
- **BREAKING**: `python3 b3_selic_pre.py` → `python3 -m b3_selic_pre` (ou `b3-selic-pre` via entry point)

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.7.1...HEAD
[0.7.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.7.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
