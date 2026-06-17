## 1. Implementação

- [x] 1.1 Adicionar `__version__ = "0.2.0"` no topo de `b3_selic_pre.py` (após os imports)
- [x] 1.2 Alterar `root.title("B3 SELIC Pré")` para `root.title(f"B3 SELIC Pré v{__version__}")`
- [x] 1.3 Adicionar argumento `--version` com `action="version"` no `parse_args()`
- [x] 1.4 Atualizar `CHANGELOG.md`: mover conteúdo de `[Unreleased]` para `[0.2.0]` e adicionar entrada sobre exibição de versão

## 2. Verificação

- [x] 2.1 Executar `pytest` e confirmar 38 testes passando (`38 passed`)
- [x] 2.2 Executar `python b3_selic_pre.py --version` e confirmar saída `b3-selic-pre 0.2.0`
- [x] 2.3 Verificar via `python3 -c "import b3_selic_pre; print(f'B3 SELIC Pré v{b3_selic_pre.__version__}')"`
