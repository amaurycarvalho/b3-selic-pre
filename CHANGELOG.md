# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-10-30

### [improve-linux-release-compatibility](openspec/changes/archive/2026-10-30-improve-linux-release-compatibility/) Os binários Linux gerados no CI herdaram a glibc do runner móvel `ubuntu-latest` e passaram a exigir `GLIBC_2.42`, falhando em máquinas alvo mais antigas (o erro de `tkinter`/`Tkinter` era apenas o sintoma do `_tkinter` não carregar). O release precisa cobrir, no mínimo, Ubuntu 24.04 (glibc 2.39).

#### Added

- Construir o artefato Linux dentro de um container fixo baseado em Ubuntu 24.04 (`buildpack-deps:noble`, glibc 2.39), em vez de depender do SO do runner.
- Instalar Python 3.12 e Tk dentro do container a partir dos repositórios oficiais do Ubuntu (`python3.12`, `python3.12-venv`, `python3.12-tk`).

#### Changed

- Separar o job de build em `build-linux` (containerizado) e `build-desktop` (Windows/macOS).
- Fixar todos os runners do release em labels explícitos (`ubuntu-24.04`, `windows-2025`, `macos-26`), eliminando `*-latest`.
- Não adicionar job de smoke test (fora do escopo desta mudança).

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v1.1.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
