# Proposal

## Why

Os binários Linux gerados no CI herdaram a glibc do runner móvel `ubuntu-latest` e passaram a exigir `GLIBC_2.42`, falhando em máquinas alvo mais antigas (o erro de `tkinter`/`Tkinter` era apenas o sintoma do `_tkinter` não carregar). O release precisa cobrir, no mínimo, Ubuntu 24.04 (glibc 2.39).

## What Changes

- Construir o artefato Linux dentro de um container fixo baseado em Ubuntu 24.04 (`buildpack-deps:noble`, glibc 2.39), em vez de depender do SO do runner.
- Instalar Python 3.12 e Tk dentro do container a partir dos repositórios oficiais do Ubuntu (`python3.12`, `python3.12-venv`, `python3.12-tk`).
- Separar o job de build em `build-linux` (containerizado) e `build-desktop` (Windows/macOS).
- Fixar todos os runners do release em labels explícitos (`ubuntu-24.04`, `windows-2025`, `macos-26`), eliminando `*-latest`.
- Não adicionar job de smoke test (fora do escopo desta mudança).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `release-automation`: ambiente de build Linux, labels dos runners e dependências de sistema do Linux passam a garantir piso de glibc 2.39.

## Impact

- `.github/workflows/release.yml` (build Linux, matriz desktop, labels dos runners).
- Compatibilidade do artefato Linux: glibc >= 2.39 (Ubuntu 24.04+).
- Sem mudanças em código Python, `b3-selic-pre.spec`, dependências ou banco de dados.
