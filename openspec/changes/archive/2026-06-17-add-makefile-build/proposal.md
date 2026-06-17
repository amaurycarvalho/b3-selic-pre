## Why

Centralizar a lógica de build do PyInstaller em um Makefile, eliminando a duplicação entre CI e desenvolvimento local. Atualmente os comandos de build estão hardcoded no workflow GitHub Actions, impossibilitando builds locais reproduzíveis sem copiar comandos manualmente. Além disso, unifica a instalação de dependências Python em um único target.

## What Changes

- Criar `Makefile` com targets `install`, `build` e `clean`
- Atualizar `.github/workflows/release.yml` para usar `make install` e `make build` em vez de comandos inline
- Bump da versão de `0.2.2` para `0.2.3`
- Adicionar `CHANGELOG.md` com entry para a mudança
- Adicionar hidden imports (`PIL._tkinter_finder`, `matplotlib`, `matplotlib.figure`, `pyxclip`) no `b3-selic-pre.spec` para corrigir erros em runtime
- Substituir lógica de clipboard do `copy_chart` (subprocessos + threads + xclip/ctypes/osascript) pelo `pyxclip` (Rust, zero dependências externas)
- Adicionar `pyxclip>=0.2.0` ao `requirements.txt`
- Atualizar `README.md` com instruções de instalação (manual, Makefile, binário pré-compilado) e uso nas três modalidades

## Capabilities

### New Capabilities
- `local-build`: Habilidade de executar o build PyInstaller localmente via Makefile, sem depender do CI

### Modified Capabilities
- `release-automation`: O passo de build no workflow deixa de usar comandos inline e passa a delegar ao Makefile (`make install` + `make build`). Dependências de sistema (`python3-tk`) e renomeação do binário permanecem no workflow por serem específicas do CI.

## Impact

- `Makefile` (novo) na raiz do projeto
- `.github/workflows/release.yml` — substitui comandos inline por `make install` + `make build`
- `b3_selic_pre.py` — bump `__version__` para `0.2.3`
- `CHANGELOG.md` — nova entrada unreleased
