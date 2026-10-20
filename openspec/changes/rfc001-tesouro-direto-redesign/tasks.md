## 0. Pré-requisito bloqueante — spike de descoberta

> Nenhuma tarefa das seções 1–6 pode ser iniciada antes da conclusão da tarefa 0.5.

- [ ] 0.1 Consultar o CKAN (`package_show`) e registrar o endpoint real, o identificador/nome do dataset, os metadados e as URLs dos recursos.
- [ ] 0.2 Baixar uma amostra do CSV e registrar tamanho, encoding, BOM, delimitador, cabeçalho e primeiras linhas.
- [ ] 0.3 Verificar se o dataset contém apenas vendas ou também resgates/saldo; decidir o nome final do modelo (`VendaTesouroDireto` ou `RegistroTesouroDireto`) e os campos/tipos definitivos.
- [ ] 0.4 Verificar `ETag`, `Last-Modified`, resposta `304`, periodicidade de atualização e defasagem real dos dados.
- [ ] 0.5 Incorporar o schema verificado em `proposal.md`, `design.md`, `specs/` e `tasks.md`; somente depois iniciar a implementação.

> A versão preliminar do RFC-001 e a entrada do CHANGELOG já foram atualizadas nesta reestruturação. Ambas devem ser revisadas novamente após o spike.

## 1. Núcleo de domínio e aplicação

- [ ] 1.1 Adicionar o frozen dataclass provisório em `src/b3_selic_pre/domain/models.py`, com os campos confirmados pelo spike.
- [ ] 1.2 Adicionar `TESOURO_BASE_URL` e `TESOURO_DATASET_ID` em `src/b3_selic_pre/domain/constants.py`; manter `TESOURO_CACHE_TTL_MINUTES` na infraestrutura do cache.
- [ ] 1.3 Criar `src/b3_selic_pre/application/tesouro/__init__.py` com a API pública de processamento, filtros e agregação.
- [ ] 1.4 Implementar `src/b3_selic_pre/application/tesouro/_processamento.py` recebendo os bytes baixados, sem I/O de arquivo/rede: fallback de encoding, validação de delimitador/colunas, mapeamento de nomes sem distinção de caixa/acentos, conversão de tipos, erros com linha/coluna, filtros e agregação.
- [ ] 1.5 Implementar `src/b3_selic_pre/application/tesouro/_formatting.py` reutilizando os helpers de `src/b3_selic_pre/application/formatting.py`; a aplicação devolve texto/dict e a presentation serializa JSON.
- [ ] 1.6 Criar `src/b3_selic_pre/presentation/tesouro_view_model.py` (headless) para linhas, filtros, estado de controles e mensagens de status.
- [ ] 1.7 Adicionar testes headless de processamento, filtros, agregação e formatação.

## 2. Infraestrutura

- [ ] 2.1 Implementar `src/b3_selic_pre/infrastructure/tesouro_client.py` para descoberta CKAN, extração da URL do CSV, download em chunks com timeout, retry e cabeçalhos condicionais.
- [ ] 2.2 Tratar `ETag`/`If-Modified-Since` e `304 Not Modified`, preservando o cache válido; mapear falhas de rede/HTTP/corpo vazio para `CommunicationError`.
- [ ] 2.3 Implementar `src/b3_selic_pre/infrastructure/tesouro_cache.py` com caminho XDG (`cache_base() / "b3-selic-pre" / "tesouro"`), CSV cumulativo + metadados, TTL de 6h, escrita atômica via `cache_payload.write_atomic`, tratamento de cache corrompido e leitura somente leitura.
- [ ] 2.4 Implementar `src/b3_selic_pre/infrastructure/tesouro_cached_client.py` com `TesouroDiretoClient`, `force` e caminho de leitura somente leitura.
- [ ] 2.5 Integrar `ActionLock` no composition root se CLI e GUI puderem disparar downloads concorrentes.
- [ ] 2.6 Adicionar testes de cliente e cache com `FakeResponse`/`opener`, incluindo 304, cache corrompido e preservação da versão anterior.

## 3. CLI

- [ ] 3.1 Adicionar `tesouro` aos subcomandos em `src/b3_selic_pre/presentation/cli_parser.py`, com `--titulo`, `--inicio`, `--fim`, `--json` e `--no-cache`.
- [ ] 3.2 Implementar o handler em `src/b3_selic_pre/presentation/cli_commands.py`, reutilizando as regras de data da aplicação e os códigos `0`/`1`/`2`.
- [ ] 3.3 Despachar o subcomando em `src/b3_selic_pre/presentation/cli.py` e montar o cliente no composition root.
- [ ] 3.4 Cobrir o subcomando com testes headless: filtros, CSV, JSON, `--no-cache`, erros e códigos de saída.
- [ ] 3.5 Atualizar `docs/misc/cli.md` e `README.md`.

## 4. GUI

- [ ] 4.1 Adicionar o botão "Tesouro Direto" na barra superior em `src/b3_selic_pre/presentation/gui/app.py`, com ícone, tooltip e respeito ao escudo de inicialização.
- [ ] 4.2 Implementar `src/b3_selic_pre/presentation/gui/tesouro.py` com janela `Toplevel`, Treeview, filtros de título/período, botão de atualização, opção de ignorar cache, progresso e status.
- [ ] 4.3 Injetar o cliente em `src/b3_selic_pre/presentation/gui/dependencies.py` e `src/b3_selic_pre/presentation/gui/launch.py`.
- [ ] 4.4 Executar o download em thread e atualizar a UI via `root.after`, sem bloquear a janela principal.
- [ ] 4.5 Testar o view-model headless e manter testes de UI apenas para montagem/wiring, marcados `@pytest.mark.ui`, respeitando o orçamento de 5.
- [ ] 4.6 Atualizar a documentação da GUI no `README.md`, se necessário.

## 5. Documentação

- [ ] 5.1 Revisar o RFC-001 após o spike e incorporar o schema verificado.
- [ ] 5.2 Atualizar a documentação da CLI e do README.
- [ ] 5.3 Atualizar o PRD somente após o spike e a aprovação de implementação.
- [ ] 5.4 Revisar a entrada do CHANGELOG após o spike.

## 6. Testes e validação

- [ ] 6.1 Testar imutabilidade e campos do modelo de domínio.
- [ ] 6.2 Testar o cliente CKAN/CSV com respostas simuladas, incluindo erros e 304.
- [ ] 6.3 Testar o cache: hit, miss, TTL, corrupção, escrita atômica e leitura somente leitura.
- [ ] 6.4 Testar parsing: encoding, delimitador, colunas ausentes/desconhecidas, valores inválidos, filtros e agregação.
- [ ] 6.5 Testar formatação CSV/JSON.
- [ ] 6.6 Rodar `make lint`, `make complexity` e `make test`; registrar a justificativa da suíte completa.
- [ ] 6.7 Registrar um teste manual opcional da CLI e da janela da GUI.
