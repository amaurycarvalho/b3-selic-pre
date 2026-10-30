# Fontes de Dados Externas

Documentação das URLs, APIs e demais fontes externas consultadas pela aplicação
`b3-selic-pre` em tempo de execução.

## Escopo

Esta avaliação cobre todo acesso de rede realizado pela aplicação. O código-fonte
não usa SDKs, bibliotecas HTTP de terceiros nem serviços de telemetria: as fontes
externas são dois endpoints do portal de derivativos da B3 e a API CKAN do Tesouro
Transparente, acessados via `urllib.request` em
`src/b3_selic_pre/infrastructure/`.

| Fonte | Base URL | Uso | Autenticação |
| --- | --- | --- | --- |
| B3 `GetList` | `https://sistemaswebb3-derivativos.b3.com.br/` | Data corrente e fallback de datas passadas | Nenhuma |
| B3 `GetDownloadFile` | `https://sistemaswebb3-derivativos.b3.com.br/` | Fonte primária para datas passadas (CSV) | Nenhuma |
| Tesouro CKAN | `https://www.tesourotransparente.gov.br/ckan` | Descoberta dos datasets e das URLs dos CSVs | Nenhuma |
| Tesouro CSV | URL retornada pelo CKAN | Vendas, resgates e estoque do Tesouro Direto | Nenhuma |

Páginas do GitHub (releases, repositório) e a página pública de taxas da B3
citadas no `README.md` são apenas referências para o usuário; não são acessadas
pela aplicação.

## Base URL

Definida em `src/b3_selic_pre/domain/constants.py`:

```text
B3_BASE_URL = "https://sistemaswebb3-derivativos.b3.com.br/"
```

Ambos os endpoints ficam sob o prefixo `referenceRatesProxy/Search/` e usam
`HTTPS` com validação de certificado padrão do Python. Não há chave de API,
token, cookie de sessão nem credencial de qualquer tipo.

## Endpoint `GetList`

Usado para a **data corrente** e como **fallback** quando o `GetDownloadFile`
não retorna dados para uma data passada.

### URL

```text
{B3_BASE_URL}referenceRatesProxy/Search/GetList/{payload_base64}
```

O `{payload_base64}` é o JSON compacto do payload codificado em Base64 (UTF-8),
sem URL-encoding adicional. Construído em
`src/b3_selic_pre/infrastructure/b3_list.py`.

### Payload

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `language` | string | `pt-br` | Idioma dos textos retornados |
| `id` | string | `SLP` | Identificador da taxa referencial SELIC Pré |
| `pageNumber` | int | `1` | Página solicitada (1-based) |
| `pageSize` | int | `20` | Registros por página |
| `date` | string | — | Data de referência em `YYYY-MM-DD` |

Exemplo de payload:

```json
{"language":"pt-br","id":"SLP","pageNumber":1,"pageSize":20,"date":"2026-06-10"}
```

### Resposta

JSON com a lista `results` e metadados de paginação no objeto `page`:

```json
{
  "results": [
    {"day252": 1, "day360": 1, "rate": "14,90"}
  ],
  "page": {
    "pageNumber": 1,
    "pageSize": 20,
    "totalRecords": 279,
    "totalPages": 14
  }
}
```

Regras de leitura implementadas:

- `results` é obrigatório e deve ser uma lista; caso contrário, erro de dados.
- Cada item deve conter `day252` (int), `day360` (int) e `rate` (string).
- Os metadados vêm de `page.totalRecords` e `page.totalPages`, com fallback de
  contagem para o campo legado `totalCount`.
- Se `totalPages` não vier, ele é calculado a partir de `totalRecords / pageSize`.
- O sistema busca todas as páginas de `1` até `totalPages`.
- `totalPages` acima de `DEFAULT_MAX_PAGES` (100) é rejeitado.
- A soma dos registros coletados é comparada com `totalRecords`; divergência gera
  falha de comunicação explícita (não retorna resultado parcial como sucesso).
- Página esperada vazia é repetida conforme a política de retry abaixo.

## Endpoint `GetDownloadFile`

Fonte **primária** para datas anteriores à data corrente. Retorna um arquivo CSV
codificado em Base64.

### URL

```text
{B3_BASE_URL}referenceRatesProxy/Search/GetDownloadFile/{payload_base64}
```

Construído em `src/b3_selic_pre/infrastructure/b3_download.py`.

### Payload

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `language` | string | `pt-br` | Idioma dos textos retornados |
| `date` | string | — | Data de referência em `YYYY-MM-DD` |
| `id` | string | `SLP` | Identificador da taxa referencial SELIC Pré |

Exemplo de payload:

```json
{"language":"pt-br","date":"2026-06-09","id":"SLP"}
```

### Resposta

Corpo de texto contendo um CSV em Base64. A aplicação:

1. decodifica o Base64 validando o conteúdo (entrada vazia → resultado vazio);
2. decodifica o CSV em `latin-1`;
3. divide as linhas com suporte a `\n` e `\r\n`, removendo espaços de cada campo;
4. ignora a primeira linha (cabeçalho) e linhas em branco;
5. interpreta as colunas separadas por `;` como
   `[descrição, day252, day360, rate]`;
6. rejeita linha malformada com erro de dados em vez de descartá-la em silêncio.

## Seleção de fonte por data

Implementada em `fetch_rates_for_date`
(`src/b3_selic_pre/infrastructure/b3_client.py`):

| Data solicitada | Fonte primária | Fallback |
| --- | --- | --- |
| Igual à data corrente (UTC) | `GetList` | — |
| Anterior à data corrente | `GetDownloadFile` | `GetList`, somente após esgotar os retries do CSV |

O fallback para `GetList` só ocorre quando o `GetDownloadFile` retorna vazio após
todas as tentativas. Erros de dados (CSV/JSON inválido, esquema inesperado) **não**
disparam troca de fonte: são propagados como erro.

A busca de evolução consulta 5 datas (hoje, 7, 14, 21 e 28 dias atrás) em paralelo
(5 workers). Falhas de comunicação por data são isoladas e a data fica sem registros,
sem interromper as demais.

## Retry e timeouts

- Timeout padrão por requisição: **60 s**.
- Resposta HTTP `200` com corpo vazio é tratada como falha transitória.
- Orçamentos independentes:
  - até **6 tentativas** quando o resultado permanece vazio;
  - até **3 tentativas** quando ocorre falha transiente de rede/transporte.
- Falhas transientes repetidas: `urllib.error.URLError`,
  `http.client.HTTPException`, `TimeoutError`, `ConnectionError`,
  `ssl.SSLError` e `socket.gaierror`.
- Backoff exponencial com jitter: tetos de `0.5`, `1.0`, `2.0`, `4.0` e `4.0` s,
  multiplicados por um fator aleatório em cada espera.
- Esgotados os orçamentos, é lançado `CommunicationError` identificando a data e a
  fonte.
- Para datas passadas, uma falha transiente do `GetDownloadFile` após os retries
  também aciona o fallback para `GetList`.
- JSON inválido, CSV inválido ou esquema inesperado **não** são repetidos.

## Classificação de erros

As exceções de rede/HTTP abaixo são tratadas como falha de comunicação e podem
gerar mensagem amigável na CLI e log em linha única:

- `urllib.error.URLError`
- `http.client.HTTPException`
- `TimeoutError`
- `ConnectionError`
- `ssl.SSLError`
- `socket.gaierror`

Erros de dados (`ValueError`/`TypeError`) representam resposta fora do contrato e
seguem o fluxo de erro da aplicação, sem retry.

## Tesouro Transparente (CKAN)

### Descoberta

```text
GET https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=<dataset>
```

A resposta JSON deve ter `success: true` e um objeto `result`. O sistema não
interpreta HTML nem consome PDFs de metadados. Resposta inválida, `success`
falso, recurso ausente ou recurso ambíguo gera `TesouroDataError`.

### Datasets e recursos

| Grupo | Dataset | Recurso lógico | Nome no CKAN | CSV de cache | Colunas |
| --- | --- | --- | --- | --- | --- |
| vendas | `vendas-do-tesouro-direto` | `vendas` | Vendas do Tesouro Direto | `vendastesourodireto.csv` | 6, com `PU` |
| resgates | `resgates-do-tesouro-direto` | `recompra` | Recompras do Tesouro Direto | `recompras.csv` | 5, sem `PU` |
| resgates | `resgates-do-tesouro-direto` | `cupom` | Pagamento de Cupom de Juros do Tesouro Direto | `cupom.csv` | 6, com `PU` |
| resgates | `resgates-do-tesouro-direto` | `vencimento` | Vencimentos do Tesouro Direto | `vencimentos.csv` | 6, com `PU` |
| estoque | `estoque-do-tesouro-direto` | `estoque` | Estoque do Tesouro Direto | `estoque.csv` | 6, com `Mes Estoque` e `Valor Estoque` |

O dataset de vendas exige exatamente um recurso CSV. O dataset de estoque exige
um recurso CSV. O dataset de resgates é selecionado por nome/filename; quando há
dois recursos de cupom, vence o de maior `last_modified` (o mais novo é
superconjunto do antigo).

| Item | Valor |
| --- | --- |
| Separador | `;` |
| Datas | `DD/MM/YYYY` |
| Mês de estoque | `MM/YYYY` |
| Decimal | vírgula |
| Cabeçalho de vendas | `Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;PU;Quantidade;Valor` |
| Cabeçalho de recompras | `Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade;Valor` |
| Cabeçalho de cupom/vencimentos | `Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor` |
| Cabeçalho de estoque | `Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;Valor Estoque` |

### Download e cabeçalhos

O download usa `urllib.request`, em chunks de 64 KiB, timeout de 60 s e
cabeçalhos condicionais `If-None-Match` (`ETag`) e `If-Modified-Since`
(`Last-Modified`). O servidor pode responder `304 Not Modified`; nesse caso o
CSV não é regravado e apenas `checked_at` do metadata é atualizado.

Headers observados no spike:

```text
Content-Type: text/csv
Transfer-Encoding: chunked
Content-Range: bytes 0-7488602/7488603
ETag: "1792146545.96-7488603"
Last-Modified: Fri, 16 Oct 2026 10:29:05 GMT
```

O `Content-Range` é usado para validar o tamanho do corpo. `Content-Type` que não
começa por `text/csv`, corpo vazio ou corpo parcial é falha transitória; após os
retries, vira `CommunicationError`.

### Retry e classificação

- até 3 tentativas para rede, timeout, HTTP 429/5xx, corpo vazio/parcial e
  resposta não-CSV, com backoff exponencial e jitter;
- HTTP 4xx não transitório gera `CommunicationError` sem retry;
- CSV malformado, colunas ausentes, datas/valores inválidos e CSV vazio geram
  `TesouroDataError` e não são cacheados;
- a versão anterior do cache é preservada quando download ou parsing falham.

### Cache

```text
$XDG_CACHE_HOME/b3-selic-pre/tesouro/
├── vendastesourodireto.csv
├── metadata.json
├── recompras.csv
├── recompras.metadata.json
├── cupom.csv
├── cupom.metadata.json
├── vencimentos.csv
├── vencimentos.metadata.json
├── estoque.csv
└── estoque.metadata.json
```

Cada recurso tem CSV e metadata independentes, sem poda. O TTL é aplicado por
recurso: recompras usam 1 hora quando o dado mais recente alcança o dia corrente
ou o último dia útil e 6 horas quando é histórico; cupom, vencimentos e estoque
usam 24 horas. Cache ausente, vazio, corrompido, incompleto ou com
`schema_version` antigo é tratado como miss. A escrita do CSV e do metadata é
atômica. Falha em um recurso preserva a versão anterior e não impede os demais.

## Cache local

As respostas da B3 são cacheadas em disco (ver `disk-cache`), não sendo uma fonte
externa adicional:

- data corrente respeita TTL configurável (padrão: 6 h / 360 min);
- datas passadas não expiram;
- apenas resultados não vazios e completos são gravados;
- entradas vazias, incompletas ou legadas são tratadas como miss e re-buscadas;
- entradas antigas com `ttl_minutes: 30` mantêm o TTL gravado e expiram uma
  última vez antes de serem regravadas com 360 min.

Os rótulos exibidos na GUI são `API B3` (`GetList`), `Arquivo oficial B3`
(`GetDownloadFile`) e `Histórico B3` (busca de evolução).

## Avaliação e riscos

- **Contrato não público**: os dois endpoints são internos do portal de
  derivativos da B3 e não possuem documentação pública, versionamento nem SLA.
  Mudanças de URL, esquema ou formato podem quebrar a aplicação.
- **Sem autenticação**: não há credenciais a proteger, mas também não há garantia
  de quota; a aplicação não conhece limites de rate limiting da B3.
- **Privacidade**: apenas data, idioma e identificador da taxa são enviados; não há
  dados pessoais, telemetria ou identificação do usuário.
- **Segurança de transporte**: todo tráfego usa HTTPS; a URL é montada a partir de
  constantes fixas, sem entrada do usuário no host ou esquema.
- **Dependência de rede**: indisponibilidade ou resposta vazia persistente resulta
  em falha de comunicação explícita, sem apresentar curva vazia como sucesso.
- **User-Agent**: as requisições usam o `User-Agent` padrão do `urllib` do Python.

## Manutenção

Arquivos relevantes:

| Arquivo | Responsabilidade |
| --- | --- |
| `domain/constants.py` | Base URL, `id`, idioma e defaults de paginação |
| `infrastructure/b3_list.py` | `GetList`, payload, paginação e completude |
| `infrastructure/b3_download.py` | `GetDownloadFile` e parsing do CSV |
| `infrastructure/b3_retry.py` | Retry de respostas vazias, falhas transientes e backoff |
| `infrastructure/b3_client.py` | Seleção de fonte, timeouts e busca histórica |
| `infrastructure/cached_client.py` | Cache em disco e rótulos de origem |
| `infrastructure/disk_cache.py` | Persistência e invalidação de entradas |
| `infrastructure/tesouro_client.py` | Download condicional, retry e validação de corpo |
| `infrastructure/tesouro_discovery.py` | Descoberta CKAN e seleção de recursos |
| `infrastructure/tesouro_cache.py` | CSV e metadata por recurso, TTL e escrita atômica |
| `infrastructure/tesouro_cached_client.py` | Cliente de vendas, resgates e estoque com `force` |
