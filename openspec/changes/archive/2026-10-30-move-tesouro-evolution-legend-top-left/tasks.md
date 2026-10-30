# Tasks

## 1. Posição da legenda

- [x] 1.1 Alterar `render_evolution` e `render_gap` para posicionar a legenda em `upper left`; verificar que os dois renderizadores continuam desenhando sem erro.
- [x] 1.2 Adicionar testes em `tests/test_charts_tesouro.py` confirmando legenda `upper left` nos gráficos temporais e `upper right` nos gráficos de percentual atual; verificar que os testes passam.
- [x] 1.3 Rodar `make lint`, `make complexity` e os testes de gráficos do Tesouro; verificar saída sem erros.

## Workflow follow-up

- Teste manual opcional: abrir a GUI, acessar `Tesouro Direto` e conferir que o segundo gráfico (temporal) tem a legenda no canto superior esquerdo e o primeiro mantém a legenda no canto superior direito.
- Arquivar a change após a aprovação.
