# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.2.2] - 2026-06-17

### Fixed

- Renomeação dos binários com prefixo da plataforma (`b3-selic-pre-linux`, `b3-selic-pre-windows.exe`, `b3-selic-pre-macos`) para evitar colisão de nomes no upload da release

## [0.2.1] - 2026-06-17

### Added

- Exibição da versão na barra de título da janela e flag `--version` no CLI

### Fixed

- Correção do glob de upload no workflow de release para anexar os binários à release (`b3-selic-pre-*/` → `b3-selic-pre-*/*`)
- Remoção do `b3-selic-pre.desktop` dos assets da release (continha caminhos absolutos locais)

## [0.2.0] - 2026-06-16

### Added

- GitHub Actions workflow for automated PyInstaller builds (Windows, Linux, macOS)
- GitHub Release publishing with binary assets
- PyInstaller `.spec` file for reproducible builds
- `CHANGELOG.md` for tracking version history
