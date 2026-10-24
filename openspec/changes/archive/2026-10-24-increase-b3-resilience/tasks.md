# Tasks

## 1. Timeout centralizado de 60 s

- [x] 1.1 Adicionar `DEFAULT_B3_TIMEOUT_SECONDS = 60` em `src/b3_selic_pre/domain/constants.py` e usá-lo como default em `b3_list.fetch_reference_rates_page`, `b3_list.fetch_reference_rates`, `b3_download.fetch_rates_download` e `b3_client.fetch_rates_for_date`; verificar com `pytest tests/test_b3_client.py` que os timeouts chegam como 60 ao opener.
- [x] 1.2 Atualizar as asserções de timeout em `tests/test_b3_client.py` de 30 para 60 e verificar que os testes de `GetList` e `GetDownloadFile` passam.
- [x] 1.3 Atualizar a seção "Retry e timeouts" de `docs/misc/datasources.md` com o timeout de 60 s e verificar que a documentação cita o valor correto.

## 2. Retry de falhas transientes e respostas vazias

- [x] 2.1 Mover a tupla de exceções de comunicação para `src/b3_selic_pre/infrastructure/b3_retry.py` como `TRANSIENT_ERRORS` e reexportá-la em `b3_client.py` como `COMMUNICATION_EXCEPTIONS`; verificar que `tests/test_communication_errors.py` e `tests/test_b3_client.py` continuam passando.
- [x] 2.2 Substituir o loop de `retry_empty` por um único loop com orçamentos independentes: 6 tentativas para resultado vazio, 3 para exceções transientes, backoff exponencial com jitter, erro de dados propagado na primeira ocorrência e `CommunicationError` ao esgotar; cobrir com testes de timeout transitório, timeout persistente, exceção de dados sem retry, vazio com 6 tentativas e jitter.
- [x] 2.3 Aplicar o novo retry em `_fetch_page` (`GetList`) e em `fetch_rates_download` (`GetDownloadFile`); verificar com testes que uma página vazia ainda tenta 6 vezes e que um timeout tenta 3 vezes.
- [x] 2.4 Garantir que `fetch_rates_for_date` cai para `GetList` quando o `GetDownloadFile` esgota timeouts ou falhas transientes; adicionar teste de fallback após timeout e verificar que erros de CSV continuam propagando sem fallback.
- [x] 2.5 Atualizar a seção "Retry e timeouts" de `docs/misc/datasources.md` com os dois orçamentos (6 vazios, 3 transientes), a lista de exceções e o fallback após falha transiente; verificar que a documentação não afirma mais que o retry é só para vazio.

## 3. TTL de 6 horas para a data corrente

- [x] 3.1 Alterar o default de `CachedB3Client.__init__` de `ttl_minutes=30` para `ttl_minutes=360` em `src/b3_selic_pre/infrastructure/cached_client.py`; atualizar apenas as asserções e expectativas de default em `tests/test_disk_cache.py` e verificar com `pytest tests/test_disk_cache.py`.
- [x] 3.2 Atualizar `docs/PRD.md` e `docs/adrs/ADR-001.md` de 30 min para 6 h e verificar com `grep` que não restam referências ao TTL antigo nesses arquivos.
- [x] 3.3 Documentar em `docs/misc/datasources.md` que entradas antigas com `ttl_minutes: 30` expiram uma última vez antes de serem regravadas com 360 min; verificar que a seção de cache reflete o novo default.

## 4. Verificação integrada

- [x] 4.1 Executar `make lint` e corrigir qualquer problema; verificar que o comando termina com sucesso.
- [x] 4.2 Executar `make complexity` e verificar que o comando termina sem bloqueio.
- [x] 4.3 Executar `make test` (suíte completa, justificada por alterar infraestrutura e contrato de cache compartilhados) e verificar que todos os testes e a cobertura mínima passam.
- [x] 4.4 Validar a change com `npx --yes @fission-ai/openspec validate increase-b3-resilience --type change --strict` e verificar que não há erros de spec.
