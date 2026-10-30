## 0. Spike de descoberta (concluído)

> Evidências completas em `docs/rfcs/RFC-001 - Vendas do Tesouro Direto.md`, seção 12.

- [x] 0.1 Consultar o CKAN (`package_show`) e registrar o endpoint real, o identificador/nome do dataset, os metadados e as URLs dos recursos.
- [x] 0.2 Baixar uma amostra do CSV e registrar tamanho, encoding, BOM, delimitador, cabeçalho e primeiras linhas.
- [x] 0.3 Verificar se o dataset contém apenas vendas ou também resgates/saldo; decidir o nome final do modelo (`VendaTesouroDireto`) e os campos/tipos definitivos.
- [x] 0.4 Verificar `ETag`, `Last-Modified`, resposta `304`, periodicidade de atualização e defasagem real dos dados.
- [x] 0.5 Incorporar o schema verificado em `proposal.md`, `design.md`, `specs/` e `tasks.md`.

> Resgates e estoque foram confirmados como datasets separados e ficam fora desta change. A change `add-tesouro-direto-resgates-estoque` reutilizará cliente, cache e CLI.

## 1. Núcleo de domínio e aplicação

- [x] 1.1 Adicionar o frozen dataclass `VendaTesouroDireto` em `src/b3_selic_pre/domain/models.py`, com `tipo_titulo`, `vencimento`, `data_liquidacao`, `pu`, `quantidade` e `valor`; usar `Decimal` nos três valores e strings ISO nas datas.
- [x] 1.2 Adicionar `TESOURO_CKAN_BASE_URL` e `TESOURO_DATASET_NAME` em `src/b3_selic_pre/domain/constants.py`; manter `TESOURO_CACHE_TTL_MINUTES` na infraestrutura do cache.
- [x] 1.3 Criar `src/b3_selic_pre/application/tesouro/__init__.py` com a API pública de processamento, filtros, agregação, ordenação e formatação; adicionar `TesouroDataError` e o erro de validação de período.
- [x] 1.4 Implementar `src/b3_selic_pre/application/tesouro/_processamento.py` recebendo os bytes baixados, sem I/O de arquivo/rede: decodificação `utf-8-sig`/`utf-8`/`latin-1`, delimitador `;`, cabeçalho confirmado, datas `DD/MM/YYYY` para ISO, decimais com vírgula para `Decimal`, erros com linha/coluna, preservação de duplicatas, filtros, agregação com `PU` ponderado e ordenação determinística.
- [x] 1.5 Implementar `src/b3_selic_pre/application/tesouro/_formatting.py` reutilizando os padrões de `src/b3_selic_pre/application/formatting.py`; a aplicação devolve texto/dict e a presentation serializa JSON. CSV de vendas, CSV agregado e payload JSON devem seguir o schema aprovado.
- [x] 1.6 Adicionar testes headless de processamento, filtros, agregação, ordenação e formatação.

## 2. Infraestrutura

- [x] 2.1 Implementar `src/b3_selic_pre/infrastructure/tesouro_client.py` para descoberta CKAN, validação de `success`, extração do recurso CSV, download em chunks com timeout de 60 s, retry transitório e cabeçalhos condicionais.
- [x] 2.2 Tratar `ETag`/`If-Modified-Since` e `304 Not Modified`, atualizando `checked_at`; validar corpo parcial por `Content-Range`; mapear falhas de rede/HTTP/corpo vazio ou não-CSV para `CommunicationError`.
- [x] 2.3 Implementar `src/b3_selic_pre/infrastructure/tesouro_cache.py` com caminho XDG (`cache_base() / "b3-selic-pre" / "tesouro"`), CSV cumulativo + `metadata.json`, TTL condicional (1 h corrente, 6 h histórico), escrita atômica em bytes, tratamento de cache corrompido e leitura somente leitura.
- [x] 2.4 Implementar `src/b3_selic_pre/infrastructure/tesouro_cached_client.py` com `TesouroDiretoClient`, `force` e caminho de leitura somente leitura.
- [x] 2.5 Integrar `ActionLock` com caminho dedicado `.../tesouro.lock` no composition root para evitar downloads concorrentes entre processos CLI.
- [x] 2.6 Adicionar testes de cliente e cache com `FakeResponse`/`opener`, incluindo 304, retry transitório, corpo parcial, cache corrompido e preservação da versão anterior.
- [x] 2.7 Adicionar `write_atomic_bytes` em `cache_payload.py` (ou generalizar `write_atomic` para bytes) e cobrir com teste.
- [x] 2.8 Adicionar retry transitório para rede/5xx/429/corpo parcial em `b3_retry.py` (ou helper próprio), com backoff/jitter e testes.

## 3. CLI

- [x] 3.1 Adicionar `tesouro` aos subcomandos em `src/b3_selic_pre/presentation/cli_parser.py`, com `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json`, `--no-cache` e `--saida`.
- [x] 3.2 Implementar o handler em `src/b3_selic_pre/presentation/cli_commands.py`, com validação de datas ISO exata (sem `nearest_business_day`), período padrão de 30 dias até a maior data disponível, `inicio <= fim`, códigos `0`/`1`/`2`, `TesouroDataError` e `CommunicationError`.
- [x] 3.3 Despachar o subcomando em `src/b3_selic_pre/presentation/cli.py` e montar o cliente no composition root.
- [x] 3.4 Cobrir o subcomando com testes headless: filtros, período padrão, período invertido, CSV, CSV agregado, JSON, `--saida` (arquivo/diretório), `--no-cache`, erros, resultado vazio e códigos de saída.
- [x] 3.5 Atualizar `docs/misc/cli.md` e `README.md` com o subcomando e a exportação via `--saida`.

## 4. MCP

- [x] 4.1 Adicionar `tesouro_vendas` ao catálogo em `src/b3_selic_pre/presentation/mcp/catalog.py`, com schema, descrição e anotações somente leitura; verificar teste do catálogo.
- [x] 4.2 Estender `ToolContext`, `Dispatcher`, `McpServer` e `run_mcp_command` para injetar o leitor de cache do Tesouro; verificar teste de composição headless.
- [x] 4.3 Implementar o handler `tesouro_vendas` reutilizando filtros, agregação, ordenação e paginação; verificar teste de consulta, agregação e `nextCursor`.
- [x] 4.4 Cobrir `cache_vazio`, período vazio, cursor inválido, leitura somente cache e ausência de rede/escrita; verificar testes headless.
- [x] 4.5 Atualizar `docs/misc/mcp.md` e `README.md` com a tool e a preparação do cache via `tesouro`.

## 5. Documentação

- [x] 5.1 Revisar o RFC-001 após o spike e incorporar o schema verificado.
- [x] 5.2 Revisar a consistência entre RFC, specs, `docs/misc/cli.md` e `README.md` após a implementação.
- [x] 5.3 Atualizar o PRD somente após a implementação e a aprovação final.
- [x] 5.4 Revisar a entrada do CHANGELOG após a implementação.
- [x] 5.5 Atualizar `docs/misc/datasources.md` para incluir o Tesouro Transparente, o CKAN, o CSV, os cabeçalhos, o retry, o cache e a classificação de erros.

## 6. Testes e validação

- [x] 6.1 Testar imutabilidade, campos, tipos `Decimal` e semântica de `data_liquidacao` do modelo de domínio.
- [x] 6.2 Testar o cliente CKAN/CSV com respostas simuladas, incluindo erros, retry, 304 e corpo parcial.
- [x] 6.3 Testar o cache: hit, miss, TTL, corrupção, escrita atômica em bytes, `checked_at` em 304 e leitura somente leitura.
- [x] 6.4 Testar parsing: encoding, delimitador, colunas ausentes/desconhecidas, datas e valores inválidos, duplicatas, filtros, agregação, `PU` ponderado e ordenação.
- [x] 6.5 Testar formatação CSV/JSON, incluindo versão agregada, período vazio e exportação via `--saida`.
- [x] 6.6 Testar o catálogo, o handler MCP, a paginação e o erro `cache_vazio`; verificar que a tool não acessa a rede.
- [x] 6.7 Rodar `make lint`, `make complexity` e `make test`; registrar a justificativa da suíte completa.
- [x] 6.8 Registrar um teste manual opcional da CLI e da tool MCP.
- [x] 6.9 Registrar na change `add-tesouro-direto-resgates-estoque` o escopo de resgates e estoque, reutilizando a infraestrutura desta feature.

> Teste manual opcional: executar `b3-selic-pre tesouro --titulo Selic --agregar`
> e `b3-selic-pre tesouro --json --saida exports/`; iniciar `b3-selic-pre mcp` e
> chamar `tesouro_vendas` com `agregar=true` para conferir a paginação.
