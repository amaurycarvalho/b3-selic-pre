## Why

O aplicativo não exibe sua versão em lugar nenhum — nem na janela, nem no CLI. Com o workflow de release gerando executáveis versionados por tag, o usuário não tem como saber qual versão está rodando. Uma versão visível na barra de título e via `--version` dá confiança e ajuda no debugging.

## What Changes

- Adicionar constante `__version__` no topo de `b3_selic_pre.py`
- Exibir a versão na barra de título da janela: `"B3 SELIC Pré v<version>"`
- Adicionar flag `--version` ao argparse para exibir a versão no CLI

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability -->

### Modified Capabilities
- `desktop-rate-browser`: Adicionar requisito de exibição de versão na barra de título; adicionar requisito de flag `--version` no CLI

## Impact

- `b3_selic_pre.py`: ~3 linhas adicionadas (`__version__`, uso no `root.title()`, argumento `--version`)
- Nenhuma dependência nova
- Nenhuma mudança em CI, workflow ou outras specs
