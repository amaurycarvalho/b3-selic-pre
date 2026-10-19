## Context

Ver `proposal.md` para motivação e `specs/b3-api-client/spec.md` para o contrato de comportamento. O spike mostrou que a B3 expõe `GetProducts`, `GetDate` e `GetList` sem autenticação; o site da B3 usa `GetList` com `page.totalRecords`/`page.totalPages`, não `totalCount`. O `GetDate` de `SLP` retornou 20 datas úteis. Tanto `GetList` quanto `GetDownloadFile` podem retornar `200 OK` vazio de forma intermitente, e o parser CSV atual deixa `\r` no campo `rate`. O logging já entrega o contrato `CommunicationError` (linha única para comunicação, traceback para o resto). A arquitetura permite `infrastructure -> application` e só permite `presentation -> infrastructure` nos composition roots.

## Goals / Non-Goals

**Goals:**

- Tornar a API JSON a fonte primária para a janela disponível, com metadados de página e validação de completude.
- Tratar respostas `200` vazias/incompletas com retry de aplicação, separado do retry HTTP.
- Usar `GetDate` como fonte de verdade da janela e alinhar GUI/CLI/evolução a ela.
- Manter o CSV apenas como fallback temporário para datas fora da janela, corrigindo o parser.
- Adicionar `requests` com pooling, retries, timeouts e TLS/proxy configuráveis.
- Manter o contrato de logging existente: `CommunicationError` em uma linha; erros de dados com traceback.

**Non-Goals:**

- Remover o CSV definitivamente; isso é um follow-up após a API se mostrar estável em produção.
- Adicionar uma API de terceiros; a B3 `GetList` é a única fonte gratuita e anônima que cobre a curva.
- Adicionar UI para editar CA/proxy; as chaves são editadas no `settings.json`.
- Desligar a verificação TLS; apenas CA customizado é suportado.
- Resolver a consistência de datas antigas que não estão em `GetDate`; elas dependem do fallback ou são reportadas como indisponíveis.

## Decisions

### 1. Transporte HTTP com `requests`

Criar `infrastructure/http_client.py` com `B3HttpClient`:

- `threading.local()` com uma `requests.Session` por thread; a GUI usa 5 threads no histórico e uma `Session` compartilhada não é thread-safe.
- `HTTPAdapter(max_retries=Retry(total=2, connect=2, read=0, status=2, backoff_factor=0.5, status_forcelist=(408, 429, 500, 502, 503, 504), allowed_methods=("GET",), respect_retry_after_header=True, raise_on_status=False))`.
- `timeout=(5, 20)`; `raise_for_status()` antes de ler o conteúdo; `User-Agent` próprio.
- `trust_env=False`; as configurações do `settings.json` são a fonte de verdade.
- `close()` fecha a `Session` da thread atual.

`read=0` evita repetir read timeout e mantém o orçamento próximo de 20–30 s. `raise_on_status=False` deixa o `raise_for_status()` produzir um `HTTPError` final com status legível.

**Alternativa rejeitada:** `requests.get` por chamada. Não oferece pooling nem retry configurável sem recriar a Session a cada requisição.

### 2. Cliente API-first

Criar `infrastructure/b3_api.py` com:

- `PageMeta`: `page_number`, `page_size`, `total_records`, `total_pages`.
- `ApiPage`: `records: list[RateRecord]`, `meta: PageMeta`.
- `B3ApiClient.fetch_page(date, page_number, page_size) -> ApiPage`.
- `B3ApiClient.fetch_all(date, progress_callback) -> list[RateRecord]`.
- `B3ApiClient.available_dates() -> list[str]` via `GetDate`, com cache em memória e lock.
- Payload/URL builders reaproveitados de `b3_client` ou movidos para `b3_api`; `b3_client` permanece como fachada de compatibilidade.

A paginação é 1-based. Usar `page.totalPages` e `page.totalRecords`; `pageSize` acima de 120 retornou metadados nulos no spike, então o cliente usa 100 (ou 120) e valida o limite. `GetProducts` é usado para validar o ID `SLP` em teste/smoke; o ID permanece uma constante (`DEFAULT_RATE_ID = "SLP"`).

JSON deve ser decodificado com `json.loads(response.content.decode("utf-8"))`, **não** `response.json()`: no `requests`, um JSON inválido vira `requests.exceptions.JSONDecodeError` (subclasse de `RequestException`) e seria classificado como comunicação; com `json.loads`, continua `ValueError` e recebe traceback.

### 3. Retry de aplicação para `200` vazio/incompleto

O retry HTTP cobre conexão/429/5xx. Uma página `200` com `results=[]` e `totalRecords=0` é tratada como possível falha transitória:

1. Se a data está em `GetDate` e a página esperada veio vazia, repetir até 2 vezes com backoff curto (0.5 s, 1 s).
2. Se persistir, lançar `CommunicationError` com data, página e quantidade esperada.
3. Se a coleta terminar com `len(records) != totalRecords`, repetir as páginas faltantes; se persistir, `CommunicationError`.
4. Não repetir no nível da API um erro de read timeout/conexão já tratado pelo transporte; isso evita multiplicar o orçamento de 20–30 s.

Se `GetDate` retornar lista vazia após os retries, lançar `CommunicationError` (“janela de datas indisponível”). Se a data não está em `GetDate`, não é uma falha transitória: sinaliza indisponibilidade e tenta o fallback CSV.

### 4. Contrato de erros

- `requests.RequestException` ou resposta incompleta persistente → `CommunicationError`, preservando a causa (`raise ... from exc`).
- JSON inválido ou schema inesperado (`results`/`page`) → `ValueError` (ou erro de dados equivalente), sem `CommunicationError`.
- O logging existente trata `CommunicationError` como uma linha e `ValueError` com traceback. Não é necessário alterar a spec de logging já entregue.
- A mensagem do `CommunicationError` deve ser curta e útil (`B3 indisponível após 3 tentativas: ...`, `Resposta incompleta da B3: esperados 279, obtidos 0`).

### 5. Fallback CSV

`GetDownloadFile` permanece em `b3_client`/`b3_api` apenas para datas fora de `GetDate`. O fallback:

- não é usado quando a data está na janela e a API falha, para não mascarar instabilidade;
- usa o mesmo `B3HttpClient` (requests) e `raise_for_status()`;
- corrige o parser para `splitlines()` e `strip()` em cada campo, eliminando o `\r` do `rate`;
- mantém o `source_callback` indicando “Arquivo oficial B3 (fallback)”;
- tem remoção planejada em um follow-up quando a janela da API for suficiente.

### 6. Janela de histórico e evolução

`GetDate` é a fonte de verdade da janela. A validação estática de 30 dias da GUI continua para os modos raw/consolidado, mas uma data dentro dos 30 dias e fora de `GetDate` é tratada como indisponível (fallback CSV ou mensagem). O modo evolução:

- busca as 5 datas via `GetList` quando disponíveis;
- usa o fallback CSV para datas fora da janela;
- se uma data não tiver dados em nenhuma fonte, reporta a data indisponível e não substitui silenciosamente por outra;
- mantém o contrato de 5 curvas quando todas as datas estão disponíveis.

A CLI usa a mesma orquestração; datas antigas fora da janela dependem do fallback e podem ser reportadas como indisponíveis.

### 7. Composição, settings e camadas

- `presentation/settings.py` adiciona `http_ca_bundle`, `http_proxy`, `https_proxy`, `no_proxy` a `DEFAULT_SETTINGS` (`""`) e getters validados que retornam `str`.
- `infrastructure/http_client.py` define `HttpConfig` (CA, proxies, no_proxy, timeout) e `B3HttpClient`. `HttpConfig` valida caminho de CA e URLs de proxy; valores inválidos viram default e geram warning no log.
- Os composition roots (`presentation/cli.py`, `presentation/gui/launch.py`) leem `Settings`, montam `HttpConfig` e criam/injetam o `B3HttpClient`/`B3ApiClient` no `CachedB3Client`. `presentation/settings.py` não importa infrastructure, preservando as camadas.
- `b3_client` mantém funções de compatibilidade e uma instância default para chamadas diretas/testes; o app usa o cliente injetado.
- TLS sempre ativo; não há `http_verify_tls`. CA customizado via `http_ca_bundle`; proxies via chaves; `no_proxy` via `requests.utils.should_bypass_proxies`.

**Alternativa rejeitada:** variáveis de ambiente do `requests`. O usuário escolheu `settings.json`; `trust_env=False` evita duas fontes de verdade e comportamento dependente do ambiente.

### 8. Dependência, build e documentação

- Adicionar `requests>=2.32,<3` a `[project].dependencies`; não depender da instalação transitiva de `semgrep`/`xenon` no venv de desenvolvimento.
- Validar PyInstaller: requests/urllib3/certifi/charset_normalizer; incluir dados de `certifi` e testar o binário em Linux (e, se possível, Windows/macOS no CI).
- Atualizar ADR-001 (nova decisão ou ADR-003), CHANGELOG e a parte de dependências do RFC-001, que hoje diz “usar `urllib`, não `requests`”. Coordenar com a change `rfc001-tesouro-direto-redesign`, que também planeja `urllib`.

## Risks / Trade-offs

- **`200` vazio é intermitente e pode ser rate limit/cache** → retry de aplicação com backoff curto, validação de `totalRecords` e mensagem clara; não aumentar indefinidamente o orçamento.
- **Janela histórica menor que o esperado** → `GetDate` como fonte de verdade; fallback CSV e mensagem de indisponibilidade; documentar que a API cobre ~20 datas úteis.
- **Evolução perto do limite de 30 dias** → fallback CSV ou reportar a data indisponível; não substituir silenciosamente.
- **`requests` aumenta dependências/binário** → testar build e tamanho; `certifi`/`charset_normalizer` exigem hooks no PyInstaller.
- **TLS/proxy mudam o comportamento do cliente** → `trust_env=False`, CA/proxy explícitos, verificação sempre ativa; documentar `settings.json`.
- **CSV ainda é flaky e tem parser frágil** → corrigir `splitlines()`/`strip()`; não usá-lo para mascarar falha da API; remoção futura.
- **`RequestException` é amplo** → URLs são constantes; validar schema para não classificar erro de programação como comunicação.
- **Duas stacks durante a transição** → `b3_client` é fachada; o app usa o cliente API-first; o CSV fica isolado no fallback.
- **RFC-001 e CHANGELOG contradizem a nova decisão** → atualizar a documentação na mesma change; caso contrário, a decisão fica ambígua.

## Migration Plan

1. Adicionar requests/settings e o `B3HttpClient`; manter o caminho CSV atual funcionando.
2. Introduzir o `B3ApiClient` e a orquestração API-first no `CachedB3Client`, com fallback CSV para datas fora de `GetDate`.
3. Atualizar GUI/CLI/evolução para a janela de `GetDate` e os novos erros.
4. Corrigir o parser CSV e cobrir `\r\n`.
5. Atualizar ADR/CHANGELOG/RFC-001 e validar o build PyInstaller.
6. Rodar suíte completa, smoke real contra a B3 e verificar datas fora da janela/fallback.

Rollback: manter `b3_client`/CSV e o caminho antigo disponíveis até a API estar validada; se necessário, o `CachedB3Client` pode voltar a usar o CSV como fonte primária e a dependência `requests` pode ser removida em uma reversão.
