# Servidor MCP

O `b3-selic-pre` expõe a curva SELIC Pré a agentes externos por um servidor
[MCP](https://modelcontextprotocol.io) via `stdio`.

O servidor é **somente leitura** durante o atendimento: ele lê o cache local e
o settings da aplicação, e não consulta a B3/CVM, não baixa dados, não extrai
dados e não grava estado. A preparação opcional na inicialização é a única etapa
que pode carregar dados da B3; ela não é uma tool e não pode ser chamada pelo
protocolo.

## Requisitos

- Python 3.10+.
- Cache local já preparado, salvo quando `--atualizar` ou `--data` for usado.
- Cliente MCP que suporte a revisão `2026-07-28`.

O servidor usa apenas a biblioteca padrão do Python. As dependências gráficas
(matplotlib, Tk, Pillow) continuam necessárias apenas para a GUI.

## Início rápido

```bash
# Atende usando apenas o cache existente
b3-selic-pre mcp

# Carrega a data de hoje antes de atender
b3-selic-pre mcp --atualizar

# Carrega uma data específica antes de atender
b3-selic-pre mcp --data 2026-06-10

# Os dois parâmetros juntos fazem uma única carga, usando a data informada
b3-selic-pre mcp --atualizar --data 2026-06-10
```

O processo encerra quando o cliente fecha `stdin` (EOF). O código de saída é
`0` no encerramento normal. Falhas na preparação encerram com código diferente
de zero e o servidor não inicia.

## Transporte e ciclo de vida

- O cliente lança o processo e escreve mensagens JSON-RPC delimitadas por
  newline em `stdin`.
- O servidor responde em `stdout`, uma mensagem JSON-RPC por linha.
- `stdout` é exclusivo do protocolo. Logs, progresso e diagnósticos vão para
  `stderr`.
- Em `EOF`, o servidor encerra prontamente.
- Requisições podem ser canceladas com `notifications/cancelled`, informando o
  `requestId`. O servidor não envia resposta para uma requisição cancelada.

```text
cliente                         b3-selic-pre mcp
   |                                   |
   |-- JSON-RPC request (linha) ------>|
   |<-- JSON-RPC response (linha) -----|
   |                                   |
   |-- notifications/cancelled ------->|
   |                                   |
   |-- fecha stdin (EOF) ------------->|  sai com 0
```

## Protocolo 2026-07-28

A revisão `2026-07-28` é stateless e não usa o handshake `initialize`.

Toda requisição deve declarar, em `params._meta`:

```json
{
  "_meta": {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {}
  }
}
```

O servidor também aceita `io.modelcontextprotocol/clientInfo`, mas ele não é
obrigatório.

### `server/discover`

RPC obrigatória. Devolve as versões suportadas, as capacidades e a identidade
do servidor.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```

Resposta (resumida):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "complete",
    "supportedVersions": ["2026-07-28"],
    "capabilities": { "tools": {} },
    "_meta": {
      "io.modelcontextprotocol/serverInfo": {
        "name": "b3-selic-pre",
        "version": "1.0.0"
      }
    },
    "instructions": "Servidor somente leitura..."
  }
}
```

### Versionamento e erros

- Versão não suportada: `UnsupportedProtocolVersionError` (`-32022`), com
  `data.supported` e `data.requested`.
- Requisição sem `_meta` obrigatório: `-32602` (Invalid params).
- Método desconhecido: `-32601` (Method not found).
- `initialize` legado: `-32601`, com mensagem que nomeia `2026-07-28`. O
  servidor não inicia handshake legado.
- Erro de parsing: `-32700`. Requisição inválida: `-32600`.

### `tools/list` e `tools/call`

`tools/list` devolve o catálogo determinístico. `tools/call` executa uma tool e
devolve `content` (texto) e `structuredContent` (JSON). Todo resultado inclui
`resultType: "complete"`.

Listagens usam cursores opacos. Quando há continuação, a resposta inclui
`nextCursor`; a ausência do campo indica o fim. Um cursor inválido retorna
`-32602`.

## Tools

Todas as tools são somente leitura (`readOnlyHint: true`,
`openWorldHint: false`, `idempotentHint: true`). Datas usam o formato
`AAAA-MM-DD`.

| Tool | Argumentos | Resultado |
| --- | --- | --- |
| `data_referencia` | nenhum | `data_referencia`, `origem`, `disponivel`, `cached_at` |
| `consultar_curva` | `data?`, `curva?`, `cursor?`, `limite?` | itens da curva curta ou longa + `nextCursor` |
| `exportar_curva_curta` | `data?` | CSV `DATA;DU252;DC365;TAXA` + datas indisponíveis |
| `exportar_curva_longa` | `data?` | CSV `DATA;ANO;TAXA_MEDIA` + datas indisponíveis |
| `analise` | `data?`, `curva?` | texto da análise e da evolução + datas indisponíveis |
| `evolucao` | `data?`, `cursor?`, `limite?` | resumo por data + datas indisponíveis |
| `estatisticas` | `data?` | menor/máxima, taxa curta/longa, inclinação e juro real |
| `listar_datas` | `cursor?`, `limite?` | datas em cache, da mais recente para a mais antiga |
| `tesouro_vendas` | `titulo?`, `inicio?`, `fim?`, `agregar?`, `cursor?`, `limite?` | vendas do Tesouro no cache local, com filtros, agregação e paginação |

### `data_referencia`

Devolve a data resolvida da última carga bem-sucedida. A data vem do settings
(`data_referencia`); se a chave não existir ou for inválida, usa a maior data
válida do cache. Se não houver cache, devolve erro de domínio `cache_vazio`.

```json
{
  "data_referencia": "2026-06-10",
  "origem": "settings",
  "disponivel": true,
  "cached_at": "2026-06-10T18:00:00+00:00"
}
```

A data é atualizada por `atualizar`, pela preparação do `mcp` e por uma carga
bem-sucedida da GUI. `consultar` e `exportar` não alteram a referência.

### `consultar_curva`

`curva=curta` (padrão) devolve os registros brutos:

```json
{
  "data": "2026-06-10",
  "curva": "curta",
  "itens": [
    { "du252": 1, "dc365": 1, "taxa": 14.9, "taxa_texto": "14,90" }
  ]
}
```

`curva=longa` devolve uma linha por ano com menor taxa, maior taxa e taxa média:

```json
{
  "ano": 0,
  "menor_taxa": 14.5,
  "maior_taxa": 15.1,
  "taxa_media": 14.8
}
```

A data segue as regras da CLI: não pode ser futura, deve estar nos últimos 30
dias e fins de semana retrocedem para a sexta-feira anterior.

### `exportar_curva_curta` e `exportar_curva_longa`

Devolvem o mesmo conteúdo dos artefatos de `exportar`, sem gravar arquivos:

```json
{
  "nome": "curva-curta.csv",
  "content_type": "text/csv",
  "conteudo": "DATA;DU252;DC365;TAXA\n...",
  "datas_indisponiveis": ["2026-06-03"]
}
```

### `analise`

Devolve o texto determinístico da análise da curva e, quando houver data
anterior, da evolução.

- `curva=curta` (padrão): análise sobre os registros brutos.
- `curva=longa`: análise sobre a série de taxas médias por ano. A taxa curta é
  a média do primeiro ano, a taxa longa é a média do último ano e a inclinação
  usa essas médias.

```json
{
  "data": "2026-06-10",
  "curva": "longa",
  "texto": "Análise da Curva Longa (taxa média por ano)\n\n...",
  "datas_indisponiveis": []
}
```

A análise longa usa a mesma base do CSV `DATA;ANO;TAXA_MEDIA`. Ela não usa os
valores mínimo/máximo da tabela `consultar --curva longa`.

### `evolucao`

Resumo estruturado da janela de cinco datas:

```json
{
  "data_base": "2026-06-10",
  "itens": [
    {
      "data": "2026-06-10",
      "total_registros": 120,
      "menor_taxa": 14.2,
      "maior_taxa": 15.6,
      "taxa_curta": 14.9,
      "taxa_longa": 15.4,
      "inclinacao_bps": 50.0
    }
  ],
  "datas_indisponiveis": []
}
```

### `estatisticas`

```json
{
  "data": "2026-06-10",
  "total_registros": 120,
  "menor_taxa": 14.2,
  "maior_taxa": 15.6,
  "taxa_curta": 14.9,
  "taxa_longa": 15.4,
  "inclinacao_bps": 50.0,
  "juro_real": 11.9
}
```

### `listar_datas`

Lista as datas válidas do cache, da mais recente para a mais antiga. Cache vazio
devolve `{"itens": []}`, não erro.

```json
{
  "itens": [
    {
      "data": "2026-06-17",
      "total_registros": 120,
      "cached_at": "2026-06-17T18:00:00+00:00",
      "fonte": "GetDownloadFile"
    }
  ]
}
```

### `tesouro_vendas`

Consulta somente o cache local de vendas do Tesouro Direto. A tool não acessa a
rede, não baixa arquivos e não grava estado. Prepare o cache antes com
`b3-selic-pre tesouro`.

`titulo` é parcial e ignora caixa/acentos; `inicio` e `fim` são inclusivos em
`AAAA-MM-DD`. Sem datas, o período é de 30 dias até a maior `data_liquidacao`.
`agregar=true` devolve `agregados` com `quantidade` e `valor` somados e
`pu_medio = valor / quantidade`.

```json
{
  "dataset": "vendas",
  "origem": "cache",
  "data_extracao": "2026-10-20T00:00:00+00:00",
  "publicado_em": "2026-10-16T10:29:05",
  "data_maxima_liquidacao": "2026-10-14",
  "total_registros": 2,
  "periodo": { "inicio": "2026-09-14", "fim": "2026-10-14" },
  "registros": [
    {
      "tipo_titulo": "Tesouro Selic 2029",
      "vencimento": "2029-01-02",
      "data_liquidacao": "2026-10-14",
      "pu": "15000.000000",
      "quantidade": "2.00",
      "valor": "30000.00"
    }
  ]
}
```

Quando há mais itens que `limite`, a resposta inclui `nextCursor`. Sem cache de
vendas, devolve `cache_vazio` com a dica de executar `b3-selic-pre tesouro`.

## Erros de domínio

Erros recuperáveis são devolvidos como resultado estruturado, sem `isError`:

```json
{
  "motivo": "sem_dados",
  "detalhe": "Não há registros em cache para 2026-06-10.",
  "dica": "Execute `b3-selic-pre mcp --data 2026-06-10` para preparar o cache."
}
```

Motivos usados:

| Motivo | Significado |
| --- | --- |
| `data_invalida` | Formato de data inválido |
| `data_futura` | Data posterior a hoje |
| `data_antiga` | Data fora da janela de 30 dias |
| `sem_dados` | Data válida, mas sem registros no cache |
| `cache_vazio` | Nenhuma data de referência válida nem cache |
| `periodo_invalido` | `inicio` maior que `fim` na `tesouro_vendas` |
| `dados_invalidos` | CSV de vendas em cache inválido |

Falhas internas não tratadas são devolvidas com `isError: true`, com mensagem
genérica; o traceback vai para `stderr` e o servidor continua atendendo.

## Cache e settings

Caminhos padrão:

```text
$XDG_CACHE_HOME/b3-selic-pre/rates/AAAA-MM-DD.json   # curvas
$XDG_CACHE_HOME/b3-selic-pre/tesouro/vendastesourodireto.csv
$XDG_CACHE_HOME/b3-selic-pre/tesouro/metadata.json    # vendas do Tesouro
$XDG_CONFIG_HOME/b3-selic-pre/settings.json          # data_referencia
```

Em Linux sem variáveis XDG, os caminhos ficam em `~/.cache` e `~/.config`.

O servidor lê o cache em modo somente leitura. Entradas ausentes, vencidas,
corrompidas ou incompletas são tratadas como miss; nenhum arquivo é removido ou
alterado durante o atendimento.

## Docker

### Imagem a partir do código fonte

O import da GUI é preguiçoso, então o comando `mcp` não precisa de Tk ou
matplotlib. A imagem abaixo instala o pacote sem dependências gráficas:

```dockerfile
# Dockerfile.mcp.source
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir --no-deps .

ENV XDG_CACHE_HOME=/data/cache \
    XDG_CONFIG_HOME=/data/config

VOLUME ["/data"]
ENTRYPOINT ["b3-selic-pre"]
CMD ["mcp"]
```

Build e preparação:

```bash
docker build -f Dockerfile.mcp.source -t b3-selic-pre-mcp .

# A preparação precisa de rede para acessar a B3
docker run --rm -v b3-selic-pre-data:/data \
  b3-selic-pre-mcp mcp --data 2026-06-10
```

Atendimento somente leitura, sem rede:

```bash
docker run -i --rm --network none \
  -v b3-selic-pre-data:/data \
  b3-selic-pre-mcp mcp
```

Não use `-t` no atendimento MCP: um TTY pode interferir no framing de
stdin/stdout. Use apenas `-i`.

### Imagem a partir do binário PyInstaller

Gere o binário com `make build` e use uma imagem multi-stage. Build e runtime
devem compartilhar a mesma família glibc; não use Alpine/musl.

```dockerfile
# Dockerfile.mcp.binary
FROM python:3.12-bookworm AS build

WORKDIR /src
COPY . .
RUN pip install --no-cache-dir . pyinstaller \
    && pyinstaller b3-selic-pre.spec

FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /src/dist/b3-selic-pre /usr/local/bin/b3-selic-pre

ENV XDG_CACHE_HOME=/data/cache \
    XDG_CONFIG_HOME=/data/config

VOLUME ["/data"]
ENTRYPOINT ["b3-selic-pre"]
CMD ["mcp"]
```

Build e execução:

```bash
docker build -f Dockerfile.mcp.binary -t b3-selic-pre-mcp-bin .

docker run --rm -v b3-selic-pre-data:/data \
  b3-selic-pre-mcp-bin mcp --data 2026-06-10

docker run -i --rm --network none \
  -v b3-selic-pre-data:/data \
  b3-selic-pre-mcp-bin mcp
```

O binário inclui GUI/gráficos e é maior que a imagem de fonte. A imagem de
fonte com `--no-deps` é a opção enxuta para uso exclusivo do MCP.

### Configuração do cliente MCP

Exemplo com Docker:

```json
{
  "mcpServers": {
    "b3-selic-pre": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "none",
        "-v",
        "b3-selic-pre-data:/data",
        "b3-selic-pre-mcp",
        "mcp"
      ]
    }
  }
}
```

Exemplo com o binário local:

```json
{
  "mcpServers": {
    "b3-selic-pre": {
      "command": "b3-selic-pre",
      "args": ["mcp"]
    }
  }
}
```

## Segurança e limitações

- O transporte `stdio` herda a confiança do processo que lança o servidor. Não
  há autenticação nem multiusuário.
- O atendimento é somente leitura: não há tool de atualização, download, log ou
  escrita de arquivos.
- Logs e diagnósticos vão para `stderr`; no modo MCP o arquivo de log ativo não
  é gravado.
- `consultar` e `exportar` não alteram `data_referencia`.
- O lock de ação cobre `atualizar` e a preparação do MCP. `consultar`,
  `exportar` e a GUI ainda podem gravar cache concorrentemente; a escrita é
  atômica para evitar leitura de conteúdo parcial.
- Clientes legados que enviam `initialize` recebem erro; é necessário um cliente
  com suporte a `2026-07-28`.

## Solução de problemas

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| `initialize` rejeitado | Cliente legado | Atualize o cliente para `2026-07-28` |
| `cache_vazio` | Sem cache e sem settings | Rode `b3-selic-pre mcp --atualizar` |
| `sem_dados` | Data sem entrada no cache | Prepare a data com `--data` |
| `data_antiga` | Data fora dos últimos 30 dias | Use uma data recente |
| Cliente não recebe resposta | `-t` no Docker ou stdout poluído | Use `-i` e não escreva em stdout |
| Container sem rede falha na preparação | Preparação precisa da B3 | Prepare em uma execução com rede e depois atenda com `--network none` |
