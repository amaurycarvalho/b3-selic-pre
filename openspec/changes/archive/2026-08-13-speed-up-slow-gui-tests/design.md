## Context

`make test` executa 256 testes em ~51s. O perfil (`pytest --durations`) mostra que os 22 testes de `tests/test_b3_selic_pre_gui.py` concentram ~50s. O `setUp` da classe `SelicPreAppTest` reconstrói uma aplicação Tk completa a cada teste (`tk.Tk()` + `SelicPreApp` + matplotlib TkAgg canvas + `tkcalendar.DateEntry` + ícones). Um perfil com `cProfile` de uma única construção mediu ~2,6s, dominado por:

| Componente | Custo |
|---|---|
| `tkcalendar.DateEntry` (`dateentry` + `calendar_` + `_setup_style`) | ~1,5s |
| matplotlib text metrics (`get_text_width_height_descent` via `render_chart`) | ~1,5s |
| `tk.Tk()` | ~0,6s |
| árvore de widgets + `root.destroy()` | ~0,6s |

Os 3 testes de atalho (`_make_app_with_shortcut`) constroem um **segundo** app cada um, por isso aparecem no topo da lista (~3s).

## Goals / Non-Goals

**Goals:**
- Reduzir `make test` de ~51s para ~7s (≈7×).
- Reduzir o teste individual mais lento de ~3,5s para <1s.
- Manter cobertura e semântica dos 22 casos de GUI.

**Non-Goals:**
- Não alterar comportamento de produto (nenhuma funcionalidade muda).
- Não trocar o backend matplotlib dos testes de GUI (o canvas TkAgg é parte do que está sendo testado).
- Não paralelizar (`pytest-xdist`) — incompatível com um único display Tk e com o cache de fontes/matplotlib.

## Decisions

### D1 — Reutilizar um único app por classe via `setUpClass`/`tearDownClass`

Construir `root` + `SelicPreApp` uma única vez por classe e resetar o estado mutável em `setUp` com um helper `_reset_app_state()`.

**Alternativa considerada:** `setUpClass` que reconstrói o app em cada teste. Rejeitada — é exatamente o custo que queremos eliminar.

**Racional:** a esmagadora maioria dos testes apenas inspeciona o estado inicial e então muta `records`/`historical_data`/variáveis de visualização. O custo está na construção, não na lógica do teste.

`_reset_app_state()` deve restaurar:
- `records = []`, `historical_data = None`, `_data_source = ""`, `_historical_fetching = False`, `_last_reference_date = None`
- `view_var = "raw"`, `evolution_var = False`, `var_3d = False`, `sidebar_var = False`
- `date_var = default_reference_date()`, `status_var` para o texto inicial
- `cb_3d` para `DISABLED`, sidebar recolhida
- `figure` limpo (ou re-render de um gráfico vazio via `render_chart(self.figure, [])`)
- `_update_button_states()`

### D2 — Isolar os 3 testes de atalho em uma classe com 2 apps compartilhados

O estado do botão de atalho é decidido em tempo de construção (`shortcut_exists()` em `_build_top_bar`), então não pode ser resetado no app compartilhado do D1. Criar uma classe separada `SelicPreAppShortcutTest` com dois apps construídos em `setUpClass`: um com `shortcut_exists` → `False` (botão presente) e outro com → `True` (botão ausente). Os 3 testes reutilizam esses dois apps.

**Alternativa considerada:** testar `_build_top_bar` isoladamente com um root espião. Rejeitada por agora — exigiria refatorar a construção em unidades menores, o que aumenta o risco; reutilizar 2 apps já elimina ~80% do custo desses testes.

### D3 — Seam para injetar um widget de data mais barato (opcional, secundário)

`tkcalendar.DateEntry` é o maior custo individual (~1,5s). Introduzir um ponto de extensão em `app.py` — por exemplo um atributo de classe `_date_entry_factory = DateEntry` ou um método `_create_date_entry(top_frame, ...)` — para que os testes possam injetar `ttk.Entry` (ou um widget simples) quando a seleção de data não é o foco.

**Racional:** mesmo após D1/D2 o app é construído 3 vezes (1 no D1 + 2 no D2), e o custo do `DateEntry` (~1,5s) permanece nesses builds. O *seam* corta esse custo sem mudar o caminho de produção.

**Trade-off:** toca código de produção. Mitigação: manter o default igual ao comportamento atual e cobrir o caminho de produção com o teste de GUI existente que usa a data (`test_invalid_date_shows_validation_without_fetching`).

## Risks / Trade-offs

- **[Vazamento de estado entre testes]** → `_reset_app_state()` idempotente que restaura explicitamente todos os campos mutáveis listados em D1; rodar a suíte completa para validar independência.
- **[Callbacks `root.after(10, ...)` agendados]** (`_center_window`/`state("zoomed")`) podem disparar em `update()` no meio de outro teste → inócuos (apenas geometria), mas `_reset_app_state()` deve zerar `_configure_after_id` se aplicável.
- **[Threads de `toggle_evolution`/`fetch`]** quando `historical_data` é `None` disparam `_fetch_historical_rates` em thread → os testes atuais já setam `historical_data` antes de `toggle_evolution`; `_reset_app_state()` deve zerar `_historical_fetching` para evitar travamento entre testes.
- **[`matplotlib` estado compartilhado]** — reutilizar o mesmo `Figure` exige limpeza correta do axes antes de cada teste; `render_chart` já limpa o axes ao desenhar.
- **[Ordem/independência com `-p no:randomly`/plugins]** — não há plugin de ordem ativo; a suíte atual já é determinística.

## Open Questions

- Nenhuma bloqueante. O *seam* do D3 é opcional; se o ganho residual após D1/D2 já for aceitável (~7s), pode ser postergado.
