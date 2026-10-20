## Why

O RFC-001 (Movimentações do Tesouro Direto) propõe uma feature futura para extrair dados de vendas de títulos públicos do portal Tesouro Transparente. A proposta original viola a Clean Architecture do projeto (ADR-001), introduz dependências externas não aprovadas (`requests`, `beautifulsoup4`, `pandas`) e não segue os padrões atuais de cache, logging, CLI e GUI.

Desde a criação desta change, a aplicação evoluiu: a CLI passou a usar subcomandos de verbo, a GUI ganhou escudo de inicialização e orçamento de testes de UI, o cache passou a exigir escrita atômica e validação de completude, e as falhas de comunicação passaram a usar o contrato `CommunicationError`. A change precisa ser reestruturada para refletir esse estado.

Além disso, o schema real do CSV do Tesouro Transparente nunca foi verificado neste repositório. O próprio RFC reconhece que a estrutura das colunas deve ser confirmada após o download. Por isso, esta change é uma **versão preliminar**: a implementação só pode começar depois de um spike obrigatório de descoberta do dataset e do schema real.

## Prerequisite (blocking)

Esta change NÃO SHALL ser aplicada antes da conclusão de um spike de descoberta que confirme:

- o identificador e a URL reais do dataset no CKAN do Tesouro Transparente;
- o schema real do CSV (colunas, nomes exatos, acentos, tipos e obrigatoriedade);
- se o dataset contém apenas vendas ou também resgates/saldo;
- encoding, delimitador, BOM, tamanho, periodicidade e defasagem;
- suporte a `ETag`, `Last-Modified` e `304 Not Modified`.

O spike complementa e revisa os artefatos desta change. Nenhuma tarefa de implementação pode começar antes de o schema verificado ser incorporado ao `proposal.md`, `design.md`, `specs/` e `tasks.md`.

## What Changes

- Adicionar o subcomando `b3-selic-pre tesouro`, com filtros por título e período, saída CSV por padrão e `--json` opcional, reaproveitando as regras de data e os códigos de saída da CLI.
- Adicionar uma janela separada "Tesouro Direto" na GUI, aberta por um botão na barra superior, com tabela, filtros, estados de carregamento/erro e indicador de cache.
- Adicionar a capability `tesouro-direto` para descoberta CKAN, download do CSV, cache cumulativo, parsing, validação, filtros, agregação e formatação.
- Adicionar a capability `tesouro-direto-gui` para o botão, a janela separada e o view-model headless.
- Modificar a capability `cli-interface` para incluir o subcomando `tesouro`.
- Reutilizar `urllib`, `csv`, `json`, `CommunicationError`, `b3_retry`, `cache_payload.write_atomic`, `xdg.cache_base`, `application/formatting.py` e `ActionLock`.
- Atualizar o RFC-001 e a documentação da CLI.
- **Non-goals**: tools MCP para Tesouro; exportação Tesouro no subcomando `exportar`; gráficos; banco de dados; agendamento; atualização do PRD antes do spike; alteração das specs principais sem arquivamento.

## Capabilities

### New Capabilities

- `tesouro-direto`: descoberta do dataset via CKAN JSON, download e cache do CSV cumulativo, parsing/validação, modelo provisório, filtros, agregação, formatação e classificação de erros.
- `tesouro-direto-gui`: botão na barra superior, janela separada, tabela, filtros, estados de carregamento/erro/cache e view-model headless.

### Modified Capabilities

- `cli-interface`: novo subcomando `tesouro`, seus parâmetros, formatos de saída e códigos de retorno.

## Impact

- Novos módulos em `src/b3_selic_pre/domain/`, `application/tesouro/`, `infrastructure/` e `presentation/`.
- Alterações em `presentation/cli_parser.py`, `presentation/cli_commands.py`, `presentation/gui/`, `presentation/gui/launch.py` e `presentation/gui/dependencies.py`.
- Nenhuma dependência externa nova; uso de `urllib`, `csv` e `json` da biblioteca padrão.
- Atualização de `docs/rfcs/RFC-001 - Movimentações do Tesouro Direto.md`, `docs/misc/cli.md` e `README.md`.
- Testes headless para cliente, cache, parsing, filtros, agregação e formatação; testes de UI apenas para montagem/wiring, respeitando o orçamento atual.
- A suíte completa é justificada por envolver `domain`, CLI, GUI, cache e contratos compartilhados.
- O PRD permanece inalterado até o spike e a aprovação de implementação.
