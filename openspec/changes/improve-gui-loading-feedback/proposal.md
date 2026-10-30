# Proposal

## Why

A montagem e o desenho dos gráficos do Tesouro Direto levam tempo perceptível. Hoje, ao selecionar uma sub-aba ou acionar `Atualizar`, a janela pode parecer travada e o conteúdo parcial pode aparecer de forma estranha. O comportamento desejado é simples: o texto de aviso fica fixo atrás do gráfico, o gráfico fica invisível durante o processamento e só volta a aparecer quando a carga de dados e o desenho terminam. Além disso, o README e a aba Sobre ainda não apresentam um resumo único das funcionalidades.

## What Changes

- Adicionar um texto fixo `Processando as informações. Aguarde…` atrás dos gráficos do Tesouro Direto.
- Ao selecionar uma sub-aba, ocultar temporariamente os gráficos para que o texto fixo apareça; reexibi-los somente após a carga de dados e o desenho concluírem.
- Ao acionar `Atualizar`, ocultar os gráficos enquanto a atualização processa e reexibi-los somente após a carga de dados completar.
- Manter o ponteiro de espera `watch`, a statusbar e o progresso durante o processamento.
- Na troca de janela de análise, manter os gráficos visíveis e usar apenas o ponteiro de espera.
- Estabilizar a geometria para que ocultar/reexibir os gráficos e a barra de progresso não desloque o conteúdo.
- Adicionar ao início do `README.md` uma seção com o resumo das funcionalidades e replicar o mesmo texto na aba Sobre.
- Não alterar cache, clientes HTTP, payloads nem o orçamento de testes de UI.

## Capabilities

### New Capabilities

- `feature-summary`: resumo único das funcionalidades da aplicação, publicado no início do README e replicado na aba Sobre.

### Modified Capabilities

- `tesouro-analise-gui`: texto fixo atrás dos gráficos e ocultação/reexibição dos gráficos durante seleção de sub-aba e `Atualizar`, até a carga concluir.
- `cambio-ouro`: ponteiro de espera ao atualizar a sub-aba Dólar e Ouro.
- `reservas-cambiais`: ponteiro de espera ao atualizar a sub-aba Reservas Internacionais.

## Impact

- `presentation/gui/tesouro_sub_tab.py`, `presentation/gui/tesouro_sub_tab_ui.py` e `presentation/gui/tesouro_tab.py`.
- `presentation/busy.py` para o cursor de espera compartilhado.
- `presentation/gui/market_tab.py`, `presentation/gui/market_sub_tab_ui.py` e `presentation/gui/reserves_sub_tab.py`.
- `application/about.py`, `presentation/gui/about_tab.py` e `README.md`.
- Testes headless do helper de ocupação e de paridade do resumo; verificações Tk reais para visibilidade dos painéis e estabilidade de layout.
- Sem novas dependências, mudanças de contrato de dados, cache em disco ou empacotamento.
