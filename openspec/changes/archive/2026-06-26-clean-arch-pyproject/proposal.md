## Why

O projeto atual tem 1161 linhas em um único arquivo `b3_selic_pre.py`, sem separação entre domínio, aplicação, infraestrutura e apresentação. Não há `pyproject.toml` — usa `requirements.txt` + `Makefile` + spec PyInstaller separados, sem um sistema de build unificado. Isso dificulta manutenção, teste isolado e evolução futura.

## What Changes

- Decompor `b3_selic_pre.py` em pacote `src/b3_selic_pre/` com camadas **domain**, **application**, **infrastructure**, **presentation**
- Criar `pyproject.toml` unificando metadados, dependências e entry point — substitui `requirements.txt`
- Mover `icons/` para dentro do pacote como `package_data`
- Atualizar `b3-selic-pre.spec` para apontar para o novo entry point (`__main__.py`)
- Atualizar `Makefile` para usar `pip install -e .` e `python -m b3_selic_pre`
- Atualizar `.github/workflows/test.yml` e `release.yml` para o novo build
- Atualizar `README.md` com novos comandos de uso
- Atualizar skills OpenSpec (`release-version`, `release-push`) com novos paths
- Atualizar todos os imports e `mock.patch` nos testes (`tests/`)
- **BREAKING**: `python3 b3_selic_pre.py` → `python3 -m b3_selic_pre` (ou `b3-selic-pre` via entry point)

## Capabilities

### New Capabilities

- `package-structure`: Nova estrutura de pacote com Clean Architecture (`src/b3_selic_pre/`), `pyproject.toml`, e build unificado

### Modified Capabilities

<!-- Nenhuma capability existente tem requisitos alterados — apenas implementação reorganizada -->

## Impact

- **Arquivos removidos**: `b3_selic_pre.py`, `requirements.txt`
- **Arquivos criados**: `pyproject.toml`, `src/b3_selic_pre/` (12 módulos em 4 camadas)
- **Arquivos modificados**: `b3-selic-pre.spec`, `Makefile`, `README.md`, `.github/workflows/test.yml`, `.github/workflows/release.yml`, `.gitignore`, `.opencode/skills/release-version/SKILL.md`, `.opencode/skills/release-push/SKILL.md`, `.opencode/skills/release-push/release-push.sh`, `tests/test_b3_selic_pre.py`, `tests/test_b3_selic_pre_gui.py`
- **Dependências**: matplotlib, Pillow, pyxclip (inalteradas)
