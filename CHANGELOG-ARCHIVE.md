# Changelog Archive

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.9.1] - 2026-07-29

### [curva-curta-longa](openspec/changes/archive/2026-07-29-curva-curta-longa/) Renomeia rótulos da UI para "Curva curta" e "Curva longa"

#### Changed

- Título da janela: "B3 SELIC Pré v{version}" → "Taxas Referenciais SELIC (B3) v{version}"
- RadioButton "Detalhado" → "Curva curta" (modo raw)
- RadioButton "Consolidado" → "Curva longa" (modo consolidado)
- Títulos dos gráficos renomeados para "Curva Curta (SELIC Pré)" / "Curva Longa (SELIC Pré)" e variações de evolução
- Título 3D centralizado horizontalmente (removido deslocamento artificial)

#### Fixed

- pyproject.toml: versão corrigida de 0.8.0 → 0.9.1 (estava defasada)

## [0.9.0] - 2026-07-02

### [cache-b3-em-disco](openspec/changes/archive/2026-07-02-cache-b3-em-disco/) Cache em disco para evitar downloads redundantes da B3

#### Added

- Criar sistema de cache em disco para dados baixados da B3, chaveado por data (granular: 1 arquivo JSON por data)
- Verificar cache antes de fazer requisição HTTP; cache hit retorna dados sem chamar a B3
- TTL de 30 minutos apenas para a data atual; datas passadas são imutáveis (sem expiração)
- Corrupção de JSON tratada como cache miss (deleta arquivo + refetch automático)
- Housekeeping automático: limpa caches com mais de 1 ano (parametrizável via `max_age_days`)
- Cache segue XDG: `~/.cache/b3-selic-pre/rates/` no Linux
- Classe `CachedB3Client` encapsula fetch + cache, usada por CLI e GUI
- Indicador visual na barra de status da GUI: mostra "Cache" vs "API B3" / "Arquivo oficial B3"
- Flag `--no-cache` no CLI para forçar download fresco ignorando o cache

### [evolucao-resumo-executivo](openspec/changes/archive/2026-07-02-evolucao-resumo-executivo/) Adiciona painel de evolução da curva ao sidebar da GUI

#### Added

- Adiciona a seção "Resumo Executivo — Evolução da Curva" ao sidebar da GUI, abaixo do painel de Curva Atual
- Adiciona 2 novos arquivos ao módulo `application/analyze/`: `_evolucao.py` e `_texto_evolucao.py`
- Adiciona parâmetros de configuração no `settings.json` sob a chave `curva_evolucao`
- Adiciona o sub-painel "Evolução da Curva" no sidebar da GUI, visível apenas quando o modo Evolução está ativo
- Adiciona a struct `EvolutionReport` com os indicadores calculados e texto gerado

#### Changed

- Atualiza `__init__.py` do módulo `analyze` para exportar a nova função `analyze_evolution()`

### [novo-resumo-executivo](openspec/changes/archive/2026-07-02-novo-resumo-executivo/) Substitui motor de análise por Resumo Executivo da Curva de Juros

#### Added

- Cria 4 novos arquivos no módulo `application/analyze/`: `__init__.py`, `_resumo.py`, `_texto.py`, `_config.py`
- Adiciona novos parâmetros de configuração no `settings.json` sob as chaves `curva_juros` e `curva_evolucao`

#### Changed

- **BREAKING**: Substitui completamente o módulo `application/analyze/` por nova implementação baseada no Resumo Executivo da Curva de Juros
- Atualiza o sidebar da GUI para exibir o novo layout do Resumo Executivo (tags tk.Text header/positive/negative, 7 blocos nomeados + mensagem final)
- **BREAKING**: Altera o contrato da função `analyze()` — agora recebe parâmetros de configuração adicionais e retorna `AnalysisReport` com estrutura diferente

#### Removed

- Remove 8 arquivos do motor antigo (`_metrics.py`, `_features.py`, `_classifier.py`, `_registry.py`, `_scoring.py`, `_templates.py`, `_report.py`, `_metrics_evolution.py`)
- Remove a classe de análise para os modos "consolidado" e "evolução" (placeholders)
- Remove todos os testes antigos do motor de análise (`test_analyze.py`)

## [0.8.4] - 2026-06-29

### [fix-shortcut-detection](openspec/changes/archive/2026-06-29-fix-shortcut-detection/) Fix shortcut detection to check both Desktop and applications paths

#### Fixed

- `shortcut_exists()` now checks both `~/Desktop/` and `~/.local/share/applications/` instead of only the applications entry
- "Criar Atalho Desktop" button now appears whenever either shortcut is missing (instead of only when applications entry is missing)

#### Changed

- Update `shortcut-installer` spec to reflect the corrected dual-path detection behavior

## [0.8.3] - 2026-06-29

### [gui-as-default](openspec/changes/archive/2026-06-29-gui-as-default/) GUI becomes default invocation mode; --today flag added

#### Added

- `--today` flag to print today's reference rates as CSV

#### Changed

- **BREAKING**: `b3-selic-pre` (no arguments) now opens the GUI instead of printing CSV to stdout

### [progress-single-fetch](openspec/changes/archive/2026-06-29-progress-single-fetch/) Determinate progress bar for single-date fetch

#### Added

- `fetch_reference_rates()` gains optional `progress_callback` parameter for page-by-page progress reporting
- Pagination metadata (`totalCount`) extracted from B3 API response for total page calculation

#### Changed

- Single-date fetch progress bar switches from indeterminate to determinate after first page reveals total pages (hybrid approach)

## [0.8.1] - 2026-06-28

### [ui-reorganization](openspec/changes/archive/2026-06-28-ui-reorganization/) UI reorganization with DateEntry, icon buttons, compact layout and frozen title

#### Added

- Add `tkcalendar` to project dependencies

#### Changed

- Replace ttk.Entry, calendar popup and custom DatePicker with tkcalendar.DateEntry
- Change date label from "Data (YYYY-MM-DD):" to "Data de referência:"
- Replace text buttons with 24x24 icon images
- Show content-loading icon on fetch button during loading; move "Buscando…" text to statusbar
- Move "Copiar dados" button to top frame
- Move "Copiar gráfico" button into matplotlib toolbar
- Merge radiobuttons/checkboxes and stats summary into a single reduced-height row
- Display stats as compact pipe-separated format on right side of control row
- Freeze window title (remove dynamic title updates on data load)

#### Removed

- Remove "Exportar PNG" button (redundant with native matplotlib toolbar save button)

## [0.8.0] - 2026-06-27

### [ux-refinements](openspec/changes/archive/2026-06-27-ux-refinements/) 26 UI refinements for professional-quality feedback, persistence, and controls

#### Added

- Add determinate/indeterminate progress bars to the statusbar
- Highlight date entry in red on validation failure
- Add placeholder text to date entry
- Add "Hoje" button to reset date to today
- Add tooltips to all interactive controls
- Show data source and last update time in statusbar
- Persist last used date and user preferences to XDG config file
- Add keyboard shortcuts (Ctrl+C, Ctrl+Shift+C, Ctrl+S, F5, Ctrl+E, Ctrl+L)
- Show quick statistics row above chart
- Show placeholder text on empty chart ("Nenhum dado carregado")
- Temporarily show confirm message on copy then revert to prior status
- Add ttk.Separator between top/middle/bottom layout sections
- Add headers and rich-text formatting to analysis panel
- Automatically disable/enable controls based on available data context

#### Changed

- Block all controls during loading and show wait cursor
- Prefix status messages with Unicode icons per severity
- Toggle "Buscar" button text to "Buscando…" during fetch
- Update window title with loaded data context
- Improve export feedback with full file path
- Replace fixed-width sidebar with ttk.PanedWindow for resizable analysis panel

### [add-statusbar-feedback](openspec/changes/archive/2026-06-27-add-statusbar-feedback/) The application's feedback messages are currently displayed as a plain `ttk.Label` alongside action buttons in the bottom frame, with no visual distinction between errors, warnings, successes, or informational messages.

#### Added

- The statusbar will visually differentiate message types (info, success, warning, error) using foreground colors and/or icons

#### Changed

- Replace the existing plain `ttk.Label` status message with a proper statusbar widget at the window's base
- Update all `set_status()` call sites to pass a message type so the statusbar renders appropriate styling
- Keep the statusbar API simple: `set_status(message, type="info")` where type defaults to `"info"`
- No new dependencies required — the statusbar will be built with standard `ttk` widgets

#### Removed

- The existing message label position (inline in `bottom_frame`) will be removed; the statusbar sits at the very bottom of the window

### [auto-analysis-commentary](openspec/changes/archive/2026-06-26-auto-analysis-commentary/) O programa exibe gráficos de taxas SELIC Pré, mas não oferece nenhuma interpretação textual dos dados. Um motor de inferência baseado em regras, 100% determinístico, pode gerar automaticamente um relatório em linguagem natural.

#### Added

- Adicionar subpacote `application/analyze/` com motor de inferência baseado em regras, composto por 14 regras (R001–R014)
- Extração de métricas geométricas: Índice de Tendência, segmentação da curva (curto/médio/longo), suavidade, extremos locais, mudanças de inclinação e pontos de inflexão
- Score agregado com pesos (+2, +1, 0, −1) classificado em 5 níveis (estável a mudança estrutural expressiva)
- Relatório estruturado em 4 blocos: Tendência Geral → Forma Geométrica → Segmentos → Conclusão
- Adicionar painel lateral direito collapsível na GUI (`SelicPreApp` em `presentation/gui.py`) para exibir o relatório textual
- Checkbox "Análise" no bottom_frame para alternar visibilidade do painel
- Integrar a análise no fluxo de redraw do gráfico (`_redraw_chart`), atualizando o relatório automaticamente a cada nova visualização
- Thresholds ajustáveis por parâmetro nas funções do motor

### [fix-after-min-feature](openspec/changes/archive/2026-06-26-fix-after-min-feature/) O feature `AFTER_MIN_UP` computa a proporção de deltas positivos após o mínimo global usando toda a cauda da curva. Em curvas DI típicas, o trecho longo é essencialmente plano (deltas zero), destruindo a proporção.

#### Fixed

- **Restringir janela do `AFTER_MIN_UP` ao intervalo [min_idx, max_idx]**: limitar a análise à zona de recuperação — do mínimo global até o máximo global. **BREAKING**: altera o comportamento do feature
- **Restringir janela do `AFTER_MAX_DOWN` ao intervalo [max_idx, min_idx]**: analisar apenas a zona de descida do máximo ao mínimo global. **BREAKING**: idem
- **Adicionar fallback para quando max_idx <= min_idx**: se o máximo não ocorre depois do mínimo (ou vice-versa), o feature retorna False

### [fix-inference-edge-cases](openspec/changes/archive/2026-06-26-fix-inference-edge-cases/) O framework atual de classificação utiliza um limiar binário de ativação: cada regra ou é satisfeita integralmente ou é descartada. Na prática, evidências estruturais possuem diferentes importâncias diagnósticas.

#### Added

- **Adicionar R199 — Classe Primária por Dominância**: o Classifier coleta os escores de ativação que cada regra produziu; se nenhuma classe primária ativou diretamente, R199 seleciona a de maior `activation_score` >= 0.70
- **Rastrear estado de avaliação por regra**: cada regra produz `matched_features`, `missing_features` e `activation_score`, permitindo auditoria completa
- **Adicionar VOLATILIDADE_MODERADA**: fecha a lacuna diagnóstica entre baixa e alta volatilidade. Escore 0 (informativo)
- **Adicionar RECUPERACAO_LONGA**: detecta tendência ascendente persistente com critérios determinísticos (>= 70% deltas positivos em >= 15% da curva, slope positivo, amplitude >= 40%)

#### Changed

- **Separar fatos estruturais em independentes e dependentes**: fatos como TORCAO, EMPINAMENTO, ACHATAMENTO e DEGRAUS passam a ser avaliados independentemente da classe primária (sem `gated_by`); RECUPERACAO_SUSTENTADA mantém o gate

### [fix-inference-engine-rules](openspec/changes/archive/2026-06-26-fix-inference-engine-rules/) O motor de inferência implementado em `application/analyze/` contém bugs lógicos em 4 regras (R004, R005, R006, R013) que distorcem a ativação de inferências e o score final.

#### Added

- Adicionar métrica `indice_minimo_global` ao `DetailedMetrics` para suportar R006 corrigido
- **Adicionar 6 novas regras (R015–R020)**: R015 Oscilação Elevada, R016 Amplitude Reduzida, R017 Amplitude Elevada, R018 Curva Invertida, R019 Achamento/Empinamento, R020 Formato-S
- **Adicionar thresholds** para as novas regras em `AnalysisThresholds`

#### Changed

- **Classificação dual (ascendente/descendente)**: labels de classificação de score refletem a direção da tendência global detectada (R001, R002 ou R003)

#### Fixed

- **Corrigir R004 (Vale)**: cálculo da posição relativa do mínimo e remoção do `max_day=756` hardcoded
- **Corrigir R005 (Pico)**: implementar verificação real de "queda contínua" após o pico (>=80% dos deltas negativos)
- **Corrigir R006 (Recuperação Sustentada)**: usar deltas ponto-a-ponto após o mínimo global
- **Corrigir R013 (Movimento Monótono)**: usar deltas ponto-a-ponto da curva inteira
- **Tornar R010 (Curva Suave) relativo à amplitude**: `IndiceSuavidade / Amplitude` em vez de threshold absoluto

### [hierarchical-inference-engine](openspec/changes/archive/2026-06-26-hierarchical-inference-engine/) O motor de inferência atual avalia 20 regras como um conjunto plano: todas competem no mesmo nível, sem hierarquia, sem exclusão mútua entre conceitos contraditórios, produzindo relatórios com afirmações inconsistentes.

#### Changed

- **Substituir a arquitetura plana de 20 regras por um motor hierárquico de 5 níveis**: N1 Classificação Primária (exclusiva: OSCILANTE > VALE > PICO > SIGMOIDE > ASCENDENTE > DESCENDENTE > PLANA), N2 Características Estruturais (gated), N3 Qualidade (independentes), N4 Intensidade (score ponderado N1×3, N2×2, N3×1 + confiança), N5 Relatório (FORMA + INTENSIDADE)
- **Adicionar `slope_global` ao `DetailedMetrics`**: coeficiente angular da regressão linear sobre toda a curva, substituindo `IndiceTendencia`
- **Endurecer condições de PLANA**: requer `amplitude < 0.10` **E** `|delta_final| < 0.05` **E** `|slope_global| < limiar`
- **Endurecer R012 (Mudança Estrutural)**: exige diferença entre slopes > 30%, não apenas 1 inflexão
- **Endurecer R020 (Formato-S → SIGMOIDE)**: exige >= 2 inflexões com cada trecho > 15% da curva
- **Reescrever `_rules.py`** como `_classifier.py` com a nova arquitetura hierárquica
- **Remover `_thresholds.py`** e integrar thresholds diretamente no classifier

#### Removed

- **Remover `IndiceTendencia`** do `DetailedMetrics` (substituído por `slope_global`)

### [refine-inference-pipeline](openspec/changes/archive/2026-06-26-refine-inference-pipeline/) O motor hierárquico atual ainda depende de contagem de extremos locais para classificação VALE/PICO — uma abordagem que quebra com dados reais da B3. Esta especificação introduz uma arquitetura de sistema especialista determinístico.

#### Added

- **Pipeline completo**: `Raw Data → Metrics → Features → Rule Registry → Classifier → Facts → ScoringPolicy → Score → Report Templates → Analysis Report`
- **ScoringPolicy separada do Registry**: regras definem apenas `id`, `priority`, `required_features`, `generated_fact`, `text_template_id`, `exclusive_group` — nunca `weight`
- **Rastreabilidade em dois níveis**: cada Fact carrega `derived_from_features`; cada Feature carrega `derived_from_metrics`
- **FactType**: `CLASSIFICATION`, `STRUCTURE`, `QUALITY`, `INTENSITY`, `AUXILIARY`
- **Confiança por Fact**: `confidence = opcionais_satisfeitas / total_opcionais`
- **InferenceConfig**: centraliza todos os ε em um único dataclass parametrizável
- **Versionamento do motor**: `AnalysisResult` inclui `engine_version`, `ruleset_version`, `generated_at`
- **Templates internacionalizáveis**: regras referenciam `template_id`, textos residem em mapa por locale
- **Framework VALE/PICO** com short-circuit (condição A obrigatória, 3/4 opcionais)
- **Métricas com fórmulas explícitas** e independentes de biblioteca; normalização X ∈ [0,1]; guarda contra divisão por zero

#### Changed

- **Features imutáveis**: após `compute_features()`, nenhuma regra pode alterar Features — apenas gerar novos Facts
- **Grupos de exclusividade no Registry**: `exclusive_group = "PRIMARY_CLASS"` impede que regras contraditórias coexistam
- **Classifier puro**: mesmas entradas → mesmas saídas; sem estado interno, sem cache, sem mutação
- **Prioridade explícita**: `priority` menor = maior prioridade (0 executa antes de 100)
- **Report consome apenas Facts**: nunca acessa Features ou métricas diretamente

## [0.7.1] - 2026-06-26

### [clean-arch-pyproject](openspec/changes/archive/2026-06-26-clean-arch-pyproject/) Reestruturar monolito para Clean Architecture com src/ layout e pyproject.toml

#### Changed

- Decompor `b3_selic_pre.py` em pacote `src/b3_selic_pre/` com camadas domain, application, infrastructure, presentation
- Criar `pyproject.toml` unificando metadados, dependências e entry point — substitui `requirements.txt`
- Mover `icons/` para dentro do pacote como `package_data`
- Atualizar `b3-selic-pre.spec` para apontar para o novo entry point (`__main__.py`)
- Atualizar `Makefile` para usar `pip install -e .` e `python -m b3_selic_pre`
- Atualizar `.github/workflows/test.yml` e `release.yml` para o novo build
- Atualizar `README.md` com novos comandos de uso
- Atualizar skills OpenSpec (release-version, release-push) com novos paths
- Atualizar todos os imports e `mock.patch` nos testes (`tests/`)
- **BREAKING**: `python3 b3_selic_pre.py` → `python3 -m b3_selic_pre` (ou `b3-selic-pre` via entry point)

## [0.7.0] - 2026-06-26

### [grafico-3d-evolucao-curva](openspec/changes/archive/2026-06-26-grafico-3d-evolucao-curva/) 3D surface visualization of curve evolution

#### Added

- Add a "3D" checkbox alongside the existing "Evolução da curva" checkbox in the GUI (disabled when evolution is OFF)
- When evolution is ON and 3D is ON, render the 5 curves as a 3D surface plot using `plot_surface` instead of the standard 2D line chart
- The 3D view works with both "Detalhado" and "Consolidado" radio states — raw rate data or yearly averages
- Each curve occupies a distinct Z position (today=0, 28d ago=4)
- The 5 individual curves are drawn as black lines overlaid on the surface, with decreasing linewidth (today thickest, oldest thinnest)
- Surface uses a unified colormap (RdYlGn_r — red=high rate, yellow=mid, green=low) where color represents rate magnitude
- Requires `mpl_toolkits.mplot3d` for 3D projection support

## [0.6.0] - 2026-06-26

### [improve-quiver-arrow-layout](openspec/changes/archive/2026-06-26-improve-quiver-arrow-layout/) Redesign quiver arrow layout with offset/step pattern to eliminate visual overlap

#### Changed

- Redesign quiver arrow placement to show at most one arrow per tick position, cycling through curve transitions by offset (offset 1, step 5)
- Apply the new layout to both `render_curve_evolution` (1-year intervals) and `render_detailed_evolution` (22 DU intervals)

## [0.5.1] - 2026-06-18

### Changed

- **Eixo X do gráfico Detalhado**: rótulo alterado de "DU252" para "Dias úteis" (tanto no modo Detalhado quanto na Evolução Detalhada)
- **Grid trimestral**: marcas principais (major) passaram de 90 DU para aproximadamente 66 DU (trimestre ≈ 66 dias úteis), com nearest-match aos dados reais (tolerância 44 DU); marcas secundárias (minor) ajustadas para aproximadamente 22 DU (≈ mês, tolerância 22 DU), excluindo posições ocupadas pelo major — garante que as linhas de grid coincidam com dados existentes
- **Setas quiver na Evolução Detalhada**: adicionadas setas de direção da taxa nos mesmos pontos do grid secundário (minor ticks, ~22 DU), coincidindo com as linhas tracejadas; posições calculadas via nearest-match aos dados da data mais recente, não mais à união de todas as datas históricas
- **Setas quiver na Evolução Consolidada**: substituídas as posições fixas `QUIVER_YEARS` pelo mesmo padrão — setas em todos os minor ticks (~1 ano), com lookup nearest-match por data
- **Evolução Consolidada**: grid (major ~3 anos, minor ~1 ano) e quiver agora usam `_nearest_ticks` com tolerância 1, mesma lógica da evolução detalhada; constantes `QUIVER_YEARS` e `QUIVER_DU252` removidas
- **Helper `_nearest_ticks`**: função extraída para eliminar duplicação da lógica de nearest-match entre todas as funções de renderização
- **Modo Consolidado**: grid (major ~3 anos, minor ~1 ano) também migrado de ticks exatos para `_nearest_ticks` com tolerância 1, consistente com as demais funções
- **Base de dados única para grid**: `render_detailed_evolution` e `render_curve_evolution` agora usam apenas os dados da data mais recente (em vez da união entre datas) para calcular ticks e setas, garantindo consistência com os gráficos base

### [detailed-chart-improvements](openspec/changes/archive/2026-06-18-detailed-chart-improvements/) The detailed chart (DU252 × TAXA) has usability gaps: the x-axis label "DU252" is not intuitive for non-specialist users, the quarterly grid marks at 90 DU (~4.5 months) don't align with a natural calendar quarter (~60 business days), and the detailed evolution view lacks quiver arrows.

#### Added

- **Quiver arrows in detailed evolution**: Add quiver arrows at each quarterly position (60, 120, ..., 720) showing rate change direction between historical curves, matching the consolidated evolution behavior

#### Changed

- **X-axis label**: Change from "DU252" to "Dias úteis" in both the raw detailed chart and the detailed evolution chart
- **Grid marks**: Change quarterly (major) grid marks from every 90 DU to every 60 DU, which better approximates a calendar quarter in business days
- **Documentation**: Update CHANGELOG.md, README.md, and existing spec files to reflect the new behavior

## [0.5.0] - 2026-06-18

### Added

- **Grid trimestral no gráfico Detalhado**: linhas verticais sólidas a cada 90 DU (≈ trimestre) como ticks principais (major, alpha=0.3), aplicadas tanto no modo Detalhado quanto na Evolução Detalhada
- **Grid trienal no gráfico Consolidado**: linhas verticais sólidas a cada 3 anos como ticks principais (major, alpha=0.3), aplicadas tanto no modo Consolidado quanto na Evolução Consolidada
- `ax.grid` dividido em `which='major'` (sólido, alpha=0.3) e `which='minor'` (tracejado, alpha=0.15, linestyle="--") nas 4 funções de renderização — o grid trimestral/trienal (major) é mais proeminente que o mensal/anual (minor)

### Changed

- **Radiobutton "Evolução da curva" → Checkbox**: "Evolução da curva" convertido de `ttk.Radiobutton` para `ttk.Checkbutton`, desacoplado dos modos base "Detalhado" e "Consolidado". O checkbox pode ser marcado/desmarcado independentemente do radiobutton ativo.
- **Evolução detalhada**: nova função `render_detailed_evolution` que plota 5 linhas gradiente verde no eixo DU252 × TAXA (uma curva por data histórica), exibida quando o checkbox está marcado e o radiobutton "Detalhado" está selecionado.
- **Evolução consolidada**: `render_curve_evolution` mantida (5 curvas azuis + flechas quiver), exibida quando o checkbox está marcado e "Consolidado" está selecionado.
- **Lazy one-time fetch**: ao marcar o checkbox pela primeira vez na execução, o sistema automaticamente busca dados históricos (5 datas, data-base = hoje) sem exigir clique em "Buscar". Ao desmarcar/remarcar, apenas alterna a exibição sem novas requisições.
- **"Copiar dados" segue o checkbox**: evolution ON → copia CSV de evolução; OFF → copia base (detalhado ou consolidado conforme o radio).
- Versão bumpada para `0.5.0`

### Removed

- Radiobutton "Evolução da curva" removido (substituído por checkbox)
- Modo `view_var = "evolution"` removido do grupo de radiobuttons

### [evolution-checkbox](openspec/changes/archive/2026-06-18-evolution-checkbox/) The current "Evolução da curva" is a radiobutton mutually exclusive with "Detalhado" and "Consolidado", forcing users to lose their base view to see evolution. Making it a checkbox decouples the two concerns.

#### Added

- **Detailed evolution chart**: New `render_detailed_evolution(fig, date_rates)` function plots 5 lines on DU252 × TAXA with gradient coloring (one curve per historical date)
- **Lazy one-time fetch**: First check of the evolution checkbox auto-triggers `fetch_historical_rates()` (date = today) without requiring the user to click "Buscar"; subsequent toggles only switch the display
- **Two evolution renderings**: Radio "Detalhado" + evolution ON → detailed evolution; Radio "Consolidado" + evolution ON → consolidated evolution (existing quiver chart)

#### Changed

- **Radiobutton → Checkbox**: "Evolução da curva" becomes a standalone `ttk.Checkbutton` independent from the two-view radiobutton group ("Detalhado", "Consolidado")
- **Copiar dados follows view**: Evolution ON copies evolution CSV; OFF copies base view data
- **Version bump**: `__version__` → `"0.5.0"`

#### Removed

- **BREAKING**: `view_var` values drop `"evolution"` — now only `"raw"` / `"consolidated"`

### [quarterly-grid-marks](openspec/changes/archive/2026-06-18-quarterly-grid-marks/) The current charts have a uniform grid with no temporal reference marks, making it hard to visually align data points with calendar quarters (detailed chart) or multi-year periods (consolidated chart).

#### Added

- **Detailed chart (raw + detailed evolution)**: add minor vertical grid lines every 90 DUs (business days ≈ 1 quarter) with dashed style and reduced alpha
- **Consolidated chart (consolidated + consolidated evolution)**: add minor vertical grid lines every 3 years with dashed style and reduced alpha

#### Changed

- **Grid refactored**: split `ax.grid(True, alpha=0.3)` into separate major/minor grid calls to support different styles per tier

## [0.4.0] - 2026-06-18

### Added

- `--create-shortcut`: novo parâmetro CLI que cria atalho desktop e sai
- `create_shortcut()`: função que gera `.desktop` FreeDesktop com nome "Taxas Referenciais SELIC (B3)" e categoria `Finance;Office;`
- `_detect_desktop_dir()`: detecção do diretório Desktop via `xdg-user-dir` → `~/.config/user-dirs.dirs` → `~/Desktop` (suporte a locale pt-BR)
- `_resolve_executable()`: resolução do executável para script Python (`python3 + script`) ou binário compilado PyInstaller (`sys.executable`)
- `_icon_source()`: resolução do caminho do ícone em modo script (`_SCRIPT_DIR/icons/`) ou frozen (`sys._MEIPASS`)
- `shortcut_exists()`: verifica se atalho já está instalado em `~/.local/share/applications/`
- **Botão "Criar Atalho Desktop"** na GUI (top_frame, lado direito), aparece automaticamente se não existir atalho e se auto-destrói após criar
- **Instalação do ícone**: cópia de `b3_selic_pre.png` para `~/.local/share/icons/` com referência absoluta no `.desktop`
- **Instalação em dois locais**: `.desktop` gerado em `~/Desktop/` e `~/.local/share/applications/`

### Changed

- Versão bumpada para `0.4.0`
- `b3-selic-pre.desktop` na raiz do projeto: `Name` atualizado para "Taxas Referenciais SELIC (B3)", caminhos substituídos por referências simbólicas (`b3-selic-pre --gui`, `Icon=b3-selic-pre`)
- `b3-selic-pre.spec`: `upx` desabilitado no macOS (evita warnings); `console` desabilitado no macOS (.app sem terminal); adicionado `info_plist` com `NSHighResolutionCapable`, `CFBundleShortVersionString` e `CFBundleVersion`

### [create-desktop-shortcut](openspec/changes/archive/2026-06-18-create-desktop-shortcut/) Ao rodar em modo GUI, usuários não têm um atalho no desktop para iniciar a aplicação rapidamente. O arquivo `.desktop` existe apenas no repositório e precisa ser copiado manualmente.

#### Added

- Adicionar função `create_shortcut()` que gera um `.desktop` compatível com FreeDesktop
- Adicionar parâmetro CLI `--create-shortcut` que cria o atalho e sai
- No modo GUI, detectar automaticamente se o atalho já existe; se não, mostrar botão "Criar Atalho Desktop" no top_frame
- Nome do atalho: "Taxas Referenciais SELIC (B3)"
- Categoria Linux: `Finance;Office;`
- Ícone copiado para `~/.local/share/icons/` para referência estável
- `.desktop` instalado em `~/Desktop/` e `~/.local/share/applications/`

#### Changed

- Versão bumpada de `0.3.1` para `0.4.0`

## [0.3.0] - 2026-06-17

### Added

- **Evolução da Curva**: novo modo de visualização que plota 5 curvas superpostas (data-base + 7, 14, 21, 28 dias atrás) com gradiente de cor e flechas quiver nos anos-chave 0, 1, 2, 3, 5, 10, 15, 20
- `fetch_rates_download`: função que busca dados históricos via endpoint `GetDownloadFile` da B3 (base64-encoded CSV)
- `fetch_historical_rates`: função que busca taxas de 5 datas em paralelo (4 workers) com fallback para `GetList` quando `GetDownloadFile` retorna vazio
- `average_rate_by_year`: função que calcula a taxa média por ano (midpoint entre min e max)
- `render_curve_evolution`: função que renderiza o gráfico de evolução com gradiente, alpha decrescente e flechas quiver
- `format_evolution_csv`: função que exporta dados das 5 curvas no formato `DATA;ANO;TAXA_MEDIA`
- `DatePicker`: widget de calendário popup implementado com tkinter puro (navegação mês/ano, grid de dias clicáveis)
- **Radio buttons**: três `ttk.Radiobutton` ("Detalhado", "Consolidado", "Evolução da curva") substituem o checkbox "Consolidar por ano"
- **Validação de 30 dias**: consultas nos modos Detalhado e Consolidado são bloqueadas para datas anteriores a 30 dias corridos; modo Evolução é isento
- **Auto-date no Evolution**: ao selecionar "Evolução da curva", a data é automaticamente alterada para a data atual
- **Calendário visual**: botão `📅` ao lado do campo de data abre o DatePicker
- **Título reposicionado**: `fig.suptitle(..., y=0.92)` em todos os modos evita sobreposição com a toolbar do matplotlib
- Indicador de progresso na status bar durante fetch multi-data no modo evolução

### Changed

- Versão bumpada para `0.3.0`
- `GetDownloadFile` é usado para datas históricas (retorna dados específicos da data); `GetList` é usado apenas para a data atual (sempre retorna snapshot recente)
- `_weeks_ago` substituído por `_days_ago` com `EVOLUTION_DAYS = [28, 21, 14, 7, 0]`
- `page_size` máximo ajustado para 100 (B3 rejeita valores ≥150)

### Removed

- Checkbox "Consolidar por ano" removido (substituído por radio buttons)
- `_weeks_ago` e `HISTORICAL_WEEKS` removidos

### [curve-evolution-chart](openspec/changes/archive/2026-06-17-curve-evolution-chart/) O gráfico atual (curva única para uma data) não permite visualizar como a curva de juros SELIC Pré se movimentou ao longo do tempo. Para análise de tendências, é necessário comparar a curva atual com curvas históricas (7, 14, 21, 28 dias atrás).

#### Added

- Adicionar modo de visualização "Evolução da Curva" na GUI do desktop
- Nova função `fetch_rates_download` para buscar taxas de datas históricas usando o endpoint `GetDownloadFile` da B3
- Nova função `fetch_historical_rates` para buscar taxas de 5 datas (base, 7, 14, 21, 28 dias atrás) em paralelo
- Nova função `average_rate_by_year` para calcular a média entre menor e maior taxa por ano
- Nova função de renderização `render_curve_evolution` com 5 curvas superpostas (gradiente + alpha) e flechas quiver em anos-chave
- Adicionar DatePicker popup calendar para entrada de data visual
- Limite de 30 dias corridos para consultas nos modos Detalhado e Consolidado
- Indicador de progresso durante a busca multi-data
- A opção "Copiar dados" no modo Evolução exporta dados completos das 5 datas

#### Changed

- Substituir checkbox "Consolidar por ano" por radio buttons com 3 opções: "Detalhado", "Consolidado", "Evolução da Curva"
- Reposicionar título do gráfico para `y=0.92` (evita sobreposição com toolbar)
- Bump de versão: `__version__` passa de `"0.2.3"` para `"0.3.0"`

## [0.2.3] - 2026-06-17

### Added

- Makefile com targets `install`, `build` e `clean` para builds locais reproduzíveis
- Workflow de release agora usa `make install && make build` em vez de comandos inline
- README com seções de instalação (manual, Makefile, binário pré-compilado) e uso nas três modalidades

### Changed

- Versão bumpada para `0.2.3`
- Makefile: build via `.venv/` local em vez de pip system-wide, evitando PEP 668

### Fixed

- `b3-selic-pre.spec`: adicionados hidden imports `PIL._tkinter_finder`, `matplotlib` e `matplotlib.figure` para resolver erros de módulo não encontrado no executável gerado
- `copy_chart`: substituída implementação com subprocessos + threads por `pyxclip` (Rust, zero dependências externas), eliminando travamentos do `xclip` e simplificando o código

### [add-makefile-build](openspec/changes/archive/2026-06-17-add-makefile-build/) Centralizar a lógica de build do PyInstaller em um Makefile, eliminando a duplicação entre CI e desenvolvimento local. Atualmente os comandos de build estão hardcoded no workflow GitHub Actions.

#### Added

- Criar `Makefile` com targets `install`, `build` e `clean`
- Adicionar `CHANGELOG.md` com entry para a mudança
- Adicionar hidden imports (`PIL._tkinter_finder`, `matplotlib`, `matplotlib.figure`, `pyxclip`) no `b3-selic-pre.spec` para corrigir erros em runtime
- Adicionar `pyxclip>=0.2.0` ao `requirements.txt`

#### Changed

- Atualizar `.github/workflows/release.yml` para usar `make install` e `make build` em vez de comandos inline
- Bump da versão de `0.2.2` para `0.2.3`
- Substituir lógica de clipboard do `copy_chart` (subprocessos + threads + xclip/ctypes/osascript) pelo `pyxclip` (Rust, zero dependências externas)
- Atualizar `README.md` com instruções de instalação (manual, Makefile, binário pré-compilado) e uso nas três modalidades

## [0.2.2] - 2026-06-17

### Fixed

- Renomeação dos binários com prefixo da plataforma (`b3-selic-pre-linux`, `b3-selic-pre-windows.exe`, `b3-selic-pre-macos`) para evitar colisão de nomes no upload da release

## [0.2.1] - 2026-06-17

### Added

- Exibição da versão na barra de título da janela e flag `--version` no CLI

### Fixed

- Correção do glob de upload no workflow de release para anexar os binários à release (`b3-selic-pre-*/` → `b3-selic-pre-*/*`)
- Remoção do `b3-selic-pre.desktop` dos assets da release (continha caminhos absolutos locais)

### [show-version](openspec/changes/archive/2026-06-16-show-version/) O aplicativo não exibe sua versão em lugar nenhum — nem na janela, nem no CLI. Com o workflow de release gerando executáveis versionados por tag, o usuário não tem como saber qual versão está rodando.

#### Added

- Adicionar constante `__version__` no topo de `b3_selic_pre.py`
- Exibir a versão na barra de título da janela: `"B3 SELIC Pré v<version>"`
- Adicionar flag `--version` ao argparse para exibir a versão no CLI

## [0.2.0] - 2026-06-16

### Added

- GitHub Actions workflow for automated PyInstaller builds (Windows, Linux, macOS)
- GitHub Release publishing with binary assets
- PyInstaller `.spec` file for reproducible builds
- `CHANGELOG.md` for tracking version history

### [add-app-icon](openspec/changes/archive/2026-06-16-add-app-icon/) The desktop GUI currently has no window icon — it appears with the default Tkinter logo in the title bar and taskbar. The `b3_selic_pre.png` asset already exists at the project root but is unused.

#### Added

- Set the Tkinter window icon to `b3_selic_pre.png` using `iconphoto` (cross-platform PNG support)
- Resolve the icon path relative to the script directory to work from any CWD
- Create a `.desktop` entry file for launching the GUI from system menus
- Add a CLI helper or convenience script if `.desktop` needs an absolute entry point

### [add-csv-copy-button](openspec/changes/archive/2026-06-16-add-csv-copy-button/) Users need a way to copy the raw numerical data behind the chart to the clipboard as CSV, for use in spreadsheets or other analysis tools — the current workflow requires re-querying the CLI or manually transcribing values.

#### Added

- Add a "Copiar dados" button to the GUI bottom bar, positioned before the existing "Copiar gráfico" button
- When clicked, generate CSV matching the current view mode (raw or consolidated) and copy it to the system clipboard
- Use the same column naming conventions as the CLI output: `DU252,DC365,TAXA` for raw mode and `ANO,MENOR_TAXA,MAIOR_TAXA` for consolidated mode
- Respect existing button enable/disable pattern (disabled when no data loaded)
- No file-save dialog — clipboard-only, matching the existing "Copiar gráfico" pattern

### [add-matplotlib-chart](openspec/changes/archive/2026-06-16-add-matplotlib-chart/) The current GUI displays SELIC Pré rates as a tabular list (Treeview), which is ineffective for spotting trends and patterns across maturities. A line chart reveals the shape of the yield curve at a glance.

#### Added

- Add matplotlib as a project dependency
- Chart renders raw data as a green line (TAXA × DC365) when consolidation is off
- Chart renders consolidated data as two lines (menor_taxa in blue, maior_taxa in red) when consolidation is on
- Add "Exportar PNG" button to save the chart image to disk
- Add "Copiar gráfico" button to copy the chart image to the system clipboard
- Provide basic interactivity: zoom/pan via matplotlib toolbar

#### Changed

- Replace the Treeview table with a matplotlib line chart embedded in the tkinter window
- Keep existing CLI behavior unchanged

#### Removed

- Remove the Treeview table; tabular data remains accessible via CLI (`--yearly` and export)

### [consolidate-by-year](openspec/changes/archive/2026-06-16-consolidate-by-year/) A tabela bruta de taxas SELIC Pré mostra um registro por dia útil, o que pode ser difícil de analisar visualmente para períodos longos (centenas de linhas). Consolidar por ano permite enxergar rapidamente a taxa mínima e máxima de cada ano.

#### Added

- **GUI**: Adicionar checkbox "Consolidar por ano" que alterna a visualização da tabela entre registros individuais e linhas consolidadas por ano (ANO, MENOR TAXA, MAIOR TAXA)
- **CLI**: Adicionar flag `--yearly` ao `argparse` que, quando presente, imprime a tabela consolidada por ano em vez dos registros individuais
- **Núcleo**: Criar função `consolidate_by_year(records)` que agrupa registros por `day360 // 365` e retorna ano, taxa mínima e taxa máxima

#### Changed

- **Export/Copy**: "Copiar tabela" e "Exportar CSV" refletem a visualização atual (raw ou consolidada)

### [create-ui](openspec/changes/archive/2026-06-12-create-ui/) The project currently exposes B3 SELIC reference-rate data only through a small script with a hardcoded date and terminal output. A desktop GUI will make the data easier to query, inspect, copy, and export.

#### Added

- Add a desktop user interface for querying B3 SELIC Pré reference rates by date
- Display returned rates in a tabular view with day-count columns and rate values
- Show clear loading, success, empty-result, and error states for B3 API requests
- Allow users to copy or export the displayed results for downstream analysis

#### Changed

- Refactor the current script logic into reusable data-fetching code that can be shared by the GUI and command-line entry points

### [release-workflow](openspec/changes/archive/2026-06-16-release-workflow/) O projeto `b3-selic-pre` é uma aplicação desktop Python (tkinter + matplotlib) que consulta taxas SELIC Pré na B3. Atualmente só roda via `python b3_selic_pre.py`, exigindo Python e dependências instaladas.

#### Added

- Criar workflow GitHub Actions que gera executáveis com PyInstaller para Windows, Linux e macOS
- Publicar os binários como assets de uma GitHub Release
- Adicionar arquivo `.spec` versionado do PyInstaller
- Incluir o arquivo `b3-selic-pre.desktop` no release do Linux
- Adicionar `CHANGELOG.md` para registrar versões
- Disparar o workflow via push de tag `v*` ou manualmente (`workflow_dispatch`)
- Executáveis em formato `--onefile` (único arquivo)

[0.9.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.9.1
[0.9.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.9.0
[0.8.4]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.4
[0.8.3]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.3
[0.8.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.1
[0.8.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.8.0
[0.7.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.7.1
[0.7.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.7.0
[0.6.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.6.0
[0.5.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.5.1
[0.5.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.5.0
[0.4.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.4.0
[0.3.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.3.0

See main [CHANGELOG](CHANGELOG.md) for newer releases.
