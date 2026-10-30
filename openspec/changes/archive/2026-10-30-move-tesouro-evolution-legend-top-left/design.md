# Design

## Context

See `proposal.md` - Why. Os gráficos temporais do Tesouro Direto usam `render_evolution` (empilhamento de `Estoque` e `Apetite do mercado`) e `render_gap` (linhas da `Visão geral`). Ambos definem a legenda com `loc="upper right"`. Os gráficos de percentual atual usam renderizadores separados e não fazem parte deste escopo.

## Goals / Non-Goals

**Goals:**

- Posicionar a legenda dos dois renderizadores temporais no canto superior esquerdo.
- Manter o comportamento dos gráficos de percentual atual.
- Cobrir a posição da legenda com testes headless.

**Non-Goals:**

- Alterar cores, ordem, conteúdo ou número de colunas da legenda.
- Alterar a legenda dos gráficos da aba `SELIC Pré`.
- Mudar dados, layout ou textos orientativos das sub-abas.

## Decisions

### 1. Alterar apenas os renderizadores temporais

**Decisão:** trocar `loc="upper right"` por `loc="upper left"` em `render_evolution` e em `render_gap`, mantendo `render_current_share` e `render_current_comparison` como estão.

**Racional:** o segundo gráfico de cada sub-aba é o temporal; o primeiro é o percentual atual. A mudança fica restrita ao comportamento pedido.

**Alternativa considerada:** criar um parâmetro de posição no view-model. Seria mais flexível, mas adiciona configuração sem necessidade para um requisito fixo.

### 2. Verificação pela localização efetiva da legenda

**Decisão:** nos testes de `charts_tesouro`, afirmar que a legenda dos gráficos temporais está em `upper left` (comparando `_loc` com o código do matplotlib) e que os gráficos atuais permanecem em `upper right`.

**Racional:** a verificação é headless e confirma o efeito visual sem depender de display.

## Risks / Trade-offs

- **[Legenda sobre os primeiros pontos]** -> o canto superior esquerdo pode cobrir o início da série; é o trade-off aceito para liberar o fim da série, onde estão os dados mais recentes.
- **[Legenda larga em muitas famílias]** -> `render_evolution` mantém `ncol` proporcional ao número de famílias; se necessário, a legenda pode ocupar mais largura no topo, sem mudar a posição.
- **[Dependência de atributo interno do matplotlib]** -> o teste usa `_loc`; se a versão do matplotlib mudar, ajustar para a API equivalente. A implementação em si usa a API pública `loc`.

## Migration Plan

1. Alterar os dois `loc` e rodar os testes de gráficos.
2. Rollback: reverter os dois `loc` para `upper right`; nenhum dado ou cache é afetado.

## Open Questions

Nenhuma pendente.
