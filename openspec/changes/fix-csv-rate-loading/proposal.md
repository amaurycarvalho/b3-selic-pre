## Why

O carregamento da curva está vulnerável a respostas `200 OK` com corpo vazio da B3: o `GetDownloadFile` (CSV) e o `GetList` falham de forma intermitente, o resultado vazio/parcial é cacheado como se fosse válido e o gráfico pode ficar em branco ou lançar exceção. A change `migrate-b3-api-first` foi descartada; a correção deve preservar o CSV como fonte principal para datas anteriores e manter o `GetList` apenas para a data corrente.

## What Changes

- Centralizar a seleção de fonte: **hoje** usa `GetList`; **datas anteriores** usam `GetDownloadFile` como fonte primária, com `GetList` apenas como fallback após esgotar as tentativas do CSV.
- Adicionar retry com backoff exponencial e jitter para respostas `200` com corpo vazio, tanto no CSV quanto no `GetList`, com até 6 tentativas e sem mascarar erros de schema.
- Validar completude do `GetList` por `page.totalRecords`/`page.totalPages`: buscar todas as páginas, repetir páginas vazias e falhar explicitamente se a quantidade coletada não coincidir.
- Corrigir o parser CSV para `splitlines()` e `strip()` por campo, removendo `\r`, ignorando linhas vazias e rejeitando linhas malformadas.
- Não cachear resultados vazios ou parciais; resultados vazios/parciais já gravados passam a ser tratados como cache miss e são descartados.
- Garantir que o resultado bem-sucedido da data corrente via `GetList` seja cacheado com TTL e reutilizado nas próximas consultas.
- Proteger os gráficos e o view-model contra listas vazias: exibir estado vazio informativo em vez de lançar `ValueError` ou deixar a área em branco.
- Alinhar a CLI à mesma seleção de fonte da GUI, preservando o formato de saída atual.

## Capabilities

### New Capabilities

- `b3-rate-source`: contrato de carregamento das taxas na B3 — seleção de fonte por data, retry para corpo vazio, paginação/completude do `GetList`, parsing do CSV e classificação de erros.

### Modified Capabilities

- `desktop-rate-browser`: a GUI passa a usar a seleção de fonte por data e a exibir estado vazio/erro sem travar quando o histórico vier vazio ou incompleto.
- `curve-evolution`: a busca das 5 datas passa a usar retry/validação e o gráfico de evolução passa a tolerar datas ausentes ou listas vazias.
- `disk-cache`: resultados vazios/parciais deixam de ser cacheados; cache vazio é tratado como miss e caches legados incompletos são invalidados de forma controlada.

## Impact

- `src/b3_selic_pre/infrastructure/b3_client.py`: fachada com a seleção de fonte por data e a orquestração histórica.
- Novos módulos `b3_retry.py`, `b3_list.py` e `b3_download.py`: retry para corpo vazio, paginação/completude do `GetList` e parser CSV.
- `src/b3_selic_pre/infrastructure/cached_client.py` e `disk_cache.py`: não cachear vazio/parcial, metadados de completude e invalidação de cache legado.
- `src/b3_selic_pre/presentation/gui/fetch.py`, `chart.py` e `presentation/view_model.py`: estado vazio e fallback de modo de gráfico.
- `src/b3_selic_pre/presentation/charts.py` e `application/chart_data.py`: guardas contra listas vazias.
- `src/b3_selic_pre/presentation/cli.py`: seleção de fonte por data.
- Testes headless de cliente, cache, CLI, view-model e renderização; sem novas dependências de runtime.
