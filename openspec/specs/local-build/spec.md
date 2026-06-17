## Purpose

Permitir que desenvolvedores executem o build PyInstaller localmente de forma padronizada via Makefile, sem depender do CI do GitHub Actions.

## Requirements

### Requirement: Build local com Makefile

O projeto SHALL disponibilizar um `Makefile` na raiz com targets para instalação de dependências e build do executável via PyInstaller.

#### Scenario: Instalação de dependências

- **WHEN** o desenvolvedor executa `make install`
- **THEN** as dependências listadas em `requirements.txt` são instaladas via pip
- **THEN** o `pyinstaller` é instalado via pip

#### Scenario: Build do executável

- **WHEN** o desenvolvedor executa `make build`
- **THEN** o PyInstaller é executado com o arquivo `b3-selic-pre.spec`
- **THEN** o executável é gerado no diretório `dist/`

#### Scenario: Clean de artefatos de build

- **WHEN** o desenvolvedor executa `make clean`
- **THEN** os diretórios `dist/`, `build/` e `__pycache__/` são removidos
