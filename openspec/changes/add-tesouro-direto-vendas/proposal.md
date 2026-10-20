## Why

O RFC-001 propõe extrair dados de vendas de títulos públicos do portal Tesouro Transparente. A proposta original violava a Clean Architecture do projeto (ADR-001), introduzia dependências externas não aprovadas (`requests`, `beautifulsoup4`, `pandas`) e não seguia os padrões atuais de cache, logging, CLI e GUI.

Desde a criação desta change, a aplicação evoluiu: a CLI passou a usar subcomandos de verbo, a GUI ganhou escudo de inicialização e orçamento de testes de UI, o cache passou a exigir escrita atômica e validação de completude, e as falhas de comunicação passaram a usar o contrato `CommunicationError`. A change foi reestruturada para refletir esse estado.

O spike de descoberta foi concluído em 2026-10-20 e confirmou que o dataset `vendas-do-tesouro-direto` contém **apenas vendas**, com seis colunas, delimitador `;`, decimal com vírgula, datas `DD/MM/YYYY` e suporte real a `ETag`/`Last-Modified`/`304`. O modelo provisório original (`venda`, `resgate`, `saldo`) não existe nesse dataset e foi substituído pelo schema verificado.

## Spike (concluído)

O spike respondeu:

- dataset real: `vendas-do-tesouro-direto` (UUID `f0468ecc-ae97-4287-89c2-6d8139fb4343`);
- recurso CSV: `e5f90e3a-8f8d-4895-9c56-4bb2f7877920`, 7.488.603 bytes;
- colunas: `Tipo Titulo`, `Vencimento do Titulo`, `Data de Liquidacao da Venda`, `PU`, `Quantidade`, `Valor`;
- encoding ASCII/UTF-8 sem BOM; delimitador `;`; decimal vírgula; datas `DD/MM/YYYY`; quebra LF;
- somente vendas; resgates e estoque são datasets separados e ficam fora desta change;
- `ETag`, `Last-Modified` e `304 Not Modified` funcionam;
- periodicidade diária, com defasagem de até dois dias úteis e revisões possíveis;
- 101.331 registros, 6.129 datas distintas e 9 títulos.

As evidências completas estão no `docs/rfcs/RFC-001 - Vendas do Tesouro Direto.md`.

## What Changes

- Adicionar o subcomando `b3-selic-pre tesouro`, com filtros por título e período de liquidação, saída CSV por padrão, `--json`, `--agregar` e `--no-cache`.
- Adicionar uma janela separada "Tesouro Direto" na GUI, aberta por um botão na barra superior, com tabela, filtros, período padrão de 12 meses, limite de 5.000 linhas, estados de carregamento/erro e indicador de cache.
- Adicionar a capability `tesouro-direto` para descoberta CKAN, download do CSV, cache cumulativo, parsing, validação, filtros, agregação, ordenação e formatação.
- Adicionar a capability `tesouro-direto-gui` para o botão, a janela separada e o view-model headless.
- Modificar a capability `cli-interface` para incluir o subcomando `tesouro`.
- Reutilizar `urllib`, `csv`, `json`, `decimal`, `CommunicationError`, `b3_retry`, `cache_payload.write_atomic` (ou variante em bytes), `xdg.cache_base`, `application/formatting.py` e `ActionLock`.
- Atualizar o RFC-001 renomeado, a documentação da CLI, o README, `datasources.md` e o CHANGELOG.
- **Non-goals**: resgates e estoque nesta change; investidores, operações e taxas; tools MCP para Tesouro; exportação Tesouro no subcomando `exportar`; gráficos; banco de dados; agendamento; atualização do PRD antes da implementação; alteração das specs principais sem arquivamento.

## Capabilities

### New Capabilities

- `tesouro-direto`: descoberta do dataset `vendas-do-tesouro-direto` via CKAN JSON, download e cache do CSV cumulativo, parsing/validação, modelo `VendaTesouroDireto`, filtros, agregação, ordenação, formatação e classificação de erros.
- `tesouro-direto-gui`: botão na barra superior, janela separada, tabela com limite de linhas, filtros, estados de carregamento/erro/cache e view-model headless.

### Modified Capabilities

- `cli-interface`: novo subcomando `tesouro`, seus parâmetros, formatos de saída, período padrão e códigos de retorno.

## Impact

- Novos módulos em `src/b3_selic_pre/domain/`, `application/tesouro/`, `infrastructure/` e `presentation/`.
- Alterações em `presentation/cli_parser.py`, `presentation/cli_commands.py`, `presentation/gui/`, `presentation/gui/launch.py` e `presentation/gui/dependencies.py`.
- Nenhuma dependência externa nova; uso de `urllib`, `csv`, `json`, `decimal`, `unicodedata` e `hashlib` da biblioteca padrão.
- Atualização de `docs/rfcs/RFC-001 - Vendas do Tesouro Direto.md`, `docs/misc/cli.md`, `docs/misc/datasources.md`, `README.md` e `CHANGELOG.md`.
- Testes headless para cliente, cache, parsing, filtros, agregação, ordenação e formatação; testes de UI apenas para montagem/wiring, respeitando o orçamento atual de 5.
- A suíte completa é justificada por envolver `domain`, CLI, GUI, cache e contratos compartilhados.
- O PRD permanece inalterado até a implementação e a aprovação final.
- Resgates e estoque serão tratados na change `add-tesouro-direto-resgates-estoque`, reutilizando a infraestrutura desta feature.
