## MODIFIED Requirements

### Requirement: Build executáveis multiplataforma

O sistema SHALL gerar executáveis do `b3-selic-pre` para Windows, Linux e macOS via Makefile + PyInstaller em um workflow GitHub Actions.

#### Scenario: Build em todos os OS

- **WHEN** o workflow é disparado
- **THEN** o job `build` executa nos runners `ubuntu-latest`, `windows-latest` e `macos-latest`
- **THEN** cada runner executa `make install && make build`
- **THEN** o PyInstaller gera o executável no diretório `dist/`
- **THEN** o binário é renomeado com prefixo da plataforma (`b3-selic-pre-linux`, `b3-selic-pre-windows.exe`, `b3-selic-pre-macos`)
