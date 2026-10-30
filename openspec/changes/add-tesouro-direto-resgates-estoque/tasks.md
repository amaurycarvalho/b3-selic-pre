## 0. Pré-requisito e spike complementar

> Esta change depende de `add-tesouro-direto-vendas`. A infraestrutura de cliente, cache, erros e CLI deve existir antes das tarefas abaixo.

- [x] 0.1 Consultar o CKAN e registrar os pacotes, recursos, UUIDs, tamanhos, schemas e periodicidades de resgates e estoque.
- [x] 0.2 Baixar amostras e confirmar encoding, delimitador, datas, decimais, volumes e duplicatas.
- [x] 0.3 Confirmar que recompras não tem `PU`, que cupom/vencimentos tem e que o cupom mais novo é superconjunto do antigo.
- [x] 0.4 Confirmar que estoque é mensal e usa `Mes Estoque` e `Valor Estoque`.

## 1. Núcleo de domínio e aplicação

- [ ] 1.1 Adicionar `ResgateTesouroDireto` em `domain/models.py` com `tipo_resgate`, `tipo_titulo`, `vencimento`, `data_resgate`, `pu` opcional, `quantidade` e `valor`.
- [ ] 1.2 Adicionar `EstoqueTesouroDireto` em `domain/models.py` com `tipo_titulo`, `vencimento`, `mes`, `pu`, `quantidade` e `valor_estoque`.
- [ ] 1.3 Adicionar as constantes dos pacotes `resgates-do-tesouro-direto` e `estoque-do-tesouro-direto` em `domain/constants.py`.
- [ ] 1.4 Generalizar `application/tesouro/` para um registro de recursos com schema por recurso (recompras, cupom, vencimentos e estoque).
- [ ] 1.5 Implementar parsing de resgates por recurso, com `tipo_resgate` derivado do recurso, datas, decimais e validação de cabeçalho.
- [ ] 1.6 Implementar parsing de estoque, com `Mes Estoque` `MM/YYYY` para `AAAA-MM` e `Valor Estoque`.
- [ ] 1.7 Implementar filtros, agregação e ordenação de resgates, incluindo `PU` ponderado apenas quando todas as linhas do grupo tiverem `PU`.
- [ ] 1.8 Implementar filtros, agregação e ordenação de estoque, sem somar `valor_estoque` entre meses.
- [ ] 1.9 Implementar formatação CSV/JSON de resgates e estoque, incluindo versões agregadas.
- [ ] 1.10 Adicionar testes headless de parsing, filtros, agregação e formatação.

## 2. Infraestrutura

- [ ] 2.1 Generalizar `tesouro_client.py` para descobrir múltiplos pacotes e selecionar recursos por nome/filename.
- [ ] 2.2 Implementar a seleção do cupom mais novo por `last_modified`, rejeitando ambiguidade.
- [ ] 2.3 Reutilizar o download com timeout de 60 s, retry transitório, `ETag`/`Last-Modified`, `304` e validação de corpo parcial.
- [ ] 2.4 Generalizar `tesouro_cache.py` para cache por recurso, com CSV e metadata independentes e TTL condicional (1 h corrente, 6 h histórico, 24 h mensal/eventual).
- [ ] 2.5 Preservar a versão anterior de um recurso quando o download falhar e permitir que os demais continuem.
- [ ] 2.6 Implementar/estender `tesouro_cached_client.py` para resgates e estoque, com `force` e leitura somente leitura.
- [ ] 2.7 Adicionar testes de descoberta, seleção de cupom, cache por recurso e falha isolada.

## 3. CLI

- [ ] 3.1 Adicionar `tesouro-resgates` e `tesouro-estoque` em `presentation/cli_parser.py`, com `--saida` para exportação.
- [ ] 3.2 Implementar os handlers em `presentation/cli_commands.py`, reutilizando validação de datas, códigos `0`/`1`/`2`, classes de erro e escrita via `--saida`.
- [ ] 3.3 Implementar os defaults: resgates 30 dias; estoque último mês.
- [ ] 3.4 Implementar `--agregar` de resgates (tipo + título) e de estoque (mês único + título).
- [ ] 3.5 Despachar os subcomandos em `presentation/cli.py` e montar os clientes no composition root.
- [ ] 3.6 Cobrir com testes headless: filtros, defaults, agregação, CSV, JSON, `--saida` (arquivo/diretório), `--no-cache`, erros e resultado vazio.
- [ ] 3.7 Atualizar `docs/misc/cli.md` e `README.md` com os subcomandos e a exportação via `--saida`.

## 4. MCP

- [ ] 4.1 Adicionar `tesouro_resgates` e `tesouro_estoque` ao catálogo em `presentation/mcp/catalog.py`, atualizando a lista completa de tools somente leitura; verificar teste do catálogo.
- [ ] 4.2 Estender `ToolContext`, `Dispatcher`, `McpServer` e `run_mcp_command` para injetar o leitor de cache do Tesouro; verificar teste de composição headless.
- [ ] 4.3 Implementar os handlers `tesouro_resgates` e `tesouro_estoque` reutilizando filtros, agregação, ordenação e paginação; verificar testes de consulta, agregação e `nextCursor`.
- [ ] 4.4 Cobrir `cache_vazio`, período vazio, cursor inválido, agregação de estoque com mais de um mês, leitura somente cache e ausência de rede/escrita; verificar testes headless.
- [ ] 4.5 Atualizar `docs/misc/mcp.md` e `README.md` com as tools e a preparação dos caches via subcomandos de dados.

## 5. Documentação

- [ ] 5.1 Atualizar `docs/misc/datasources.md` com os pacotes, recursos, schemas, duplicata de cupom e cache por recurso.
- [ ] 5.2 Revisar a consistência entre specs, `docs/misc/cli.md` e `README.md` após a implementação.
- [ ] 5.3 Atualizar o CHANGELOG.

## 6. Testes e validação

- [ ] 6.1 Testar imutabilidade e tipos dos modelos.
- [ ] 6.2 Testar descoberta, seleção do cupom mais novo e recursos ausentes/ambíguos.
- [ ] 6.3 Testar download/cache por recurso, 304, corpo parcial, falha isolada e leitura somente leitura.
- [ ] 6.4 Testar parsing de recompras sem `PU`, cupom/vencimentos com `PU` e estoque mensal.
- [ ] 6.5 Testar filtros, agregação, `PU` ponderado, não soma de estoque entre meses e ordenação.
- [ ] 6.6 Testar formatação CSV/JSON, versões agregadas e exportação via `--saida`.
- [ ] 6.7 Testar o catálogo, os handlers MCP, a paginação e o erro `cache_vazio`; verificar que as tools não acessam a rede.
- [ ] 6.8 Rodar `make lint`, `make complexity` e `make test`; registrar a justificativa da suíte completa.
- [ ] 6.9 Registrar um teste manual opcional da CLI e das tools MCP.
