## 1. Scaffold — pacote, pyproject.toml, entry point

- [x] 1.1 Criar `src/b3_selic_pre/` com `__init__.py` (contendo `__version__ = "0.7.0"`) e `__main__.py` (chamando `main()` de `presentation.cli`)
- [x] 1.2 Criar `pyproject.toml` com `[build-system]`, `[project]`, `[project.scripts]`, `[tool.setuptools]`
- [x] 1.3 Remover `requirements.txt`
- [x] 1.4 Criar sub-pacotes vazios: `domain/`, `application/`, `infrastructure/`, `presentation/` (cada um com `__init__.py`)
- [x] 1.5 Mover `icons/` para `src/b3_selic_pre/icons/`; declarar como `package_data` no `pyproject.toml`
- [x] 1.6 Verificar: `pip install -e .` instala sem erros e `python -c "import b3_selic_pre"` funciona

## 2. Domain layer — models e constants

- [x] 2.1 `domain/models.py`: extrair `RateRecord` (dataclass)
- [x] 2.2 `domain/constants.py`: extrair `B3_BASE_URL`, `DEFAULT_*` constants, `EVOLUTION_DAYS`, `SHORTCUT_CHECK_PATH`

## 3. Application layer — use cases e formatting

- [x] 3.1 `application/use_cases.py`: extrair `validate_reference_date`, `consolidate_by_year`, `average_rate_by_year`, `_days_ago`
- [x] 3.2 `application/formatting.py`: extrair `format_cli_rows`, `format_records_csv`, `format_yearly_rows`, `format_evolution_csv`, `_brl`

## 4. Infrastructure layer — B3 client e desktop

- [x] 4.1 `infrastructure/b3_client.py`: extrair `build_payload`, `encode_payload`, `build_url`, `normalize_records`, `fetch_reference_rates_page`, `fetch_reference_rates`, `fetch_rates_download`, `fetch_historical_rates`
- [x] 4.2 `infrastructure/desktop.py`: extrair `create_shortcut`, `shortcut_exists`, `_detect_desktop_dir`, `_resolve_executable`, `_icon_source` (atualizar para `importlib.resources`)

## 5. Presentation layer — CLI, GUI, charts

- [x] 5.1 `presentation/cli.py`: extrair `parse_args`, `main`
- [x] 5.2 `presentation/gui.py`: extrair `SelicPreApp`, `DatePicker`, `launch_gui` (atualizar icon path e `_SCRIPT_DIR`)
- [x] 5.3 `presentation/charts.py`: extrair `render_chart`, `render_curve_evolution`, `render_detailed_evolution`, `render_3d_evolution`, `_nearest_ticks`, `_interpolate_rates`

## 6. Remover arquivo monolítico

- [x] 6.1 Remover `b3_selic_pre.py` da raiz
- [x] 6.2 Verificar que `python -m b3_selic_pre` funciona via entry point

## 7. Atualizar Makefile

- [x] 7.1 `install`: trocar `pip install -r requirements.txt` por `pip install -e .`
- [x] 7.2 `test`: trocar `unittest discover -s tests` por `pytest`
- [x] 7.3 `clean`: adicionar `src/*.egg-info/` e `src/b3_selic_pre.egg-info/`
- [x] 7.4 Manter `build` e `.venv` targets (ajustar spec path se necessário)

## 8. Atualizar PyInstaller spec

- [x] 8.1 `Analysis`: `['src/b3_selic_pre/__main__.py']`
- [x] 8.2 `datas`: `('src/b3_selic_pre/icons/b3_selic_pre.png', 'b3_selic_pre')`
- [ ] 8.3 Remover `hiddenimports` redundantes se todos são resolvidos automaticamente (opcional)

## 9. Atualizar GitHub Actions workflows

- [x] 9.1 `test.yml`: trocar `pip install -r requirements.txt` por `pip install . pytest flake8`
- [ ] 9.2 `release.yml`: verificar que `make install && make build` continua funcionando

## 10. Atualizar testes — imports e mocks

- [x] 10.1 `tests/test_b3_selic_pre.py`: atualizar todos os `from b3_selic_pre import ...` para módulos específicos
- [x] 10.2 `tests/test_b3_selic_pre.py`: atualizar todos os `mock.patch("b3_selic_pre.X")` para caminhos completos
- [x] 10.3 `tests/test_b3_selic_pre_gui.py`: atualizar todos os imports e mocks
- [x] 10.4 Rodar `pytest` e corrigir erros até todos passarem

## 11. Atualizar skills OpenSpec

- [x] 11.1 `release-version/SKILL.md`: trocar path de `b3_selic_pre.py` para `src/b3_selic_pre/__init__.py`
- [x] 11.2 `release-push/release-push.sh`: trocar `$PROJECT_ROOT/b3_selic_pre.py` para `$PROJECT_ROOT/src/b3_selic_pre/__init__.py`
- [x] 11.3 `release-push/SKILL.md`: atualizar menção textual a `b3_selic_pre.py`

## 12. Atualizar README.md

- [x] 12.1 Comandos: `python3 b3_selic_pre.py` → `b3-selic-pre` ou `python3 -m b3_selic_pre`
- [x] 12.2 Instalação: `pip install -r requirements.txt` → `pip install .`
- [x] 12.3 Remover menções ao arquivo único `b3_selic_pre.py`

## 13. Atualizar .gitignore

- [x] 13.1 Remover `!b3-selic-pre.spec` (substituído por `src/*.egg-info/`)
- [x] 13.2 Adicionar `src/*.egg-info/`

## 14. Verificação final

- [x] 14.1 `pip install -e .` funciona (pacote instalado em editable mode)
- [x] 14.2 `pytest` passa (83/83 testes)
- [ ] 14.3 `make build` gera binário em `dist/b3-selic-pre` (precisa de PyInstaller instalado)
- [x] 14.4 `b3-selic-pre --help` e `b3-selic-pre --version` funcionam (entry point)
- [x] 14.5 `python3 -m b3_selic_pre --help` funciona (via `__main__.py`)
