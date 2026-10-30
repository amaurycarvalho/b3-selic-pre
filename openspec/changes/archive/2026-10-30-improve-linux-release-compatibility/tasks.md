# Tasks

## 1. Workflow de release

- [x] 1.1 Dividir o job `build` em `build-linux` e `build-desktop`, mantendo o upload/nomeação dos artefatos e o job `release` dependendo de ambos; verificar que o YAML continua válido e que `release` só roda após os dois builds.
- [x] 1.2 Configurar `build-linux` para rodar em `container: buildpack-deps:noble` e instalar `python3.12`, `python3.12-venv` e `python3.12-tk` dos repositórios oficiais antes do build; verificar que os comandos aparecem na ordem correta no workflow.
- [x] 1.3 Executar `make install` e `make build` no Linux com `PYTHON_CMD=python3.12`; verificar que o passo usa a venv criada com Python 3.12.
- [x] 1.4 Fixar os runners do release em `ubuntu-24.04`, `windows-2025` e `macos-26`; verificar que não resta nenhum label `*-latest` em `release.yml`.

## 2. Validação

- [x] 2.1 Validar a sintaxe do YAML e rodar `make lint` e `make complexity`; verificar que ambos terminam sem erro.
- [x] 2.2 (Manual) Disparar o release via `workflow_dispatch`, baixar `b3-selic-pre-linux` e executar em Ubuntu 24.04; verificar que inicia sem erro de `GLIBC` e que a GUI abre com o `tkinter` carregado.
