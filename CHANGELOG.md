# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [add-tesouro-direto-vendas](openspec/changes/add-tesouro-direto-vendas/) Adicionar a consulta de vendas do Tesouro Direto à CLI e à GUI, com schema confirmado e cache cumulativo

#### Added

- Adicionar o subcomando `tesouro`, com filtros por título/período, agregação por título, saída CSV/JSON e exportação via `--saida`.
- Adicionar o modelo `VendaTesouroDireto` e o processamento headless de parsing, filtros, agregação e formatação.
- Adicionar descoberta CKAN, download condicional (`ETag`/`Last-Modified`/`304`), retry transitório e validação de corpo parcial.
- Adicionar cache cumulativo atômico em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`, com TTL de 1 h para dado corrente e 6 h para histórico.
- Adicionar a tool MCP somente leitura `tesouro_vendas`, com filtros, agregação, paginação e erro `cache_vazio`.
- Atualizar a documentação da CLI, do MCP, das fontes de dados, o README, o PRD e o RFC-001.

### [add-tesouro-direto-resgates-estoque](openspec/changes/add-tesouro-direto-resgates-estoque/) Adicionar a consulta de resgates (recompras, cupom e vencimentos) e do estoque mensal do Tesouro Direto à CLI e à GUI

## [1.0.1] - 2026-10-24

### [increase-b3-resilience](openspec/changes/archive/2026-10-24-increase-b3-resilience/) O acesso atual à B3 já repete respostas vazias, mas não repete timeouts nem falhas transientes de rede. Um timeout no `GetList` interrompe a consulta imediatamente e um timeout no `GetDownloadFile` nem sequer aciona o fallback para `GetList`, porque o fallback só captura `CommunicationError`. Além disso, o timeout de 30 s está duplicado em vários módulos e o TTL de 30 min para a data corrente força refetches frequentes.

#### Changed

- Centralizar o timeout padrão de acesso à B3 em **60 s**, usado por `GetList`, `GetDownloadFile` e pela seleção de fonte.
- Generalizar o retry para repetir também falhas transientes (`TimeoutError`, `URLError`, `ConnectionError`, `HTTPException`, `SSLError`, `socket.gaierror`), além dos resultados vazios já cobertos.
- Manter **6 tentativas** para resultados vazios e usar **3 tentativas** para falhas transientes, com o mesmo backoff exponencial com jitter, limitando o pior caso por página a aproximadamente 3 minutos.
- Preservar a regra de que erros de dados (JSON/CSV inválido ou esquema inesperado) não são repetidos.
- Garantir que uma falha transiente do `GetDownloadFile` em data passada permita o fallback para `GetList`, como já ocorre com resposta vazia.
- Alterar o TTL padrão da data corrente de **30 min** para **6 h (360 min)**.
- Atualizar testes, specs e documentação afetada.

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v1.0.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
