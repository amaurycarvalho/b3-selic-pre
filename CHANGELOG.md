# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
