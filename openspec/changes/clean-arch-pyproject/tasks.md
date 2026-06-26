## 1. Scaffold — pacote, pyproject.toml, entry point

- [ ] 1.1 Criar `src/b3_selic_pre/` com `__init__.py` (contendo `__version__ = "0.7.0"`) e `__main__.py` (chamando `main()` de `presentation.cli`)
- [ ] 1.2 Criar `pyproject.toml` com `[build-system]`, `[project]`, `[project.scripts]`, `[tool.setuptools]`
- [ ] 1.3 Remover `requirements.txt`
- [ ] 1.4 Criar sub-pacotes vazios: `domain/`, `application/`, `infrastructure/`, `presentation/` (cada um com `__init__.py`)
- [ ] 1.5 Mover `icons/` para `src/b3_selic_pre/icons/`; declarar como `package_data` no `pyproject.toml`
- [ ] 1.6 Verificar: `pip install -e .` instala sem erros e `python -c "import b3_selic_pre"` funciona

## 2. Domain layer — models e constants

- [ ] 2.1 `domain/models.py`: extrair `RateRecord` (dataclass)
- [ ] 2.2 `domain/constants.py`: extrair `B3_BASE_URL`, `DEFAULT_*` constants, `EVOLUTION_DAYS`, `SHORTCUT_CHECK_PATH`

## 3. Application layer — use cases e formatting

- [ ] 3.1 `application/use_cases.py`: extrair `validate_reference_date`, `consolidate_by_year`, `average_rate_by_year`, `_days_ago`
- [ ] 3.2 `application/formatting.py`: extrair `format_cli_rows`, `format_records_csv`, `format_yearly_rows`, `format_evolution_csv`, `_brl`

## 4. Infrastructure layer — B3 client e desktop

- [ ] 4.1 `infrastructure/b3_client.py`: extrair `build_payload`, `encode_payload`, `build_url`, `normalize_records`, `fetch_reference_rates_page`, `fetch_reference_rates`, `fetch_rates_download`, `fetch_historical_rates`
- [ ] 4.2 `infrastructure/desktop.py`: extrair `create_shortcut`, `shortcut_exists`, `_detect_desktop_dir`, `_resolve_executable`, `_icon_source` (atualizar para `importlib.resources`)

## 5. Presentation layer — CLI, GUI, charts

- [ ] 5.1 `presentation/cli.py`: extrair `parse_args`, `main`
- [ ] 5.2 `presentation/gui.py`: extrair `SelicPreApp`, `DatePicker`, `launch_gui` (atualizar icon path e `_SCRIPT_DIR`)
- [ ] 5.3 `presentation/charts.py`: extrair `render_chart`, `render_curve_evolution`, `render_detailed_evolution`, `render_3d_evolution`, `_nearest_ticks`, `_interpolate_rates`

## 6. Remover arquivo monolítico

- [ ] 6.1 Remover `b3_selic_pre.py` da raiz
- [ ] 6.2 Verificar que `python -m b3_selic_pre` funciona via entry point

## 7. Atualizar Makefile

- [ ] 7.1 `install`: trocar `pip install -r requirements.txt` por `pip install -e .`
- [ ] 7.2 `test`: trocar `unittest discover -s tests` por `pytest`
- [ ] 7.3 `clean`: adicionar `src/*.egg-info/` e `src/b3_selic_pre.egg-info/`
- [ ] 7.4 Manter `build` e `.venv` targets (ajustar spec path se necessário)

## 8. Atualizar PyInstaller spec

- [ ] 8.1 `Analysis`: `['b3_selic_pre/__main__.py']`
- [ ] 8.2 `datas`: `('src/b3_selic_pre/icons/b3_selic_pre.png', 'b3_selic_pre')`
- [ ] 8.3 Remover `hiddenimports` redundantes se todos são resolvidos automaticamente (opcional)

## 9. Atualizar GitHub Actions workflows

- [ ] 9.1 `test.yml`: trocar `pip install -r requirements.txt` por `pip install .[dev]` (ou simplesmente `pip install . pytest flake8`)
- [ ] 9.2 `release.yml`: verificar que `make install && make build` continua funcionando

## 10. Atualizar testes — imports e mocks

- [ ] 10.1 `tests/test_b3_selic_pre.py`: atualizar todos os `from b3_selic_pre import ...` para módulos específicos
- [ ] 10.2 `tests/test_b3_selic_pre.py`: atualizar todos os `mock.patch("b3_selic_pre.X")` para caminhos completos
- [ ] 10.3 `tests/test_b3_selic_pre_gui.py`: atualizar todos os imports e mocks
- [ ] 10.4 Rodar `pytest` e corrigir erros até todos passarem

## 11. Atualizar skills OpenSpec

- [ ] 11.1 `release-version/SKILL.md`: trocar path de `b3_selic_pre.py` para `src/b3_selic_pre/__init__.py` (ou manter como `b3_selic_pre/__init__.py` para o `sed` funcionar)
- [ ] 11.2 `release-push/release-push.sh`: trocar `$PROJECT_ROOT/b3_selic_pre.py` para `$PROJECT_ROOT/src/b3_selic_pre/__init__.py`
- [ ] 11.3 `release-push/SKILL.md`: atualizar menção textual a `b3_selic_pre.py`

## 12. Atualizar README.md

- [ ] 12.1 Comandos: `python3 b3_selic_pre.py` → `b3-selic-pre` ou `python3 -m b3_selic_pre`
- [ ] 12.2 Instalação: `pip install -r requirements.txt` → `pip install .`
- [ ] 12.3 Remover menções ao arquivo único `b3_selic_pre.py`

## 13. Atualizar .gitignore

- [ ] 13.1 Remover `!b3-selic-pre.spec` se não for mais necessário (ou manter)
- [ ] 13.2 Adicionar `src/*.egg-info/`

## 14. Verificação final

- [ ] 14.1 `make install` funciona e cria .venv com o pacote instalado em editable mode
- [ ] 14.2 `make test` passa (todos os testes)
- [ ] 14.3 `make build` gera binário em `dist/b3-selic-pre`
- [ ] 14.4 `b3-selic-pre --help` e `b3-selic-pre --version` funcionam (entry point)
- [ ] 14.5 `python3 -m b3_selic_pre --help` funciona (via `__main__.py`)
