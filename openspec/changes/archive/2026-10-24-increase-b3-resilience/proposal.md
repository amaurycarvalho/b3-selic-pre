## Why

O acesso atual à B3 já repete respostas vazias, mas não repete timeouts nem falhas transientes de rede. Um timeout no `GetList` interrompe a consulta imediatamente e um timeout no `GetDownloadFile` nem sequer aciona o fallback para `GetList`, porque o fallback só captura `CommunicationError`. Além disso, o timeout de 30 s está duplicado em vários módulos e o TTL de 30 min para a data corrente força refetches frequentes.

## What Changes

- Centralizar o timeout padrão de acesso à B3 em **60 s**, usado por `GetList`, `GetDownloadFile` e pela seleção de fonte.
- Generalizar o retry para repetir também falhas transientes (`TimeoutError`, `URLError`, `ConnectionError`, `HTTPException`, `SSLError`, `socket.gaierror`), além dos resultados vazios já cobertos.
- Manter **6 tentativas** para resultados vazios e usar **3 tentativas** para falhas transientes, com o mesmo backoff exponencial com jitter, limitando o pior caso por página a aproximadamente 3 minutos.
- Preservar a regra de que erros de dados (JSON/CSV inválido ou esquema inesperado) não são repetidos.
- Garantir que uma falha transiente do `GetDownloadFile` em data passada permita o fallback para `GetList`, como já ocorre com resposta vazia.
- Alterar o TTL padrão da data corrente de **30 min** para **6 h (360 min)**.
- Atualizar testes, specs e documentação afetada.

**Non-goals**: alterar a seleção de fonte por data, o modelo de paginação, o layout do cache, o formato do payload, os comandos da CLI, a GUI ou o servidor MCP.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `b3-rate-source`: timeout padrão de 60 s, retry de falhas transientes com orçamento próprio, manutenção do retry de respostas vazias e fallback de data passada também em falha transiente.
- `disk-cache`: TTL padrão da data corrente passa de 30 min para 6 h.

## Impact

- `src/b3_selic_pre/domain/constants.py`: novo default de timeout.
- `src/b3_selic_pre/infrastructure/b3_retry.py`: retry de vazio e de exceções transientes.
- `src/b3_selic_pre/infrastructure/b3_list.py`, `b3_download.py`, `b3_client.py`: uso do timeout centralizado e do novo retry.
- `src/b3_selic_pre/infrastructure/cached_client.py`: TTL padrão de 360 min.
- Testes em `tests/test_b3_client.py`, `tests/test_disk_cache.py` e testes de comunicação afetados.
- Documentação em `docs/misc/datasources.md`, `docs/PRD.md` e `docs/adrs/ADR-001.md`.
- Entradas de cache já gravadas com `ttl_minutes: 30` continuam expirando uma última vez com o TTL antigo; a próxima gravação passa a usar 360 min.
