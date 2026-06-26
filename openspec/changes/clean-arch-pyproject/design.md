## Context

O projeto `b3-selic-pre` é uma aplicação desktop/CLI Python pura (sem framework web). Tem ~1161 linhas em um único arquivo, com três responsabilidades misturadas: chamadas HTTP à API da B3, processamento de dados (domínio) e interface com usuário (CLI + Tkinter GUI). Não tem `pyproject.toml` — as dependências estão em `requirements.txt` e o build usa Makefile + PyInstaller spec separado.

## Goals / Non-Goals

**Goals:**
- Decompor o monolito em camadas com responsabilidades claras (Clean Architecture)
- Unificar configuração do projeto em `pyproject.toml` (build-system, metadados, dependências, entry point, tool configs)
- Usar `src/` layout para evitar poluição do import path e seguir boas práticas de packaging
- Mover `icons/` para dentro do pacote como `package_data`, acessível via `importlib.resources`
- Manter a compatibilidade do PyInstaller (via spec atualizado) e do entry point `b3-selic-pre`
- Atualizar todos os consumidores: Makefile, CI, testes, skills OpenSpec
- Preservar 100% do comportamento existente — sem mudanças funcionais

**Non-Goals:**
- Não adicionar novas funcionalidades
- Não mudar a API pública da B3 nem os formatos de saída
- Não introduzir type hints (será feito separadamente se desejado)
- Não trocar o build system (setuptools, não Poetry/PDM)
- Não adicionar cobertura de testes nova

## Decisions

### 1. src/ layout (vs diretório raiz)

`src/` layout evita que `pytest` ou `unittest` importem acidentalmente o código fonte não-instalado. Exige `pip install -e .` para desenvolvimento. É o padrão recomendado pelo Python Packaging Authority.

```
Pro: isolamento limpo entre fonte e instalado
Pro: pyproject.toml na raiz, pacote aninhado
Con: um nível extra de diretório
```

### 2. Camadas do pacote

```
src/b3_selic_pre/
├── __init__.py          → __version__, sem re-exports (purista)
├── __main__.py          → if __name__ == "__main__": main()
├── domain/              → entidades e regras de negócio
│   ├── __init__.py
│   ├── models.py        → RateRecord
│   └── constants.py     → B3_BASE_URL, defaults, EVOLUTION_DAYS
├── application/         → casos de uso do sistema
│   ├── __init__.py
│   ├── use_cases.py     → consolidate_by_year, average_rate_by_year, validate_reference_date (_days_ago tb)
│   └── formatting.py    → format_cli_rows, format_records_csv, format_yearly_rows, format_evolution_csv, _brl
├── infrastructure/      → comunicação com mundo externo
│   ├── __init__.py
│   ├── b3_client.py     → build_payload, encode_payload, build_url, normalize_records, fetch_reference_rates_page, fetch_reference_rates, fetch_rates_download, fetch_historical_rates
│   └── desktop.py       → create_shortcut, shortcut_exists, _detect_desktop_dir, _resolve_executable, _icon_source, SHORTCUT_CHECK_PATH
└── presentation/        → interface com usuário (CLI + GUI + gráficos)
    ├── __init__.py
    ├── cli.py            → parse_args, main (entry point do console_scripts)
    ├── gui.py            → SelicPreApp, DatePicker, launch_gui
    └── charts.py         → render_chart, render_curve_evolution, render_detailed_evolution, render_3d_evolution, _nearest_ticks, _interpolate_rates
```

### 3. Icons como package_data

Em vez de `_SCRIPT_DIR` + path relativo, usar `importlib.resources`:

```python
def _icon_source():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "b3_selic_pre.png")
    return importlib.resources.files("b3_selic_pre").joinpath("icons/b3_selic_pre.png")
```

PyInstaller copia os `datas` para `sys._MEIPASS`, então o fallback frozen continua funcionando.

### 4. pyproject.toml

```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "b3-selic-pre"
version = "0.7.0"
requires-python = ">=3.10"
dependencies = [
    "matplotlib>=3.0.0",
    "Pillow>=10.0.0",
    "pyxclip>=0.2.0",
]

[project.scripts]
b3-selic-pre = "b3_selic_pre.presentation.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
b3_selic_pre = ["icons/*.png"]
```

O `[project.scripts]` entry point permite que o binário seja chamado como `b3-selic-pre` sem caminho.

### 5. PyInstaller spec mantido

O spec tem lógica condicional por SO (ícone, console, UPX, macOS BUNDLE) que `[tool.pyinstaller]` não suporta bem. Mantém-se o arquivo `.spec`, atualizando:
- `Analysis(['b3_selic_pre/__main__.py'])`
- `datas=[('src/b3_selic_pre/icons/b3_selic_pre.png', 'b3_selic_pre')]`

### 6. Makefile

```makefile
install: .venv
	$(VENV_PYTHON) -m pip install -e .
	$(VENV_PYTHON) -m pip install pyinstaller

build: .venv
	MPLBACKEND=Agg $(VENV_PYTHON) -m PyInstaller b3-selic-pre.spec

test: .venv
	$(VENV_PYTHON) -m pytest

clean:
	rm -rf dist/ build/ src/*.egg-info/
```

### 7. Testes puristas

Todos os imports nos testes mudam de `from b3_selic_pre import X` para `from b3_selic_pre.domain.models import RateRecord`, etc. Todos os `mock.patch("b3_selic_pre.X")` são atualizados para o caminho completo do módulo.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Mock paths quebrados após refactor | Atualizar um a um, rodar `pytest` iterativamente |
| `importlib.resources` não funciona em PyInstaller < 5 | O frozen fallback com `sys._MEIPASS` é preservado |
| Alguém roda `python3 b3_selic_pre.py` no diretório antigo | Arquivo removido; README atualizado; erro claro |
| Skills OpenSpec quebram se path do `__version__` mudar | Atualizar skills antes de finalizar a change |
| Circular import entre `infrastructure` e `application` | `infrastructure` não importa `application`; `application` não importa `infrastructure` (inversão de dependência via parâmetros `opener=`) |
| `pytest` descobre testes mas não encontra o pacote | `pip install -e .` antes de rodar; Makefile já garante isso |
