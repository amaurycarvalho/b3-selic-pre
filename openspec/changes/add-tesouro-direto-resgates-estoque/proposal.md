## Why

A change `add-tesouro-direto-vendas` adiciona a consulta de vendas do Tesouro Direto, mas o portal Tesouro Transparente publica resgates e estoque em datasets separados. Usuários que acompanham o programa precisam consultar também:

- recompras antecipadas;
- vencimentos;
- pagamentos de cupom de juros;
- estoque mensal por título.

O spike complementar confirmou os schemas, volumes e armadilhas desses datasets. Esta change adiciona essa consulta à CLI e à GUI, reutilizando a infraestrutura de cliente, cache, erros e view-model criada pela feature de vendas.

Esta change depende de `add-tesouro-direto-vendas` e deve ser aplicada depois dela.

## What Changes

- Adicionar os subcomandos `tesouro-resgates` e `tesouro-estoque` à CLI.
- Adicionar abas "Resgates" e "Estoque" à janela "Tesouro Direto" da GUI.
- Adicionar as capabilities `tesouro-resgates`, `tesouro-estoque` e `tesouro-resgates-estoque-gui`.
- Generalizar a descoberta CKAN e o cache para múltiplos recursos:
  - resgates: `Recompras`, `Pagamento de Cupom de Juros` e `Vencimentos`;
  - estoque: um CSV mensal.
- Adicionar os modelos `ResgateTesouroDireto` e `EstoqueTesouroDireto`.
- Implementar parsing específico por recurso:
  - recompras: 5 colunas, sem `PU`;
  - cupom e vencimentos: 6 colunas, com `PU`;
  - estoque: 6 colunas, com `Mes Estoque` (`MM/YYYY`) e `Valor Estoque`.
- Adicionar filtros, agregação e formatação por dataset.
- Adicionar defaults específicos:
  - resgates: últimos 30 dias na CLI e 12 meses na GUI;
  - estoque: último mês na CLI e 12 meses na GUI, com seleção de mês.
- Adicionar testes headless e atualizar a documentação.
- **Non-goals**: vendas (change separada); investidores; operações; taxas dos títulos; tools MCP; exportação no `exportar`; gráficos; banco de dados; agendamento; cruzamento com a SELIC.

## Capabilities

### New Capabilities

- `tesouro-resgates`: descoberta dos recursos de resgates, download/cache por recurso, parsing, modelo, filtros, agregação, ordenação e formatação.
- `tesouro-estoque`: descoberta do recurso de estoque, download/cache, parsing mensal, modelo, filtros, comparação de meses e formatação.
- `tesouro-resgates-estoque-gui`: abas de Resgates e Estoque na janela Tesouro Direto, com filtros, limites, atualização e status próprios.

### Modified Capabilities

- `cli-interface`: novos subcomandos `tesouro-resgates` e `tesouro-estoque`, com parâmetros, formatos de saída e códigos de retorno.

## Impact

- Novos modelos em `src/b3_selic_pre/domain/models.py`.
- Generalização de `application/tesouro/` e `infrastructure/tesouro_client.py`, `tesouro_cache.py` e `tesouro_cached_client.py` para um registro de recursos.
- Alterações em `presentation/cli_parser.py`, `presentation/cli_commands.py`, `presentation/cli.py` e `presentation/gui/tesouro.py`.
- Novos arquivos de cache por recurso em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`.
- Atualização de `docs/misc/cli.md`, `docs/misc/datasources.md`, `README.md` e `CHANGELOG.md`.
- Testes headless para descoberta, parsing, cache, filtros, agregação e formatação; testes de UI apenas para montagem/wiring, sem aumentar o orçamento de 5.
- A suíte completa é justificada por envolver `domain`, CLI, GUI, cache e contratos compartilhados.
- Dependência: `add-tesouro-direto-vendas` deve ser implementada/arquivada antes desta change.
