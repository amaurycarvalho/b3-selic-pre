## Why

Nos gráficos temporais das sub-abas de `Tesouro Direto`, a legenda fica no canto superior direito, sobre o fim da série, que é justamente onde estão os dados mais recentes. Posicioná-la no início da série libera essa área e acompanha a direção de leitura do eixo do tempo.

## What Changes

- Mover a legenda dos gráficos temporais (evolução de `Estoque`/`Apetite do mercado` e gap da `Visão geral`) para o canto superior esquerdo.
- Manter inalterada a posição da legenda dos gráficos de percentual atual.
- Adicionar verificação de que os gráficos temporais usam a legenda no canto superior esquerdo.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova. -->

### Modified Capabilities

- `tesouro-analise-gui`: adicionar a posição da legenda dos gráficos temporais no canto superior esquerdo.

## Impact

- `src/b3_selic_pre/presentation/charts_tesouro.py`: posição da legenda em `render_evolution` e `render_gap`.
- `tests/test_charts_tesouro.py`: verificação da posição da legenda.
- Nenhuma alteração de dados, cache, CLI ou dependências.
