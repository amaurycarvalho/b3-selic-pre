# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Makefile com targets `install`, `build` e `clean` para builds locais reproduzíveis
- Workflow de release agora usa `make install && make build` em vez de comandos inline
- README com seções de instalação (manual, Makefile, binário pré-compilado) e uso nas três modalidades

### Changed

- Versão bumpada para `0.2.3`
- Makefile: build via `.venv/` local em vez de pip system-wide, evitando PEP 668

### Fixed

- `b3-selic-pre.spec`: adicionados hidden imports `PIL._tkinter_finder`, `matplotlib` e `matplotlib.figure` para resolver erros de módulo não encontrado no executável gerado
- `copy_chart`: substituída implementação com subprocessos + threads por `pyxclip` (Rust, zero dependências externas), eliminando travamentos do `xclip` e simplificando o código

## [0.2.2] - 2026-06-17

### Fixed

- Renomeação dos binários com prefixo da plataforma (`b3-selic-pre-linux`, `b3-selic-pre-windows.exe`, `b3-selic-pre-macos`) para evitar colisão de nomes no upload da release

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
