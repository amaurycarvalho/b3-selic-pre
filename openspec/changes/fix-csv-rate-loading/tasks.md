## 1. Cliente B3: retry, fonte e completude

- [x] 1.1 Adicionar constantes de retry (`EMPTY_RETRY_ATTEMPTS`, backoff) e o helper `_retry_empty` em `infrastructure/b3_client.py`, com `sleep` injetável; verificar com teste unitário que corpo vazio é repetido e que `ValueError` não é repetido.
- [x] 1.2 Implementar `fetch_rates_for_date(date_str, today=None, ...)` com a regra hoje=`GetList` / passado=`GetDownloadFile`+fallback `GetList`, devolvendo também a origem; verificar com testes dos três cenários (hoje, passado com CSV, passado com CSV vazio).
- [x] 1.3 Atualizar `fetch_reference_rates_page` para devolver `total_records`/`total_pages` de `page.*`, com fallback para `totalCount`; verificar com teste de resposta real (page.totalRecords=279, totalPages=3) e de resposta legada.
- [x] 1.4 Atualizar `fetch_reference_rates` para buscar `1..total_pages`, repetir página esperada vazia, rejeitar `totalPages > max_pages` e validar `len(records) == total_records`; verificar com testes de paginação completa, página vazia transitória, coleta incompleta e limite excedido.
- [x] 1.5 Corrigir `fetch_rates_download` para `splitlines()`, `strip()` por campo, ignorar cabeçalho/linhas vazias e rejeitar linha malformada com `ValueError`; verificar com testes de CSV `\r\n`, linha em branco, `rate` sem `\r` e linha inválida.
- [x] 1.6 Fazer `fetch_historical_rates` usar `fetch_rates_for_date` por data e isolar falhas por data (data indisponível vira lista vazia, sem interromper as demais); verificar com teste de 5 datas com uma indisponível e com todas indisponíveis.

## 2. Cache: integridade e invalidação

- [x] 2.1 Adicionar `schema_version`, `complete`, `expected_count` e `source` ao payload de `DiskCache.put`; verificar com teste de payload gravado para resultado completo.
- [x] 2.2 Fazer `DiskCache.put`/`CachedB3Client` só gravarem resultados não vazios e completos, inclusive com `force=True`; verificar que vazio/parcial não cria arquivo e não sobrescreve entrada válida.
- [x] 2.3 Fazer `DiskCache.get` tratar como miss e apagar entradas vazias, incompletas, com contagem divergente ou legadas sem `schema_version: 2`; verificar que uma entrada legada/parcial é re-buscada uma vez.
- [x] 2.4 Integrar `CachedB3Client.fetch_rates_for_date`/`fetch_historical_rates` à nova validação e à seleção de fonte; verificar com testes de cache hit, miss, força e data indisponível não cacheada.
- [x] 2.5 Verificar que `CachedB3Client.fetch_rates_download` e `fetch_reference_rates` mantêm a interface pública e os testes existentes, ajustando apenas o comportamento de cache.

## 3. Apresentação: GUI e CLI

- [x] 3.1 Atualizar `presentation/gui/fetch.py` para usar `CachedB3Client.fetch_rates_for_date` na busca única e remover a duplicação do `if today`; verificar com teste headless do view-model/fluxo de busca.
- [x] 3.2 Ajustar `handle_historical_fetch_success` para aceitar dicionário com datas vazias, listar datas indisponíveis na status bar e não redesenhar gráfico inválido; verificar com teste headless do estado e da mensagem.
- [x] 3.3 Atualizar `presentation/cli.py` para usar a mesma seleção de fonte; verificar com testes de CLI para hoje (GetList), data passada (CSV) e falha persistente (exit não zero).
- [x] 3.4 Ajustar `presentation/view_model.py` para `has_historical` considerar apenas listas não vazias e `chart_mode` cair para o modo base sem histórico utilizável; verificar com testes de view-model.
- [x] 3.5 Atualizar `presentation/charts.py` e `application/chart_data.py`: `nearest_ticks` devolve `[]` com entrada vazia e os renderizadores de evolução/3D filtram datas vazias ou mostram estado vazio; verificar com testes de renderização headless (Agg) para mapping vazio, lista vazia por data e mistura de datas com/sem registros.

## 4. Regressão e documentação interna

- [x] 4.1 Adicionar/ajustar testes unitários em `tests/test_b3_client.py`, `tests/test_disk_cache.py`, `tests/test_cli.py`, `tests/test_view_model.py` e `tests/test_charts_render.py` cobrindo os cenários das specs; verificar que todos passam.
- [x] 4.2 Revisar `tests/test_application_services.py`, `tests/test_b3_selic_pre.py` e testes de GUI afetados; manter testes de Tk marcados `@pytest.mark.ui` e não aumentar o budget de `tests/test_ui_test_budget.py`.
- [x] 4.3 Rodar `make lint` e corrigir eventuais problemas.
- [x] 4.4 Rodar `make complexity` e resolver qualquer regressão de complexidade.
- [x] 4.5 Rodar `make test` (suíte completa, justificada por alterar infraestrutura compartilhada, cache e contrato de carregamento) e corrigir falhas.
- [x] 4.6 Smoke manual: abrir a GUI, buscar hoje (deve usar GetList), buscar uma data passada (deve usar CSV), ativar evolução e confirmar que datas indisponíveis não quebram o gráfico.
- [x] 4.7 Verificar e cobrir o cache da data corrente via `GetList`: a primeira chamada grava com TTL e a segunda chamada usa o cache; verificar com teste de integração em `tests/test_disk_cache.py`.
- [x] 4.8 Aumentar o retry de corpo vazio para 6 tentativas com backoff exponencial e jitter (limite de 4 s por espera); verificar com testes de contagem de tentativas, jitter determinístico e orçamento.
