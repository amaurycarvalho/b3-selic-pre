## Why

A aplicação já expõe a curva SELIC Pré por CLI e GUI, mas agentes externos não têm uma interface estruturada e somente leitura para consultar os mesmos dados. Um servidor MCP via `stdio`, iniciado explicitamente por `b3-selic-pre mcp`, permite que clientes MCP consultem curvas, evolução, análise e estatísticas sem duplicar regras nem abrir acesso de rede durante o atendimento.

## What Changes

- Adicionar o subcomando `b3-selic-pre mcp`, com transporte `stdio` e encerramento em EOF.
- Implementar a revisão MCP `2026-07-28`: `_meta` por requisição, `server/discover`, `tools/list`, `tools/call`, `UnsupportedProtocolVersionError`, erros para `initialize` legado e cancelamento.
- Expor tools somente leitura: `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas` e `listar_datas`.
- Preparar dados opcionalmente na inicialização com `--atualizar` e `--data <AAAA-MM-DD>`, reutilizando a carga de `atualizar`, sob lock de ação, com progresso em `stderr` e sem iniciar o servidor em caso de falha.
- Persistir `data_referencia` no settings da aplicação, atualizado por `atualizar`, preparação do MCP e carga da GUI; `consultar` e `exportar` não alteram a referência.
- Tornar a leitura do cache somente leitura no MCP e a escrita de cache/settings atômica.
- Permitir selecionar a análise da curva curta ou longa, com a curva longa definida pela taxa média por ano; adicionar `exportar --analise-curva curta|longa`.
- Documentar o servidor e as tools em `docs/misc/mcp.md`, incluindo execução em Docker a partir do código fonte e do binário PyInstaller, e registrar uma seção breve no `README.md`.
- **Non-goals**: tool de log ou metadados de log; tool de atualização ou qualquer acesso à B3/CVM durante o atendimento; transporte HTTP/SSE; autenticação/multiusuário; escrita de arquivos pelas tools.

## Capabilities

### New Capabilities
- `mcp-server`: subcomando, transporte stdio, protocolo `2026-07-28`, descoberta, versionamento, ciclo de vida, cancelamento, pureza de stdout, preparação e garantia de somente leitura.
- `mcp-tools`: catálogo e contrato das tools, entradas/saídas estruturadas, paginação, `data_referencia` e envelope de erros de domínio.

### Modified Capabilities
- `cli-interface`: novo subcomando `mcp` e nova opção `exportar --analise-curva`.
- `persistence`: chave `data_referencia`, escrita atômica e leitura tolerante a arquivo ausente/corrompido.
- `disk-cache`: leitura sem mutação para o MCP e escrita atômica para produtores.
- `headless-application-services`: transformação para curva longa e payloads headless reutilizados pelo MCP.
- `novo-resumo-executivo`: análise sobre as representações curta e longa, com a longa baseada na taxa média por ano.
- `application-logging`: no modo MCP, logs e diagnósticos vão para `stderr`, sem gravar no arquivo de log.

## Impact

- Novos módulos em `presentation/mcp/`, `application/mcp_services.py` e `infrastructure` (lock e leitura de cache).
- Alterações em `presentation/cli.py`, `cli_parser.py`, `cli_commands.py`, `gui/fetch.py`, `settings.py`, `disk_cache.py`, `application/cli_services.py` e `application/analyze`.
- Nenhuma dependência externa nova; o servidor usa apenas a biblioteca padrão.
- Import preguiçoso da GUI na CLI para permitir imagem Docker enxuta com `pip install --no-deps`.
- Documentação em `docs/misc/mcp.md`, `docs/misc/cli.md` e `README.md`.
- Testes headless de protocolo, tools, cache, preparação e análise; suíte completa por envolver CLI, cache e contratos compartilhados.
