## Context

A change `establish-architecture-governance` adiciona guardas estáticas e aprova as dívidas atuais em `tests/architecture_allowlist.py`. Este design elimina essas dívidas e migra para headless os testes de comportamento que hoje dependem de Tk.

Estado relevante encontrado:

- `application/analyze/_config.py` importa `presentation.settings.Settings`.
- `domain/constants.py` importa `os` para `SHORTCUT_CHECK_PATH`.
- `presentation/gui/app.py` instancia `CachedB3Client` e importa `_icon_source`/`shortcut_exists`; `actions.py` importa `create_shortcut`.
- `presentation/gui/fetch.py` e `window.py` concentram validação de data, limite de 30 dias e cálculo de dia útil.
- `presentation/gui/chart.py` calcula estatísticas, estados de botões e seleção de renderizador.
- `presentation/gui/actions.py` seleciona o formato de exportação.
- `presentation/charts.py` contém transformações puras de dados (marcações, interpolação, grades 3D).
- `tests/test_b3_selic_pre_gui.py` tem 22 testes, muitos validando regras que não precisam de display.

Ver `proposal.md` para motivação e `specs/` para os requisitos.

## Goals / Non-Goals

**Goals:**
- Remover todas as dívidas aprovadas de `application -> presentation`, `domain -> os` e GUI -> infrastructure (exceto o composition root da CLI).
- Criar serviços/headless reutilizáveis pela GUI e pela futura CLI.
- Reduzir o UI test budget de 22 para a menor contagem possível, mantendo cobertura equivalente.
- Manter comportamento observável da aplicação.

**Non-Goals:**
- Criar novos comandos CLI ou flags de produto.
- Reescrever a GUI ou alterar layout/aparência.
- Introduzir framework de injeção de dependência.
- Trocar Tkinter, matplotlib ou numpy.

## Decisions

### 1. Configuração por mapping na application; Settings na composição

**Decisão:** `CurvaJurosConfig` e `EvolutionConfig` passam a expor `from_mapping(...)` (ou construtor com defaults) e não importam `Settings`. A GUI monta a configuração a partir de `Settings` e injeta em `analyze`/`analyze_evolution`.

**Alternativa considerada:** Mover `Settings` para `infrastructure`. Também resolveria a dependência, mas ainda acoplaria a configuração de análise a um formato persistido. Mapping é mais simples e testável.

### 2. Regras de consulta em `application/use_cases.py` (ou serviço dedicado)

**Decisão:** Mover para a application:
- `days_ago` como API pública;
- `nearest_business_day`;
- validação de formato, data futura e idade máxima do histórico;
- estatísticas de taxas (mínimo/máximo);
- seleção do payload de exportação.

A GUI e a futura CLI chamam essas funções. Mensagens de validação permanecem equivalentes às atuais para não alterar a experiência.

**Alternativa considerada:** Um serviço de aplicação por operação. É mais CERIMÔNIA do que o necessário para o tamanho atual; funções puras no módulo de casos de uso bastam e podem ser extraídas depois.

### 3. View-model headless em `presentation/view_model.py`

**Decisão:** Criar um módulo de presentation sem Tkinter que, a partir de registros/histórico/modos, calcula:
- texto de estatísticas;
- estados de habilitação de controles;
- modo de gráfico/renderizador;
- texto de exportação e indicador de "sem dados".

Os mixins Tk apenas consultam o view-model e aplicam o resultado aos widgets. O módulo fica fora de `presentation/gui/` para que `import b3_selic_pre.presentation.view_model` não importe Tk via `presentation/gui/__init__.py`.

**Alternativa considerada:** Colocar o view-model em `application`. Rejeitada porque estados de controles e modos de gráfico são concerns de apresentação, embora headless.

### 4. Transformações de gráfico em `application/chart_data.py`

**Decisão:** Mover para a application as funções puras `nearest_ticks`, `interpolate_rates`, `nearest_rate`, `consolidated_3d_data`, `daily_3d_data` e `interpolate_3d_surface`. `presentation/charts.py` mantém apenas desenho, eixos, títulos, legendas e superfícies.

**Alternativa considerada:** Manter em `presentation/chart_data.py`. Seria headless, mas a regra de negócio de consolidação/interpolação é reutilizável e não depende de matplotlib; a application é o lugar mais adequado.

### 5. Injeção de adapters na GUI via composition root

**Decisão:** `SelicPreApp` recebe dependências opcionais (cliente B3, `shortcut_exists`, `create_shortcut`, `icon_source`, `settings`). `launch_gui` (composition root) instancia os adapters de infrastructure e injeta. Os padrões continuam funcionando para uso normal, mas os módulos da GUI deixam de importar infrastructure.

**Alternativa considerada:** Aprovar GUI -> infrastructure permanentemente. Rejeitada porque impede testar a GUI com fakes sem depender de infraestrutura concreta e mantém acoplamento desnecessário.

### 6. CLI fina com serviços compartilhados

**Decisão:** `presentation/cli.py` continua instanciando `CachedB3Client` e `create_shortcut` (composition root), mas delega resolução de data, seleção de saída e formatação aos serviços de application. Nenhuma nova flag é criada nesta change.

**Alternativa considerada:** Mover a CLI inteira para application. Rejeitada: parsing de argumentos e montagem de adapters são responsabilidades de presentation/composition root.

## UI Test Migration Plan

Baseline atual: 22 testes em `tests/test_b3_selic_pre_gui.py`.

| Teste atual | Destino |
| --- | --- |
| `test_invalid_date_shows_validation_without_fetching` | Headless: validação de data na application/view-model |
| `test_success_and_empty_and_error_flows` | Headless: estado do view-model/controller |
| `test_radio_buttons_exist_and_raw_is_default` | UI: montagem de widgets |
| `test_toggle_to_consolidated_updates_chart` | Headless: dispatch/modo de gráfico; render já coberto em `test_charts_render.py` |
| `test_fetch_respects_view_mode` | Headless: seleção de dados/modo de gráfico |
| `test_export_png_replaced_by_toolbar` | UI: montagem do toolbar (ou remover guard histórico) |
| `test_buttons_disabled_without_data` | Headless: view-model |
| `test_buttons_enabled_after_data_loaded` | Headless: view-model |
| `test_buttons_disabled_after_error_clears_data` | Headless: view-model |
| `test_data_button_exists_and_disabled_without_data` | UI: existência; estado vai para view-model |
| `test_data_button_enabled_after_data_loaded` | Headless: view-model |
| `test_data_button_disabled_after_error_clears_data` | Headless: view-model |
| `test_copy_data_raw_mode` | Headless: serviço de exportação |
| `test_copy_data_consolidated_mode` | Headless: serviço de exportação |
| `test_copy_data_noop_when_no_data` | Headless: serviço de exportação/view-model |
| `test_3d_checkbox_disabled_when_evolution_off` | Headless: view-model |
| `test_3d_checkbox_enabled_when_evolution_on_with_data` | Headless: view-model |
| `test_3d_checkbox_disabled_and_reset_when_evolution_turned_off` | Headless: view-model |
| `test_3d_triggers_3d_render_dispatch` | Headless: dispatch/modo de gráfico |
| `test_shortcut_button_shown_when_no_shortcut` | UI: montagem condicional |
| `test_shortcut_button_hidden_when_shortcut_exists` | UI: montagem condicional |
| `test_shortcut_button_callback_creates_shortcut` | Headless: serviço de ação/injeção; UI mantém apenas wiring se necessário |

Meta: manter no máximo 6 testes de UI e reduzir `UI_TEST_BUDGET` de 22 para a contagem medida (esperado 5–6).

## Risks / Trade-offs

- **[Refatoração ampla pode alterar mensagens/estado]** → Preservar mensagens e adicionar testes headless de equivalência antes de remover os testes de UI.
- **[View-model pode virar uma camada de indireção excessiva]** → Manter funções puras e pequenas; a GUI aplica estado, não recalcula regra.
- **[Mover funções de gráfico quebra imports de testes]** → Atualizar imports em `test_charts_data.py`, `test_charts_render.py` e `test_b3_selic_pre.py` na mesma tarefa.
- **[Injeção de dependências aumenta assinatura de `SelicPreApp`]** → Parâmetros opcionais com defaults de composição e um dataclass de dependências se a lista crescer.
- **[Redução do orçamento pode ser esquecida]** → Tarefa explícita para ajustar `UI_TEST_BUDGET` e rodar o guard após a migração.

## Migration Plan

1. Introduzir serviços/headless e view-model com testes headless, mantendo a GUI atual funcionando.
2. Refatorar a GUI para consumir os novos serviços e injetar adapters.
3. Migrar os testes de comportamento para headless e remover os testes de UI equivalentes.
4. Reduzir `UI_TEST_BUDGET`, remover aprovações de arquitetura obsoletas.
5. Executar `make lint`, `make complexity`, testes direcionados e, por haver mudança transversal na GUI/CLI, a suíte completa.
