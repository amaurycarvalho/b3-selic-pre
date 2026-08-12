## Why

`make test` (256 tests) leva ~51s, dos quais ~50s vêm de apenas 22 testes de GUI (`tests/test_b3_selic_pre_gui.py`). Cada teste reconstrói uma aplicação Tk inteira no `setUp` (~2,6s por app), mesmo quando só verifica o estado inicial de um widget. Isso torna o loop de desenvolvimento lento e encarece cada execução da quality gate.

## What Changes

- Reutilizar uma única instância de `tk.Tk` + `SelicPreApp` por classe de teste (`setUpClass`/`tearDownClass`), com reset de estado em `setUp`, em vez de reconstruir o app a cada teste.
- Isolar os 3 testes de atalho desktop (que dependem do mock de `shortcut_exists` na construção) para reutilizar 2 apps compartilhados (um com atalho, um sem) em vez de criar um app novo por teste.
- Introduzir um *seam* opcional na construção do app para permitir injetar um widget de data mais barato que `tkcalendar.DateEntry` nos testes.
- Manter comportamento e cobertura de teste equivalentes; nenhuma mudança de funcionalidade de produto.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma.

## Impact

- `tests/test_b3_selic_pre_gui.py`: reestruturação dos testes (sem remover casos).
- `src/b3_selic_pre/presentation/gui/app.py`: possível *seam* de injeção de widget de data (sem mudança de comportamento em produção).
- Tempo esperado de `make test`: ~51s → ~7s (≈7× mais rápido).
- Sem impacto em APIs públicas, dependências ou sistemas externos.
