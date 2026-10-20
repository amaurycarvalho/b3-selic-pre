## Context

Ver `proposal.md` — Why. O código atual já usa `GetList` para hoje e `GetDownloadFile` para datas passadas em parte dos caminhos, mas a seleção está duplicada entre `b3_client`, `cached_client`, GUI e CLI. O `GetList` lê `totalCount` (campo que não existe mais), a paginação para na primeira página curta e tanto o CSV quanto o `GetList` aceitam corpo vazio como sucesso. O cache grava esse resultado e, para datas passadas, nunca expira. A camada de gráficos não tolera listas vazias.

## Goals / Non-Goals

**Goals:**
- Uma única regra de seleção de fonte, reutilizada por GUI, CLI, busca histórica e cache.
- Retry limitado para corpo vazio, sem retry para erros de dados.
- Completude verificável no `GetList` e parser CSV estrito.
- Cache auto-recuperável: vazio/parcial/legado nunca é servido como válido.
- Gráficos e view-model à prova de listas vazias.

**Non-Goals:**
- Migrar para `GetProducts`/`GetDate` ou trocar `urllib` por `requests`.
- Alterar o formato de saída da CLI, o layout da GUI ou a API pública existente.
- Implementar calendário de feriados da B3.
- Remover o fallback CSV/`GetList`; apenas definir a ordem e a validação.

## Decisions

### 1. Seleção de fonte centralizada

Adicionar em `infrastructure/b3_client.py` (fachada) uma função `fetch_rates_for_date(date_str, today=None, ...)` que:
- usa `fetch_reference_rates` quando `date_str == today`;
- usa `fetch_rates_download` quando `date_str < today`;
- se o CSV continuar vazio após os retries, tenta `fetch_reference_rates` da mesma data;
- devolve também a origem (`"GetList"` ou `"GetDownloadFile"`) para o `source_callback`.

`CachedB3Client` ganha um método equivalente que aplica cache; `fetch.py` e `cli.py` passam a chamá-lo em vez de repetir o `if today`. `fetch_historical_rates` (com e sem cache) usa a mesma função por data. A paginação do `GetList` fica em `b3_list.py`, o CSV em `b3_download.py` e o retry em `b3_retry.py`; `b3_client.py` reexporta a interface pública e concentra a seleção de fonte.

**Alternativa rejeitada:** manter o `if` duplicado em cada chamador. Foi a origem da divergência atual (a CLI usa `GetList` até para datas passadas).

### 2. Retry para corpo vazio

Criar em `infrastructure/b3_retry.py` o helper `retry_empty(operation, *, date, source, attempts=6, backoff=(0.5, 1.0, 2.0, 4.0, 4.0), sleep=time.sleep, random_fn=random.random)`:
- repete somente quando o resultado é vazio (corpo vazio no CSV ou `results` vazio no `GetList`);
- não repete `ValueError` de schema/parse;
- aplica backoff exponencial com jitter completo (`ceiling * random_fn()`), limitado a 4 s por espera;
- após o limite, lança `CommunicationError` com data, fonte e, quando aplicável, esperado/coletado.

Os valores ficam em constantes de módulo para permitir ajuste e para que os testes injetem `sleep` e `random_fn`. O orçamento de espera fica em ~5,75 s esperados e ~11,5 s no pior caso, além dos timeouts HTTP existentes.

**Alternativa rejeitada:** retry HTTP genérico. O status é `200`, então o transporte não tem como distinguir corpo vazio de resposta legítima.

### 3. Paginação e completude do GetList

Em `infrastructure/b3_list.py`, `fetch_reference_rates_page` passa a devolver também os metadados da página:
- `total_records`: `page.totalRecords`, com fallback para o `totalCount` de topo (compatibilidade com testes/respostas antigas);
- `total_pages`: `page.totalPages`, com fallback calculado por `ceil(total_records / page_size)`.

`fetch_reference_rates`:
- busca de `1` até `total_pages` quando o total é conhecido;
- se uma página esperada vier vazia, reaplica o retry do item 2;
- se `total_pages` exceder `max_pages`, rejeita sem continuar;
- ao final, compara `len(records)` com `total_records`; divergência vira `CommunicationError` e o resultado não é cacheado;
- se `total_records` não existir (resposta legada), mantém o critério antigo de parar na primeira página curta, mas ainda exige resultado não vazio e não cacheia parcial.

### 4. Parser CSV

Em `infrastructure/b3_download.py`, `fetch_rates_download` passa a:
- usar `text.splitlines()` (cobre `\n` e `\r\n`);
- ignorar a primeira linha não vazia (cabeçalho) e linhas em branco;
- aplicar `strip()` em cada campo;
- exigir quatro campos por linha (`descrição;dias úteis;dias corridos;taxa`);
- converter `day252`/`day360` para inteiro e manter `rate` sem `\r`;
- lançar `ValueError` em linha malformada, em vez de descartar silenciosamente.

O número de registros parseados é a própria expectativa de completude do CSV; se alguma linha falhar, o resultado não é considerado completo.

### 5. Cache: metadados, invalidação e não-gravação

O payload do cache passa a incluir:
- `schema_version: 2`;
- `complete: true`;
- `expected_count` (quando conhecido; `page.totalRecords` no `GetList`, contagem parseada no CSV);
- `source` (`"GetList"` ou `"GetDownloadFile"`).

Regras:
- `put` só grava resultado não vazio e completo;
- `get` trata como miss e apaga quando `schema_version` ausente/< 2, `complete` falso, `records` vazio ou `expected_count` divergente;
- isso invalida automaticamente o cache legado (inclusive o caso real de `2026-10-12` com 200/279 registros) na primeira leitura de cada data;
- `force=True` com resultado vazio/parcial não sobrescreve uma entrada válida existente;
- resultados da data corrente via `GetList` são gravados com `ttl_minutes` (30 por padrão) e servidos do cache na próxima chamada enquanto o TTL for válido; entradas expiradas são descartadas e re-buscadas.

**Alternativa rejeitada:** aceitar cache legado não vazio. Manteria curvas truncadas já gravadas, que é exatamente o sintoma atual.

### 6. Orquestração do histórico

`fetch_historical_rates` executa cada data isoladamente. Um `CommunicationError` por data:
- não grava cache;
- é registrado como data indisponível (lista vazia no dicionário);
- não cancela as demais datas.

Assim, o modo evolução consegue renderizar as curvas disponíveis e reportar as ausentes. Se todas as datas ficarem vazias, o dicionário ainda é devolvido com as 5 chaves vazias e a GUI mostra estado vazio/base view. A busca de uma única data continua propagando `CommunicationError` para o usuário.

### 7. Guardas de gráfico e view-model

- `nearest_ticks` devolve `[]` quando `all_values` está vazio.
- `render_curve_evolution`, `render_detailed_evolution` e `render_3d_evolution` filtram datas sem registros; se sobrar zero, usam `_render_empty`.
- `GuiViewModel.has_historical` passa a considerar `any(records for records in historical_data.values())`; `chart_mode` cai para o modo base quando não há curva utilizável.
- `handle_historical_fetch_success` mantém o dicionário completo, mas a mensagem de status lista as datas sem registros; não chama renderização que possa lançar exceção.

### 8. Testes e camadas

- Testes de cliente, cache, CLI, view-model e renderização são headless.
- Testes de GUI que precisem de Tk continuam marcados `@pytest.mark.ui`; não aumentar o budget de `tests/test_ui_test_budget.py`.
- O retry é testado com `sleep` injetado, sem esperas reais.
- Nenhuma dependência nova de runtime.

## Risks / Trade-offs

- **Latência extra em falhas transitórias** → limite de 6 tentativas e backoff exponencial com jitter, limitado a 4 s por espera (~11,5 s no pior caso).
- **Invalidação única do cache legado** → re-download de cada data na primeira leitura após a atualização; aceitável para corrigir curvas truncadas.
- **Data genuinamente sem dados (feriado/fora da janela)** → após retries e fallback, a busca única reporta falha de comunicação; o histórico reporta a data como indisponível e segue com as demais.
- **Respostas sem `page` (legado/testes)** → fallback para `totalCount` e para o critério de página curta, mantendo compatibilidade.
- **Retry pode mascarar indisponibilidade real** → a mensagem final inclui data, fonte e contagens esperadas/obtidas.
- **Mudança de schema do cache** → cache antigo é descartado; não há migração de dados necessária.
