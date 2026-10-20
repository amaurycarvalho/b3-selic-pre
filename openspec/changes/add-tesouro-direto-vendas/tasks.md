## 0. Spike de descoberta (concluído)

> Evidências completas em `docs/rfcs/RFC-001 - Vendas do Tesouro Direto.md`, seção 12.

- [x] 0.1 Consultar o CKAN (`package_show`) e registrar o endpoint real, o identificador/nome do dataset, os metadados e as URLs dos recursos.
- [x] 0.2 Baixar uma amostra do CSV e registrar tamanho, encoding, BOM, delimitador, cabeçalho e primeiras linhas.
- [x] 0.3 Verificar se o dataset contém apenas vendas ou também resgates/saldo; decidir o nome final do modelo (`VendaTesouroDireto`) e os campos/tipos definitivos.
- [x] 0.4 Verificar `ETag`, `Last-Modified`, resposta `304`, periodicidade de atualização e defasagem real dos dados.
- [x] 0.5 Incorporar o schema verificado em `proposal.md`, `design.md`, `specs/` e `tasks.md`.

> Resgates e estoque foram confirmados como datasets separados e ficam fora desta change. A change `add-tesouro-direto-resgates-estoque` reutilizará cliente, cache, CLI e GUI.

## 1. Núcleo de domínio e aplicação

- [ ] 1.1 Adicionar o frozen dataclass `VendaTesouroDireto` em `src/b3_selic_pre/domain/models.py`, com `tipo_titulo`, `vencimento`, `data_liquidacao`, `pu`, `quantidade` e `valor`; usar `Decimal` nos três valores e strings ISO nas datas.
- [ ] 1.2 Adicionar `TESOURO_CKAN_BASE_URL` e `TESOURO_DATASET_NAME` em `src/b3_selic_pre/domain/constants.py`; manter `TESOURO_CACHE_TTL_MINUTES` na infraestrutura do cache.
- [ ] 1.3 Criar `src/b3_selic_pre/application/tesouro/__init__.py` com a API pública de processamento, filtros, agregação, ordenação e formatação; adicionar `TesouroDataError` e o erro de validação de período.
- [ ] 1.4 Implementar `src/b3_selic_pre/application/tesouro/_processamento.py` recebendo os bytes baixados, sem I/O de arquivo/rede: decodificação `utf-8-sig`/`utf-8`/`latin-1`, delimitador `;`, cabeçalho confirmado, datas `DD/MM/YYYY` para ISO, decimais com vírgula para `Decimal`, erros com linha/coluna, preservação de duplicatas, filtros, agregação com `PU` ponderado e ordenação determinística.
- [ ] 1.5 Implementar `src/b3_selic_pre/application/tesouro/_formatting.py` reutilizando os padrões de `src/b3_selic_pre/application/formatting.py`; a aplicação devolve texto/dict e a presentation serializa JSON. CSV de vendas, CSV agregado e payload JSON devem seguir o schema aprovado.
- [ ] 1.6 Criar `src/b3_selic_pre/presentation/tesouro_view_model.py` (headless) para linhas, filtros, período padrão de 12 meses, limite de 5.000 linhas, estado de controles e mensagens de status.
- [ ] 1.7 Adicionar testes headless de processamento, filtros, agregação, ordenação e formatação.

## 2. Infraestrutura

- [ ] 2.1 Implementar `src/b3_selic_pre/infrastructure/tesouro_client.py` para descoberta CKAN, validação de `success`, extração do recurso CSV, download em chunks com timeout de 60 s, retry transitório e cabeçalhos condicionais.
- [ ] 2.2 Tratar `ETag`/`If-Modified-Since` e `304 Not Modified`, atualizando `checked_at`; validar corpo parcial por `Content-Range`; mapear falhas de rede/HTTP/corpo vazio ou não-CSV para `CommunicationError`.
- [ ] 2.3 Implementar `src/b3_selic_pre/infrastructure/tesouro_cache.py` com caminho XDG (`cache_base() / "b3-selic-pre" / "tesouro"`), CSV cumulativo + `metadata.json`, TTL de 6 h, escrita atômica em bytes, tratamento de cache corrompido e leitura somente leitura.
- [ ] 2.4 Implementar `src/b3_selic_pre/infrastructure/tesouro_cached_client.py` com `TesouroDiretoClient`, `force` e caminho de leitura somente leitura.
- [ ] 2.5 Integrar `ActionLock` com caminho dedicado `.../tesouro.lock` no composition root, se CLI e GUI puderem disparar downloads concorrentes.
- [ ] 2.6 Adicionar testes de cliente e cache com `FakeResponse`/`opener`, incluindo 304, retry transitório, corpo parcial, cache corrompido e preservação da versão anterior.
- [ ] 2.7 Adicionar `write_atomic_bytes` em `cache_payload.py` (ou generalizar `write_atomic` para bytes) e cobrir com teste.
- [ ] 2.8 Adicionar retry transitório para rede/5xx/429/corpo parcial em `b3_retry.py` (ou helper próprio), com backoff/jitter e testes.

## 3. CLI

- [ ] 3.1 Adicionar `tesouro` aos subcomandos em `src/b3_selic_pre/presentation/cli_parser.py`, com `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json` e `--no-cache`.
- [ ] 3.2 Implementar o handler em `src/b3_selic_pre/presentation/cli_commands.py`, com validação de datas ISO exata (sem `nearest_business_day`), período padrão de 30 dias até a maior data disponível, `inicio <= fim`, códigos `0`/`1`/`2`, `TesouroDataError` e `CommunicationError`.
- [ ] 3.3 Despachar o subcomando em `src/b3_selic_pre/presentation/cli.py` e montar o cliente no composition root.
- [ ] 3.4 Cobrir o subcomando com testes headless: filtros, período padrão, período invertido, CSV, CSV agregado, JSON, `--no-cache`, erros, resultado vazio e códigos de saída.
- [ ] 3.5 Atualizar `docs/misc/cli.md` e `README.md` após a implementação.

## 4. GUI

- [ ] 4.1 Adicionar o botão "Tesouro Direto" na barra superior em `src/b3_selic_pre/presentation/gui/app.py`, com ícone, tooltip e inclusão em `_lockable_widgets` para respeitar o escudo de inicialização.
- [ ] 4.2 Implementar `src/b3_selic_pre/presentation/gui/tesouro.py` com janela `Toplevel` única, Treeview, filtros de título/período, período padrão de 12 meses, limite de 5.000 linhas, carregamento inicial do cache, botão de atualização, opção de ignorar cache, progresso indeterminado e status.
- [ ] 4.3 Injetar o cliente em `src/b3_selic_pre/presentation/gui/dependencies.py` e `src/b3_selic_pre/presentation/gui/launch.py`.
- [ ] 4.4 Executar download e parsing em thread e atualizar a UI via `root.after`, sem bloquear a janela principal; tratar fechamento da janela durante a carga.
- [ ] 4.5 Testar o view-model headless e manter testes de UI apenas para montagem/wiring, marcados `@pytest.mark.ui`, sem aumentar o orçamento de 5.
- [ ] 4.6 Atualizar a documentação da GUI no `README.md` após a implementação.
- [ ] 4.7 Implementar o limite de 5.000 linhas e a mensagem "mostrando X de Y; refine os filtros" no view-model e na janela.

## 5. Documentação

- [x] 5.1 Revisar o RFC-001 após o spike e incorporar o schema verificado.
- [ ] 5.2 Revisar a consistência entre RFC, specs, `docs/misc/cli.md` e `README.md` após a implementação.
- [ ] 5.3 Atualizar o PRD somente após a implementação e a aprovação final.
- [ ] 5.4 Revisar a entrada do CHANGELOG após a implementação.
- [ ] 5.5 Atualizar `docs/misc/datasources.md` para incluir o Tesouro Transparente, o CKAN, o CSV, os cabeçalhos, o retry, o cache e a classificação de erros.

## 6. Testes e validação

- [ ] 6.1 Testar imutabilidade, campos, tipos `Decimal` e semântica de `data_liquidacao` do modelo de domínio.
- [ ] 6.2 Testar o cliente CKAN/CSV com respostas simuladas, incluindo erros, retry, 304 e corpo parcial.
- [ ] 6.3 Testar o cache: hit, miss, TTL, corrupção, escrita atômica em bytes, `checked_at` em 304 e leitura somente leitura.
- [ ] 6.4 Testar parsing: encoding, delimitador, colunas ausentes/desconhecidas, datas e valores inválidos, duplicatas, filtros, agregação, `PU` ponderado e ordenação.
- [ ] 6.5 Testar formatação CSV/JSON, incluindo versão agregada e período vazio.
- [ ] 6.6 Rodar `make lint`, `make complexity` e `make test`; registrar a justificativa da suíte completa.
- [ ] 6.7 Registrar um teste manual opcional da CLI e da janela da GUI.
- [ ] 6.8 Registrar na change `add-tesouro-direto-resgates-estoque` o escopo de resgates e estoque, reutilizando a infraestrutura desta feature.
