## ADDED Requirements

### Requirement: Quality gate bloqueia release
O workflow de release SHALL executar o quality gate completo via `ci.yml` antes de construir qualquer binário. Um job `ci` que referencia `.github/workflows/ci.yml` via `workflow_call` deve ser executado antes do job `build`.

#### Scenario: CI passa, build prossegue
- **WHEN** o workflow de release é disparado (tag `v*` ou `workflow_dispatch`)
- **THEN** o job `ci` executa `ci.yml` com todos os checks de qualidade
- **THEN** se `ci` passa, o job `build` inicia em todas as plataformas
- **THEN** se `ci` passa, o job `release` publica os binários

#### Scenario: CI falha, release bloqueada
- **WHEN** o job `ci` falha em qualquer verificação (lint, teste, complexidade, duplicação, cobertura, segurança, mutação)
- **THEN** o job `build` NÃO é executado
- **THEN** o job `release` NÃO é executado
- **THEN** nenhum binário é publicado

## MODIFIED Requirements

### Requirement: Build executáveis multiplataforma
O sistema SHALL gerar executáveis do `b3-selic-pre` para Windows, Linux e macOS via PyInstaller em um workflow GitHub Actions, após aprovação do quality gate.

#### Scenario: Build em todos os OS
- **WHEN** o workflow é disparado E o job `ci` conclui com sucesso
- **THEN** o job `build` executa nos runners `ubuntu-latest`, `windows-latest` e `macos-latest`
- **THEN** cada runner executa `make install && make build`
- **THEN** o PyInstaller gera o executável no diretório `dist/`
- **THEN** o binário é renomeado com prefixo da plataforma (`b3-selic-pre-linux`, `b3-selic-pre-windows.exe`, `b3-selic-pre-macos`)

#### Scenario: Falha em um OS não bloqueia os demais
- **WHEN** o build falha em um runner específico
- **THEN** os demais runners continuam e produzem seus artefatos
- **THEN** o job `release` NÃO é executado (release depende de sucesso total)
