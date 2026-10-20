## Context

O projeto já tem CLI com subcomandos, cache XDG validado por completude, settings em JSON e serviços headless de análise/exportação. Não há lock entre processos, não há data de referência persistida e a CLI importa a GUI no topo, o que puxa Tk/matplotlib mesmo para comandos que não abrem janela. Ver `proposal.md` para a motivação e `specs/` para os contratos.

A revisão MCP `2026-07-28` é stateless: cada requisição carrega versão e capacidades em `_meta`, não há `initialize`, `server/discover` é obrigatório e versões não suportadas retornam `-32022`. O transporte `stdio` usa uma mensagem JSON-RPC por linha, proíbe qualquer outra saída em `stdout` e encerra no EOF.

## Goals / Non-Goals

**Goals:**

- Servidor MCP somente leitura, stateless e sem dependências externas.
- Reutilizar os mesmos núcleos de carga, cache, análise e formatação da CLI.
- Garantir pureza de `stdout`, cancelamento e continuidade após falhas internas.
- Preparação opcional segura, com lock compartilhado com `atualizar`.
- Análise curta/longa coerente com o motor atual.
- Documentação e imagens Docker a partir do fonte e do binário PyInstaller.

**Non-Goals:**

- Transporte HTTP/SSE, autenticação, multiusuário ou execução remota.
- Tools de atualização, download, extração, escrita ou log.
- Cache de análise ou cache de respostas MCP.
- Mudar a análise da GUI para refletir a representação exibida.
- Alterar o schema do cache ou migrar dados existentes.

## Decisions

### 1. Servidor JSON-RPC em stdlib, sem SDK MCP

**Decisão:** implementar o loop JSON-RPC, a validação de `_meta`, a descoberta e o despacho de tools com `json`, `sys`, `threading` e `base64` (para cursores). Nenhuma dependência nova.

**Alternativas:** usar um SDK MCP. Rejeitado porque adiciona dependência, pode não suportar `2026-07-28` e aumenta o binário PyInstaller. O contrato é pequeno e testável.

**Consequência:** precisamos manter o parser e os códigos de erro por conta própria, cobertos por testes de conformidade.

### 2. Distribuição em camadas e composition root

```text
presentation/cli.py (composition root)
  |-- mcp [--atualizar|--data] --> prepara? --> run_mcp(cache_reader, settings_reader)
  |
  +--> presentation/mcp/
  |      protocol.py   JSON-RPC, _meta, versão, erros, stdout
  |      server.py     loop, dispatcher, cancelamento, EOF
  |      tools.py      catálogo, schemas, validação de argumentos
  |
  +--> application/mcp_services.py
  |      payloads estruturados, paginação, envelope de erros
  |      transformação para curva longa, análise por representação
  |
  +--> infrastructure/
         disk_cache (modo somente leitura e escrita atômica)
         action_lock (lock de arquivo)
```

`presentation/mcp` importa apenas `domain`/`application`/`presentation`. O leitor de cache é injetado pelo `cli.py` como protocolo, evitando que a presentation importe `infrastructure`. Não há nova entrada em `tests/architecture_allowlist.py`.

### 3. Loop, concorrência e cancelamento

**Decisão:** uma thread principal lê linhas de `stdin`. Requisições são submetidas a um pool pequeno de workers; um mapa `request_id -> Event` permite cancelamento. Notificações são processadas na thread leitora. O worker verifica o `Event` antes de começar e antes de escrever a resposta. Requisição cancelada não recebe resposta. `EOF` sinaliza parada, cancela futuros e encerra com `0`.

**Concorrência de escrita:** um `Lock` serializa a escrita de cada linha JSON em `stdout`.

**Cancelamento:** `notifications/cancelled` com `requestId` marca o evento. IDs desconhecidos ou já concluídos são ignorados.

### 4. Pureza de stdout

**Decisão:** no início do servidor, capturar o `stdout` real em `protocol_out` e substituir `sys.stdout` por `sys.stderr` durante todo o atendimento. O escritor JSON-RPC usa apenas `protocol_out`. Assim, qualquer `print` acidental de código existente ou de biblioteca vai para `stderr` e não corrompe o protocolo.

**Logging:** configurar o logger raiz com `StreamHandler(sys.stderr)` no modo MCP. Não abrir o arquivo de log ativo. A preparação também escreve progresso em `stderr`.

### 5. Protocolo e versionamento

**Decisão:** suportar apenas `2026-07-28`.

- Toda requisição deve ter `_meta.io.modelcontextprotocol/protocolVersion` e `_meta.io.modelcontextprotocol/clientCapabilities`; ausência retorna `-32602`.
- Versão diferente de `2026-07-28` retorna `-32022` com `data.supported` e `data.requested`.
- `server/discover` retorna `resultType`, `supportedVersions`, `capabilities.tools`, `_meta.io.modelcontextprotocol/serverInfo` e `instructions`.
- Todo resultado inclui `resultType: "complete"` e `_meta` com `serverInfo`.
- `initialize` é tratado antes da validação genérica de `_meta` e retorna `-32601` com mensagem que nomeia `2026-07-28`.
- `tools/list` é determinístico e suporta `cursor`/`nextCursor`.
- `tools/call` desconhecida retorna `-32602`.

**Alternativa:** servidor dual-era com `initialize`. Rejeitado pelo escopo: o requisito é implementar a revisão moderna e rejeitar o handshake legado com mensagem útil.

### 6. Catálogo e payloads das tools

**Decisão:** o catálogo e os schemas ficam em `presentation/mcp/tools.py`; a montagem dos dados fica em `application/mcp_services.py`.

Tools da v1:

- `data_referencia`
- `consultar_curva`
- `exportar_curva_curta`
- `exportar_curva_longa`
- `analise`
- `evolucao`
- `estatisticas`
- `listar_datas`

Regras comuns:

- Datas usam as mesmas funções de validação/resolução da CLI.
- Valores monetários/taxas em payloads estruturados são numéricos; a representação textual original é preservada quando relevante.
- `nextCursor` fica dentro do payload da tool, não no topo do resultado `tools/call`.
- Cursores são opacos: `base64url` de um JSON com versão e offset; cursor inválido retorna `-32602`.
- Erros de domínio retornam `resultType: complete`, `structuredContent` com `motivo`, `detalhe`, `dica` e um `TextContent` com o JSON serializado; sem `isError`.
- Falhas internas retornam `isError: true`, mensagem genérica e traceback apenas em `stderr`.

### 7. Cache somente leitura e escrita atômica

**Decisão:** adicionar `read_only=True` ao acesso ao cache. Nesse modo, entradas inválidas, vencidas, corrompidas ou incompletas retornam miss sem `unlink`. O MCP nunca usa o cliente B3.

A escrita de cache passa a ser atômica: serializar em arquivo temporário no mesmo diretório e aplicar `os.replace`. A validação de completude e a regra de não gravar resultado vazio permanecem.

**Motivo:** o lock cobre apenas `atualizar` e a preparação do MCP. `consultar`, `exportar` e a GUI ainda podem gravar cache concorrentemente; a escrita atômica evita que o leitor veja JSON parcial.

### 8. `data_referencia` nas configurações

**Decisão:** adicionar `data_referencia` ao JSON de settings.

Escritores:

- `atualizar`, após carga bem-sucedida, com a data resolvida.
- preparação do `mcp`, após carga bem-sucedida, inclusive se tudo veio do cache.
- GUI, após carga bem-sucedida.

Não escrevem: `consultar`, `exportar`, leituras de cache e o servidor MCP.

O MCP lê a configuração a cada chamada de `data_referencia` (instância nova ou recarga), porque outro processo pode atualizar o arquivo durante o atendimento. Se a chave estiver ausente/inválida, usa a maior data válida do cache. Se não houver cache, retorna `cache_vazio`. Se a data configurada não tiver entrada no cache, retorna a data com `disponivel: false`.

`Settings._save` passa a ser atômico (`NamedTemporaryFile` no mesmo diretório + `os.replace`). Isso evita leitura parcial; não resolve lost updates entre processos, que fica documentado como limitação.

### 9. Lock de ação com escopo mínimo

**Decisão:** lock de arquivo em `$XDG_CACHE_HOME/b3-selic-pre/action.lock`, usado por `atualizar` e pela preparação do MCP. Implementação stdlib com `fcntl.flock` no POSIX e `msvcrt.locking` no Windows.

- Aquisição bloqueante com timeout configurável (padrão 300 s).
- Progresso de espera em `stderr`.
- Liberação em `finally`, antes de iniciar o loop MCP.
- O servidor não adquire o lock ao atender.

**Alternativa:** lock em todas as ações de escrita. Rejeitada pelo escopo escolhido; a mitigação para concorrência residual é a escrita atômica.

### 10. Preparação reutilizando `atualizar`

**Decisão:** extrair a carga de `atualizar` para uma função pública compartilhada que executa `fetch_rates_for_date` e `fetch_historical_rates`. A preparação do MCP chama a mesma função, sem imprimir a análise, com callbacks de progresso/fonte direcionados a `stderr`.

Semântica:

- `--atualizar` sem data: data resolvida de hoje.
- `--data D`: carga de D.
- ambos: uma única carga de D.
- falha: erro em `stderr`, código diferente de zero, servidor não inicia.

### 11. Análise curta e longa

**Decisão:** “curta” usa registros brutos; “longa” usa a série de taxas médias por ano.

- A transformação usa `consolidate_by_year`/`average_rate_by_year` e cria um `RateRecord` por ano com dias sintéticos (`ano * 252`, `ano * 365`). Os dias servem apenas para ordenação; o motor atual usa a ordem e as taxas.
- O histórico é convertido por data antes de calcular estabilidade e steepening.
- `build_analysis_text` e `build_export_artifacts` aceitam a representação.
- `exportar --analise-curva curta|longa` é independente de `--curva`; sem `--analise`, é erro de uso.
- A tool `analise` aceita `curva` e devolve o texto da representação solicitada.
- Não há cache de análise na v1. Se um dia houver, o artefato carrega a representação e só é reutilizado quando ela coincide.

**Racional:** a série média é a única base coerente para taxa curta, taxa longa e inclinação; usar mínimo/máximo misturaria extremos de anos distintos e exageraria a inclinação.

### 12. Import preguiçoso da GUI

**Decisão:** mover o import de `launch_gui` para dentro do ramo `gui` em `presentation/cli.py`. O spec do PyInstaller continua listando os hiddenimports de GUI; o binário empacotado mantém a GUI.

**Motivo:** permite `pip install --no-deps .` na imagem Docker de fonte e mantém o servidor MCP com apenas stdlib. Comandos não-GUI (incluindo `mcp`) não precisam de Tk/matplotlib.

### 13. Docker

Documentar em `docs/misc/mcp.md`:

- Imagem de fonte: `python:3.12-slim`, `pip install --no-deps .`, `XDG_CACHE_HOME=/data/cache`, `XDG_CONFIG_HOME=/data/config`, volume `/data`.
- Imagem PyInstaller: build em `python:3.12-bookworm`, runtime `debian:bookworm-slim` com `ca-certificates`; copiar `dist/b3-selic-pre`. Não usar Alpine/musl.
- Execução: `docker run -i --rm ...` sem `-t`; `--network none` durante o atendimento; preparação em execução separada ou com rede.
- Configuração do cliente MCP com `command: docker` e args.

## Risks / Trade-offs

- **[Clientes legados não conectam]** → O requisito é moderno; documentar que `initialize` é rejeitado e que o cliente precisa de `2026-07-28`.
- **[Concorrência residual de cache]** → Lock cobre só `atualizar`/preparação; `consultar`/`exportar`/GUI podem gravar. Mitigação: escrita atômica e leitura tolerante. Documentar.
- **[Settings com lost update]** → Escrita atômica evita corrupção, não serializa atualizações concorrentes. Mitigação: lock cobre os caminhos de atualização/preparação; GUI pode sobrescrever chaves. Documentar.
- **[Duas formas de “curva longa”]** → `consultar --curva longa` mostra min/max; `exportar --curva longa` e a análise usam média. Documentar explicitamente para evitar interpretação errada.
- **[RateRecord sintético]** → Dias sintéticos não representam vencimentos reais; são um adaptador interno para reutilizar o motor. Se o motor passar a usar dias, revisar.
- **[Imagem PyInstaller grande]** → O binário inclui GUI/gráficos. Documentar o tamanho e oferecer a imagem de fonte com `--no-deps` como alternativa enxuta.
- **[Falha de escrita de settings]** → `Settings._save` engole `OSError`; a data pode não persistir. Fallback para o cache cobre o `data_referencia`.
- **[Protocolo novo e pouco testado em clientes]** → Testes de conformidade locais e documentação de `server/discover`/erros; smoke test com um cliente MCP real.

## Migration Plan

1. Adicionar a chave `data_referencia` com default vazio; settings existentes continuam válidos.
2. Não alterar o schema do cache; a leitura somente leitura aceita o schema atual.
3. O lock é aditivo e só é adquirido por `atualizar`/preparação.
4. A análise curta permanece o padrão; `--analise-curva` é aditivo.
5. O subcomando `mcp` é aditivo; nenhum comando existente muda de nome.
6. Rollback: remover o subcomando e as tools; o cache e o settings antigos continuam legíveis (a chave extra é ignorada).

## Open Questions

Nenhuma pendente para iniciar a implementação. A definição de “curva longa” como taxa média por ano e o escopo mínimo do lock estão fechados.
