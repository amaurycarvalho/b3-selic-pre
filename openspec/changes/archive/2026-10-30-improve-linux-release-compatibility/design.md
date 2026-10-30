# Design

## Context

Ver `proposal.md` — Why. O release atual compila Linux diretamente no runner `ubuntu-latest` (`.github/workflows/release.yml`). Como o PyInstaller não empacota a glibc, o binário herda o piso do ambiente de build. O runner é um label móvel e já produziu artefatos exigindo `GLIBC_2.42`. O projeto exige Python >= 3.12 (`pyproject.toml`) e a UI usa `tkinter`/`tkcalendar`.

## Goals / Non-Goals

**Goals:**
- Tornar o piso de glibc do binário Linux determinístico e <= 2.39 (Ubuntu 24.04).
- Manter `tkinter` empacotado corretamente.
- Eliminar dependência de labels `*-latest` no workflow de release.

**Non-Goals:**
- Cobrir distribuições com glibc < 2.39 (ex.: Ubuntu 22.04, Debian 12).
- Adicionar job de smoke test do binário (fora do escopo solicitado).
- Alterar código Python, dependências ou `b3-selic-pre.spec`.

## Decisions

### Build Linux em container Ubuntu 24.04

**Decisão:** executar o job `build-linux` em um container `buildpack-deps:noble` (Ubuntu 24.04, glibc 2.39), fixado por label explícito.

**Por quê:** o container define o piso de glibc independente do runner; `buildpack-deps:noble` já traz `git`, `gcc` e `make`, necessários para `actions/checkout` e para o build, e alinha o ambiente ao piso mínimo suportado.

**Alternativas consideradas:**
- `python:3.12-bookworm` (Debian 12, glibc 2.36): geraria um piso inferior ao mínimo declarado e foge do Ubuntu LTS usado como referência de compatibilidade.
- Runner `ubuntu-24.04` com `setup-python`: também teria glibc 2.39, mas o piso voltaria a depender da imagem do runner.
- `manylinux_2_28`/`python-build-standalone`: permitiria piso menor (glibc 2.17–2.28), mas o CPython do manylinux é estático (incompatível com o requisito de `libpython` compartilhada do PyInstaller) e o standalone não foi validado neste projeto; complexidade desnecessária para o alvo definido.

### Python 3.12 e Tk dos repositórios oficiais

**Decisão:** instalar `python3.12`, `python3.12-venv` e `python3.12-tk` dos repositórios oficiais do Ubuntu 24.04 e criar a venv com `make PYTHON_CMD=python3.12`.

**Por quê:** Ubuntu 24.04 já traz Python 3.12 como padrão; `python3.12-tk` fornece o módulo `_tkinter` e a `libpython3.12` compartilhada exigida pelo PyInstaller, sem depender de PPA externo.

**Alternativas consideradas:**
- PPA deadsnakes: desnecessário, pois o Python 3.12 já está nos repositórios do Ubuntu 24.04.
- Compilar CPython 3.12 do fonte com `--enable-shared` e `tk-dev`: adiciona tempo e complexidade ao CI sem ganho.

### Separar `build-linux` e `build-desktop`

**Decisão:** dividir o antigo job `build` em `build-linux` (com `container:`) e `build-desktop` (matriz Windows/macOS).

**Por quê:** o GitHub Actions não permite aplicar `container:` condicionalmente por item de matriz; separar mantém Windows/macOS nos runners hospedados e Linux no container.

### Fixar labels dos runners

**Decisão:** usar `ubuntu-24.04`, `windows-2025` e `macos-26` em vez de `*-latest`.

**Por quê:** labels móveis mudam o SO silenciosamente; fixar evita regressões futuras de compatibilidade e mantém o ambiente de build reproduzível.

## Risks / Trade-offs

- [Imagem `buildpack-deps:noble` sofre atualizações de patch] → glibc permanece 2.39 na série noble; patches não elevam o piso de compatibilidade.
- [Ubuntu 24.04 chega ao fim de vida] → quando 24.04 não for mais necessário como alvo, o container pode ser atualizado; o piso de 2.39 é intencional.
- [Build mais lento] → instalar Python/Tk e dependências no container adiciona alguns minutos; aceitável para um release.
- [Sem smoke test] → a compatibilidade é garantida pelo ambiente de build, não por uma execução automatizada no alvo (explicitamente fora do escopo).

## Migration Plan

1. Mesclar a alteração em `main`.
2. Disparar o release (`workflow_dispatch` com tag de teste ou push de tag `v*`).
3. Baixar `b3-selic-pre-linux` e validar em Ubuntu 24.04.
4. Rollback: reverter o commit e reexecutar o workflow; nenhum dado ou migração é afetado.
