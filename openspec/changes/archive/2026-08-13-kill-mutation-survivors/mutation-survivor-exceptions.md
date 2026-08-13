# Mutantes equivalentes (lista de exceção)

Mutantes sobreviventes classificados como **equivalentes** (D3 do design do change `kill-mutation-survivors`): o comportamento é idêntico ao original para todos os inputs, logo nenhum teste pode matá-los. Eles são registrados aqui com o motivo da equivalência e **nenhum teste** é criado para eles.

Formato: `chave_do_mutante | módulo.função :: mutmut_N | motivo da equivalência`

---

## application.use_cases

- `b3_selic_pre.application.use_cases.x__days_ago__mutmut_2` | `_days_ago :: 2` | `replace(tzinfo=timezone.utc)` → `replace(tzinfo=None)`; a saída é `datetime.date`, cujo `isoformat()` é idêntico com ou sem tzinfo.
- `b3_selic_pre.application.use_cases.x_validate_reference_date__mutmut_2` | `validate_reference_date :: 2` | idem: `replace(tzinfo=...)` não altera `date().isoformat()`.

## infrastructure.disk_cache

- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_load_payload__mutmut_3` | `_load_payload :: 3` | `encoding=None` equivale ao default (utf-8 no POSIX); leitura idêntica para JSON ASCII.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_load_payload__mutmut_5` | `_load_payload :: 5` | `encoding="UTF-8"` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_load_payload__mutmut_6` | `_load_payload :: 6` | `unlink(missing_ok=None)` comporta-se como `False`; o arquivo existe no ponto da chamada (acabou de ser lido/falhou o parse), então não há diferença.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_load_payload__mutmut_7` | `_load_payload :: 7` | idem: `missing_ok=False` vs `True` é indistinguível porque o arquivo existe.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_get__mutmut_10` | `get :: 10` | `unlink(missing_ok=None)`; arquivo existe no momento do unlink (foi carregado ou falhou o parse).
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_get__mutmut_11` | `get :: 11` | idem: `missing_ok=False`.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_get__mutmut_13` | `get :: 13` | idem: `unlink(missing_ok=None)` no caminho de erro de parse.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_get__mutmut_14` | `get :: 14` | idem: `missing_ok=False`.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_put__mutmut_24` | `put :: 24` | `write_text(encoding=None)` usa o encoding default; conteúdo ASCII, bytes idênticos.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_put__mutmut_26` | `put :: 26` | `write_text(...)` sem encoding → default; conteúdo ASCII, idêntico.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_put__mutmut_28` | `put :: 28` | `ensure_ascii=None` é falsy como `False`; conteúdo ASCII, idêntico.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_put__mutmut_30` | `put :: 30` | `json.dumps(data)` sem `ensure_ascii` (default `True`); conteúdo ASCII, idêntico.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_put__mutmut_31` | `put :: 31` | `ensure_ascii=True` vs `False`; conteúdo ASCII, idêntico.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁ_put__mutmut_33` | `put :: 33` | `encoding="UTF-8"` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁhousekeeping__mutmut_14` | `housekeeping :: 14` | `unlink(missing_ok=None)`; arquivos vêm do `glob`, sempre existem.
- `b3_selic_pre.infrastructure.disk_cache.xǁDiskCacheǁhousekeeping__mutmut_15` | `housekeeping :: 15` | idem: `missing_ok=False`.

## infrastructure.b3_client

- `b3_selic_pre.infrastructure.b3_client.x_encode_payload__mutmut_11` | `encode_payload :: 11` | `encode("UTF-8")` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.b3_client.x_encode_payload__mutmut_13` | `encode_payload :: 13` | `decode("UTF-8")` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_reference_rates_page__mutmut_21` | `fetch_reference_rates_page :: 21` | `decode("UTF-8")` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_reference_rates__mutmut_3` | `fetch_reference_rates :: 3` | `opener = None` dentro do `if opener is None`; o callee re-aplica o default, comportamento idêntico.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_reference_rates__mutmut_32` | `fetch_reference_rates :: 32` | `page_size >= 0`; como `page_size <= 0` já valida antes, a condição é sempre verdadeira.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_rates_download__mutmut_24` | `fetch_rates_download :: 24` | `encode("UTF-8")` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_rates_download__mutmut_26` | `fetch_rates_download :: 26` | `decode("UTF-8")` é o mesmo codec de `"utf-8"`.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_rates_download__mutmut_37` | `fetch_rates_download :: 37` | `decode("LATIN-1")` é o mesmo codec de `"latin-1"`.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_rates_download__mutmut_44` | `fetch_rates_download :: 44` | `decode("LATIN-1")` é o mesmo codec de `"latin-1"`.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_rates_download__mutmut_46` | `fetch_rates_download :: 46` | `split(None)` vs `split("\n")`; no CSV da B3 os campos numéricos não contêm espaços, o número de registros é idêntico.
- `b3_selic_pre.infrastructure.b3_client.x_fetch_historical_rates__mutmut_2` | `fetch_historical_rates :: 2` | `datetime.now(None)` vs `now(timezone.utc)`; `.date().isoformat()` coincide no horário de execução (datetime importado localmente, sem hook externo).

## application.analyze._evolucao

- `b3_selic_pre.application.analyze._evolucao.x_classificar_movimento__mutmut_8` | `classificar_movimento :: 8` | `max(...) <= threshold`; quando `max == threshold`, as demais condições exigem valores estritamente além do limiar, resultado idêntico.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_politica_monetaria__mutmut_24` | `classificar_politica_monetaria :: 24` | fallback final inalcançável com `slightly_restrictive_min >= neutral_max` no Settings default; comportamento idêntico para todos os inputs reais.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_politica_monetaria__mutmut_25` | `:: 25` | idem.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_politica_monetaria__mutmut_26` | `:: 26` | idem.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_premio_prazo__mutmut_10` | `classificar_premio_prazo :: 10` | `abs(delta_slope) < increased_min`; no ponto de fronteira o fallback devolve o mesmo string "Praticamente estável".
- `b3_selic_pre.application.analyze._evolucao.x_classificar_premio_prazo__mutmut_19` | `:: 19` | `<= -increased_min`; a fronteira cai no ramo anterior (`abs(...) <= increased_min`), resultado idêntico.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_premio_prazo__mutmut_20` | `:: 20` | `< +increased_min`; para deltas negativos o sinal não altera o ramo alcançado.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_premio_prazo__mutmut_24` | `:: 24` | fallback final inalcançável (`return "Praticamente estável"`); todos os inputs são cobertos pelos ramos anteriores.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_premio_prazo__mutmut_25` | `:: 25` | idem.
- `b3_selic_pre.application.analyze._evolucao.x_classificar_premio_prazo__mutmut_26` | `:: 26` | idem.
- `b3_selic_pre.application.analyze._evolucao.x_derivar_direcao_geral__mutmut_2` | `derivar_direcao_geral :: 2` | comparação `"XXEstávelXX"`; fallback devolve a mesma string, resultado idêntico para todos os regimes.
- `b3_selic_pre.application.analyze._evolucao.x_derivar_direcao_geral__mutmut_3` | `:: 3` | idem.
- `b3_selic_pre.application.analyze._evolucao.x_derivar_direcao_geral__mutmut_4` | `:: 4` | idem.
- `b3_selic_pre.application.analyze._evolucao.x_analyze_evolution__mutmut_54` | `analyze_evolution :: 54` | `derivar_direcao_geral(regime, None)`; quando `intensidade == "Muito Fraca"` o regime é "Estável" e o resultado não depende do segundo argumento.
- `b3_selic_pre.application.analyze._evolucao.x_analyze_evolution__mutmut_68` | `analyze_evolution :: 68` | `statements=[]` removido; o default `field(default_factory=list)` produz o mesmo valor.
- `b3_selic_pre.application.analyze._evolucao.x_analyze_evolution__mutmut_78` | `analyze_evolution :: 78` | `market_message=""` removido; o default do dataclass é o mesmo string.

## application.analyze._texto

- `b3_selic_pre.application.analyze._texto.x_montar_resumo_executivo__mutmut_31` | `montar_resumo_executivo :: 31` | `classificar_premio(inclinacao_bps, None)`; `classificar_premio` ignora `config`, resultado idêntico.

## presentation.cli

- `b3_selic_pre.presentation.cli.x_parse_args__mutmut_12` | `parse_args :: 12` | `default=None` removido do argumento `date`; é o default do próprio `argparse`, comportamento idêntico.

## presentation.settings

- `b3_selic_pre.presentation.settings.xǁSettingsǁ_load__mutmut_2` | `Settings._load :: 2` | `read_text(encoding=None)` usa o encoding default; conteúdo JSON idêntico.
- `b3_selic_pre.presentation.settings.xǁSettingsǁ_load__mutmut_4` | `Settings._load :: 4` | `encoding="UTF-8"` é o mesmo codec de `"utf-8"`.

## infrastructure.desktop

- `b3_selic_pre.infrastructure.desktop.x_resolve_executable__mutmut_3` | `_resolve_executable :: 3` | `getattr(sys, "frozen", None)` vs `False`; ambos falsy quando o atributo está ausente.
- `b3_selic_pre.infrastructure.desktop.x_icon_source__mutmut_3` | `_icon_source :: 3` | idem: default `None` é falsy como `False`.

## presentation.charts (não cobertos por custo × benefício — D5.7)

Conforme a decisão D5 item 7 do design, os survivors restantes de `presentation.charts` são mutações **visuais** (cores, alphas, larguras de linha, caixa/acentuação de rótulos, `subplots_adjust`, `colorbar`, tolerâncias e limites de `range` para ticks) cuja distinção exigiria asserts frágeis de pixels/layout com custo alto e baixo valor de cobertura de lógica. São **100 mutantes** em `render_chart` (39), `render_detailed_evolution` (22), `render_curve_evolution` (20), `render_3d_evolution` (15), `_daily_3d_data` (2), `_interpolate_3d_surface` (1) e `_draw_evolution_arrows` (1). Exemplos representativos:

- `render_chart :: mutmut_94/96/103/107/109/110/166-170/175/179/185/187/189` | parâmetros de `range`/tolerância de `_nearest_ticks` (ticks de anos e dias úteis); só alteram marcação visual do eixo, e para dados típicos produzem a mesma lista de ticks.
- `render_curve_evolution :: mutmut_29-33` | `colors`/`alphas`/`linewidths` de `np.linspace`; só muda o gradiente visual das linhas.
- `render_3d_evolution :: mutmut_115-121` | rótulo/case de `colorbar` e `shrink`; cosmético.
- `render_3d_evolution :: mutmut_143-153` | parâmetros de `subplots_adjust`; layout visual.
- `render_detailed_evolution :: mutmut_31-33` | gradiente de cores das linhas; cosmético.
- `_daily_3d_data :: mutmut_48` e `_interpolate_3d_surface :: mutmut_58/59` | `np.nan` → `None` em arrays float; ambos são convertidos em `nan`, comportamento idêntico.
- `_draw_evolution_arrows :: mutmut_17` | `% 5` → `% 6`; com 5 datas (EVOLUTION_DAYS), `(i-1)%5 == (i-1)%6` para todos os índices, idêntico.
