## Why

A tabela bruta de taxas SELIC Pré mostra um registro por dia útil, o que pode ser difícil de analisar visualmente para períodos longos (centenas de linhas). Consolidar por ano (agrupando por `day360 // 365`) permite enxergar rapidamente a taxa mínima e máxima de cada ano, tanto na interface gráfica quanto no terminal.

## What Changes

- **GUI**: Adicionar checkbox "Consolidar por ano" que alterna a visualização da tabela entre registros individuais e linhas consolidadas por ano (ANO, MENOR TAXA, MAIOR TAXA)
- **CLI**: Adicionar flag `--yearly` ao `argparse` que, quando presente, imprime a tabela consolidada por ano em vez dos registros individuais
- **Export/Copy**: "Copiar tabela" e "Exportar CSV" refletem a visualização atual (raw ou consolidada)
- **Núcleo**: Criar função `consolidate_by_year(records)` que agrupa registros por `day360 // 365` e retorna ano, taxa mínima e taxa máxima

## Capabilities

### New Capabilities
- `yearly-consolidation`: Agrupamento anual de taxas SELIC Pré, com visualização consolidada na GUI e no CLI

### Modified Capabilities
- `desktop-rate-browser`: Adicionar modo de visualização consolidada por ano, alternável via checkbox na interface

## Impact

- `b3_selic_pre.py`: Adicionar função `consolidate_by_year`, modificar `format_cli_rows`, modificar `SelicPreApp` (checkbox, renderização condicional, export/copy condicional)
- `tests/test_b3_selic_pre.py`: Adicionar testes para `consolidate_by_year` e formato CLI consolidado
- `tests/test_b3_selic_pre_gui.py`: Adicionar testes para o checkbox e alternância de view
