## 1. Domain Layer

- [ ] 1.1 Add `MovimentacaoTesouroDireto` frozen dataclass to `src/b3_selic_pre/domain/models.py`
- [ ] 1.2 Add Tesouro Direto constants to `src/b3_selic_pre/domain/constants.py` (`TESOURO_BASE_URL`, `TESOURO_DATASET_ID`, `TESOURO_CACHE_TTL_MINUTES`)

## 2. Infrastructure Layer

- [ ] 2.1 Implement `fetch_tesouro_metadata()` in `src/b3_selic_pre/infrastructure/tesouro_client.py` using CKAN JSON API with `urllib` and `opener` injection
- [ ] 2.2 Implement `extract_resource_urls()` to parse CSV and PDF URLs from CKAN package_show response
- [ ] 2.3 Implement `fetch_tesouro_csv()` for streaming CSV download with timeout (60s), progress callback, and `ETag`/`If-Modified-Since` header support
- [ ] 2.4 Implement `TesouroCache` class in `src/b3_selic_pre/infrastructure/tesouro_cache.py` with XDG-compliant paths (`~/.cache/b3-selic-pre/tesouro/`), TTL (6h), corrupted file handling, and housekeeping
- [ ] 2.5 Implement `TesouroDiretoClient` in `src/b3_selic_pre/infrastructure/tesouro_cached_client.py` wrapping fetch + cache with `force` parameter

## 3. Application Layer

- [ ] 3.1 Create `src/b3_selic_pre/application/tesouro/__init__.py` subpackage re-exporting `processar_csv()`
- [ ] 3.2 Implement `_processamento.py` with CSV parsing via `csv.Sniffer` + `csv.DictReader`, case-insensitive column mapping, encoding fallback (UTF-8 → Latin-1), data type conversion (dates to ISO 8601, monetary values handling Brazilian locale formatting), and validation
- [ ] 3.3 Implement `filtrar_por_titulo()`, `filtrar_por_periodo()`, and `agregar_por_titulo()` in `_processamento.py`
- [ ] 3.4 Implement `_formatting.py` with tabular text output (aligned columns, Brazilian number formatting) and JSON output (metadata + records)

## 4. Presentation Layer

- [ ] 4.1 Add `--tesouro`, `--titulo`, `--inicio`, `--fim`, and `--json` flags to CLI in `src/b3_selic_pre/presentation/cli.py`
- [ ] 4.2 Implement `handle_tesouro()` CLI handler using `TesouroDiretoClient` + application formatting
- [ ] 4.3 Add "Tesouro Direto" tab in GUI (`src/b3_selic_pre/presentation/gui.py`) with `ttk.Treeview` table, titulo filter dropdown, "Atualizar" button, progress bar, and error/status display
- [ ] 4.4 Implement threading in GUI tab using `threading.Thread` + `root.after()` pattern for non-blocking fetch

## 5. Documentation

- [ ] 5.1 Update `docs/rfcs/RFC-001 - Movimentações do Tesouro Direto.md` to reflect Clean Architecture design, CKAN API usage, `urllib`/`csv` native modules, cache strategy, and layered structure
- [ ] 5.2 Update `docs/PRD.md` to remove "Tesouro Direto" from Não-escopo and add it as P2 feature with description

## 6. Testing

- [ ] 6.1 Write unit tests for `MovimentacaoTesouroDireto` dataclass immutability and field types
- [ ] 6.2 Write unit tests for `tesouro_client.py` using `FakeResponse` to mock CKAN API, CSV download, and error responses
- [ ] 6.3 Write unit tests for `tesouro_cache.py` covering cache hit, cache miss, TTL expiration, corrupted file handling, and housekeeping
- [ ] 6.4 Write unit tests for `_processamento.py` covering CSV parsing (comma and semicolon), column mapping, encoding fallback, Brazilian locale number parsing, and filter functions
- [ ] 6.5 Write unit tests for `_formatting.py` covering tabular and JSON output formats
- [ ] 6.6 Run `make lint test` and verify all tests pass
