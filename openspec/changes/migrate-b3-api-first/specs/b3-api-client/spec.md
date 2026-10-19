## Purpose

Fornecer um cliente HTTP API-first para os dados de taxas referenciais da B3, usando chamadas JSON diretas, metadados de paginação, janela de disponibilidade e retries explícitos, com fallback temporário para o download CSV em datas fora da janela da API.

## ADDED Requirements

### Requirement: B3 API endpoints

O sistema SHALL usar os endpoints JSON da B3 `GetProducts`, `GetDate` e `GetList` para obter metadados, datas disponíveis e taxas referenciais do produto `SLP` ("Selic x pré"). As chamadas SHALL usar HTTPS e NÃO SHALL exigir autenticação.

#### Scenario: Products endpoint identifies SLP

- **WHEN** o cliente consulta `GetProducts`
- **THEN** a resposta SHALL conter o produto `SLP` com a descrição "Selic x pré"

#### Scenario: Available dates endpoint returns the API window

- **WHEN** o cliente consulta `GetDate` para `SLP`
- **THEN** a resposta SHALL conter a lista de datas disponíveis, em ordem decrescente, com as datas mais recentes primeiro

#### Scenario: List endpoint returns rates for a date

- **WHEN** o cliente consulta `GetList` para uma data disponível de `SLP`
- **THEN** a resposta SHALL conter uma lista de registros com `day252`, `day360` e `rate`

### Requirement: Page metadata and completeness

O cliente SHALL interpretar a paginação pelo objeto `page` da resposta, usando `pageNumber`, `pageSize`, `totalRecords` e `totalPages`. A paginação SHALL ser 1-based e o cliente NÃO SHALL depender de um campo `totalCount` no topo da resposta.

#### Scenario: Page metadata is parsed

- **WHEN** uma página retorna `page.totalRecords` e `page.totalPages`
- **THEN** o cliente SHALL expor esses valores para validação e progresso

#### Scenario: All pages are fetched

- **WHEN** a primeira página informa `totalPages` maior que 1
- **THEN** o cliente SHALL buscar todas as páginas de `1` até `totalPages`

#### Scenario: Completeness is validated

- **WHEN** a coleta termina
- **THEN** o cliente SHALL comparar a quantidade de registros coletados com `totalRecords`
- **AND** SHALL falhar de forma explícita se a quantidade não coincidir

#### Scenario: Excessive page count is rejected

- **WHEN** `totalPages` excede o limite máximo configurado
- **THEN** o cliente SHALL rejeitar a consulta sem continuar a paginação

### Requirement: Empty and incomplete responses

O cliente SHALL tratar respostas `200 OK` com `results` vazio ou corpo vazio como possível falha transitória, porque o retry HTTP comum não cobre esse caso.

#### Scenario: Empty page is retried

- **WHEN** uma página esperada retorna `200` com `results` vazio e a data está disponível em `GetDate`
- **THEN** o cliente SHALL repetir a consulta com backoff curto, até um limite configurado

#### Scenario: Persistent empty response is a communication failure

- **WHEN** a página continua vazia após o limite de tentativas
- **THEN** o cliente SHALL falhar com `CommunicationError`, contendo a data, a página e a quantidade esperada

#### Scenario: Invalid JSON is a data error

- **WHEN** o corpo da resposta não é um JSON válido ou não contém `results`/`page` no formato esperado
- **THEN** o cliente SHALL falhar com erro de dados (`ValueError` ou equivalente), que recebe traceback no log

### Requirement: Available-date window

O cliente SHALL usar `GetDate` como fonte de verdade para a janela de datas disponíveis da API e SHALL manter um cache em memória de curta duração para essa lista.

#### Scenario: Date inside the window

- **WHEN** a data solicitada está na lista de `GetDate`
- **THEN** o cliente SHALL buscar os dados via `GetList`

#### Scenario: Date outside the window

- **WHEN** a data solicitada não está na lista de `GetDate`
- **THEN** o cliente SHALL sinalizar a indisponibilidade para a API
- **AND** poderá usar o fallback CSV temporário, conforme o requisito de fallback

#### Scenario: Available-date lookup is cached

- **WHEN** `GetDate` é consultado novamente dentro do TTL do cache
- **THEN** o cliente SHALL reutilizar a lista em memória sem nova chamada HTTP

### Requirement: CSV fallback

O sistema SHALL manter o endpoint `GetDownloadFile` apenas como fallback temporário para datas fora da janela de `GetDate`. O fallback NÃO SHALL ser usado para mascarar falhas transitórias de uma data que está na janela da API.

#### Scenario: Out-of-window date uses CSV fallback

- **WHEN** a data solicitada não está em `GetDate` e o CSV retorna registros
- **THEN** o sistema SHALL usar os registros do CSV e indicar a fonte de fallback

#### Scenario: CSV fallback is empty

- **WHEN** a data não está em `GetDate` e o CSV também retorna vazio
- **THEN** o sistema SHALL reportar que não há dados disponíveis para a data

#### Scenario: CSV line endings are parsed correctly

- **WHEN** o CSV usa quebras de linha `\r\n`
- **THEN** o campo `rate` SHALL ser retornado sem `\r`, usando `splitlines()` ou equivalente

#### Scenario: API date is not silently replaced by CSV

- **WHEN** a data está em `GetDate` e a API falha após os retries
- **THEN** o sistema NÃO SHALL trocar silenciosamente para o CSV; a falha SHALL ser reportada como comunicação

### Requirement: HTTP transport and retry budget

O transporte HTTP SHALL usar uma sessão por thread, pooling de conexões, retries apenas para erros de conexão, `429` e `5xx`, e SHALL aplicar `raise_for_status()` antes de ler o corpo. O read timeout NÃO SHALL ser repetido.

#### Scenario: Transient network failure is retried

- **WHEN** uma requisição sofre erro de conexão ou recebe `429`/`5xx`
- **THEN** o transporte SHALL repetir a requisição com backoff, até o limite configurado

#### Scenario: Read timeout is not retried

- **WHEN** uma requisição excede o read timeout
- **THEN** o transporte SHALL falhar sem repetir, respeitando o orçamento de tempo

#### Scenario: Timeout budget is bounded

- **WHEN** a rede está indisponível
- **THEN** o tempo total até o erro SHALL ficar no orçamento de aproximadamente 20–30 segundos, incluindo retries e backoff

#### Scenario: HTTP error status is a communication failure

- **WHEN** a resposta final tem status `4xx` ou `5xx` após os retries
- **THEN** o erro SHALL ser exposto como `CommunicationError`

### Requirement: Error contract

O cliente SHALL distinguir falhas de comunicação de erros de dados.

#### Scenario: Request exception is communication

- **WHEN** o transporte lança `requests.RequestException` ou o cliente detecta resposta incompleta após retries
- **THEN** SHALL ser lançado `CommunicationError`, direto ou com a exceção original como causa

#### Scenario: JSON or schema error is data

- **WHEN** o JSON é inválido ou o schema de `results`/`page` é inesperado
- **THEN** SHALL ser lançado um erro de dados, não `CommunicationError`

#### Scenario: Communication error is logged in one line

- **WHEN** um `CommunicationError` é registrado
- **THEN** o log SHALL conter uma única linha com o tipo e a mensagem da causa, sem call stack

### Requirement: TLS and proxy settings

O cliente SHALL aplicar as configurações de CA e proxy definidas no arquivo de settings, mantendo a verificação TLS sempre ativa.

#### Scenario: Custom CA bundle is applied

- **WHEN** `http_ca_bundle` contém um caminho válido
- **THEN** o transporte SHALL usar esse arquivo como bundle de CA

#### Scenario: Proxies are applied

- **WHEN** `http_proxy` ou `https_proxy` estão definidos
- **THEN** o transporte SHALL usar os proxies correspondentes

#### Scenario: no_proxy bypasses proxies

- **WHEN** a URL corresponde a uma entrada de `no_proxy`
- **THEN** o transporte SHALL acessar a URL sem proxy

#### Scenario: TLS verification cannot be disabled

- **WHEN** as configurações são carregadas
- **THEN** a verificação TLS SHALL permanecer ativa; não haverá chave para desativá-la nesta mudança
