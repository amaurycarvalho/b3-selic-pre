## Why

A change `add-tesouro-direto-vendas` adiciona a consulta de vendas do Tesouro Direto, mas o portal Tesouro Transparente publica resgates e estoque em datasets separados. Usuários que acompanham o programa precisam consultar também:

- recompras antecipadas;
- vencimentos;
- pagamentos de cupom de juros;
- estoque mensal por título.

O spike complementar confirmou os schemas, volumes e armadilhas desses datasets. Esta change adiciona essa consulta à CLI, reutilizando a infraestrutura de cliente, cache e erros criada pela feature de vendas.

Esta change depende de `add-tesouro-direto-vendas` e deve ser aplicada depois dela.

## What Changes

- Adicionar os subcomandos `tesouro-resgates` e `tesouro-estoque` à CLI, com exportação para arquivo ou diretório via `--saida`.
- Adicionar as capabilities `tesouro-resgates` e `tesouro-estoque`.
- Adicionar as tools MCP somente leitura `tesouro_resgates` e `tesouro_estoque`, que consultam apenas o cache local e suportam filtros, agregação e paginação.
- Modificar a capability `mcp-tools` para incluir as duas tools no catálogo somente leitura.
- Generalizar a descoberta CKAN e o cache para múltiplos recursos:
  - resgates: `Recompras`, `Pagamento de Cupom de Juros` e `Vencimentos`;
  - estoque: um CSV mensal.
- Aplicar TTL condicional por recurso: 1 hora quando o recurso contém o dia corrente/último dia útil, 6 horas para histórico e 24 horas para estoque, cupom e vencimentos.
- Adicionar os modelos `ResgateTesouroDireto` e `EstoqueTesouroDireto`.
- Implementar parsing específico por recurso:
  - recompras: 5 colunas, sem `PU`;
  - cupom e vencimentos: 6 colunas, com `PU`;
  - estoque: 6 colunas, com `Mes Estoque` (`MM/YYYY`) e `Valor Estoque`.
- Adicionar filtros, agregação e formatação por dataset.
- Adicionar defaults específicos:
  - resgates: últimos 30 dias na CLI;
  - estoque: último mês na CLI, com seleção de mês.
- Adicionar testes headless e atualizar a documentação.
- **Non-goals**: vendas (change separada); GUI e análise percentual (changes `add-tesouro-gui` e `add-tesouro-analise-percentuais`); investidores; operações; taxas dos títulos; exportação no `exportar` (a exportação é via `--saida`); gráficos; banco de dados; agendamento; cruzamento com a SELIC.

## Capabilities

### New Capabilities

- `tesouro-resgates`: descoberta dos recursos de resgates, download/cache por recurso, parsing, modelo, filtros, agregação, ordenação e formatação.
- `tesouro-estoque`: descoberta do recurso de estoque, download/cache, parsing mensal, modelo, filtros, comparação de meses e formatação.

### Modified Capabilities

- `cli-interface`: novos subcomandos `tesouro-resgates` e `tesouro-estoque`, com parâmetros, formatos de saída, `--saida` e códigos de retorno.
- `mcp-tools`: novas tools `tesouro_resgates` e `tesouro_estoque` e atualização do catálogo somente leitura.

## Impact

- Novos modelos em `src/b3_selic_pre/domain/models.py`.
- Generalização de `application/tesouro/` e `infrastructure/tesouro_client.py`, `tesouro_cache.py` e `tesouro_cached_client.py` para um registro de recursos.
- Alterações em `presentation/cli_parser.py`, `presentation/cli_commands.py`, `presentation/cli.py` e `presentation/mcp/`.
- Novos arquivos de cache por recurso em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`.
- Atualização de `docs/misc/cli.md`, `docs/misc/mcp.md`, `docs/misc/datasources.md`, `README.md` e `CHANGELOG.md`.
- Testes headless para descoberta, parsing, cache, filtros, agregação, formatação, exportação e tools MCP; sem testes de UI nesta change.
- A suíte completa é justificada por envolver `domain`, CLI, MCP, cache e contratos compartilhados.
- GUI e análise percentual ficam para `add-tesouro-gui` e `add-tesouro-analise-percentuais`.
- Dependência: `add-tesouro-direto-vendas` deve ser implementada/arquivada antes desta change.
