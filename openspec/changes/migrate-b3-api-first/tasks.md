## 1. Dependência, settings e transporte

- [ ] 1.1 Adicionar `requests>=2.32,<3` a `[project].dependencies` e verificar `make install`/`pip install -e .` com `python -c "import requests"`.
- [ ] 1.2 Adicionar `http_ca_bundle`, `http_proxy`, `https_proxy` e `no_proxy` a `DEFAULT_SETTINGS` e getters validados em `Settings`; verificar com `pytest tests/test_settings.py` cobrindo defaults, valores válidos e tipos inválidos.
- [ ] 1.3 Implementar `infrastructure/http_client.py` com `HttpConfig`, `B3HttpClient`, `Session` por thread, `HTTPAdapter`/`Retry`, `timeout=(5, 20)`, `User-Agent`, `raise_for_status`, `trust_env=False` e `close()`; verificar com `pytest tests/test_http_client.py` para sessão por thread, retry, timeout, headers e close.
- [ ] 1.4 Aplicar CA/proxy/no_proxy do `HttpConfig` na sessão e validar caminho/URL com fallback para default; verificar com testes de CA válido/inválido, proxies, `no_proxy` e ausência de override por variáveis de ambiente (`pytest tests/test_http_client.py`).

## 2. Cliente API B3

- [ ] 2.1 Implementar `infrastructure/b3_api.py` com `PageMeta`, `ApiPage`, `GetProducts`/`GetDate`/`GetList`, payloads e parsing; verificar com `pytest tests/test_b3_api.py` para identificação de `SLP`, lista de datas e página de registros.
- [ ] 2.2 Implementar `fetch_all` usando `page.totalPages` e `page.totalRecords`, paginação 1-based e validação de completude; verificar com testes de múltiplas páginas, `totalPages` excedido e `totalRecords` incompatível.
- [ ] 2.3 Implementar retry de aplicação para páginas `200` vazias/incompletas, com backoff curto e limite de tentativas; verificar com testes de página vazia transitória, vazia persistente e `CommunicationError` com data/página/quantidade esperada.
- [ ] 2.4 Implementar o contrato de erros (`RequestException`/incompleto → `CommunicationError`; JSON/schema → `ValueError`) e atualizar os testes de logging para exceções de `requests`; verificar com `pytest tests/test_communication_errors.py tests/test_logging_utils.py`.
- [ ] 2.5 Implementar `available_dates()` com `GetDate`, cache em memória, TTL e lock; verificar com testes de janela, cache hit, expiração e `GetDate` vazio após retries.
- [ ] 2.6 Corrigir o parser do fallback CSV para `splitlines()`/`strip()` e manter o rótulo de fonte de fallback; verificar com testes de CSV `\r\n`, `rate` sem `\r`, CSV vazio e data fora da janela.

## 3. Orquestração e cache

- [ ] 3.1 Atualizar `CachedB3Client` para API-first com `GetDate`, fallback CSV apenas para datas fora da janela e cache por data/TTL preservado; verificar com `pytest tests/test_disk_cache.py` e testes novos de fallback/indisponibilidade.
- [ ] 3.2 Atualizar a fachada `b3_client` para usar o novo cliente e remover `urllib` do caminho principal; verificar com `pytest tests/test_b3_client.py tests/test_b3_selic_pre.py`.
- [ ] 3.3 Atualizar a orquestração de `fetch_historical_rates` para 5 datas via API, fallback fora da janela, paralelismo máximo de 5 e callback de progresso; verificar com testes de 5 datas, data indisponível, fallback e progresso.

## 4. Apresentação

- [ ] 4.1 Atualizar `presentation/gui/fetch.py` para buscar todas as datas via API/fallback, usar `GetDate` para disponibilidade e mostrar progresso/erros corretamente; verificar com testes de GUI existentes e um smoke manual de uma data disponível e uma fora da janela.
- [ ] 4.2 Atualizar `presentation/cli.py` para o mesmo caminho API-first e para mensagens claras de data indisponível/comunicação; verificar com `pytest tests/test_cli.py` cobrindo sucesso, comunicação e indisponibilidade.
- [ ] 4.3 Atualizar `launch_gui`/CLI para ler as chaves HTTP do `Settings` e injetar `HttpConfig`/`B3HttpClient` no `CachedB3Client`; verificar por teste headless dos composition roots e smoke manual de startup.

## 5. Documentação e validação

- [ ] 5.1 Atualizar ADR-001 (ou ADR-003), CHANGELOG e RFC-001 para registrar a substituição de `urllib` por `requests` e a fonte API-first; verificar que a documentação não mantém a decisão antiga sem a nota de supersessão.
- [ ] 5.2 Validar o build PyInstaller com `requests`/`certifi`/`charset_normalizer` e os hooks/dados necessários; verificar que o binário inicia e grava o log de startup.
- [ ] 5.3 Rodar `make lint`, `make complexity` e `make test` (suíte completa) e corrigir falhas; confirmar cobertura >= 85%.
- [ ] 5.4 Executar smoke real contra a B3: `GetDate`, `GetList`, fallback CSV para data fora da janela, fetch da GUI e da CLI; verificar também uma data indisponível e uma falha de comunicação simulada.
