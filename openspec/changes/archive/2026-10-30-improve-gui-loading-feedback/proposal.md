# Proposal

## Why

A montagem e o desenho dos gráficos do Tesouro Direto levam tempo perceptível. Hoje, ao selecionar uma sub-aba ou acionar `Atualizar`, a janela pode parecer travada e o conteúdo parcial pode aparecer de forma estranha. O comportamento desejado é simples: o texto de aviso fica fixo atrás do gráfico, o gráfico fica invisível durante o processamento e só volta a aparecer quando a carga de dados e o desenho terminam. Além disso, o README e a aba Sobre ainda não apresentam um resumo único das funcionalidades.

Os renderizadores de gráficos chamam `tight_layout` diretamente. Quando as margens não comportam títulos, legendas e rótulos, o matplotlib emite `UserWarning: Tight layout not applied` para o usuário e o evento não fica registrado no log da aplicação.

As sub-abas da aba de câmbio e reservas ainda não aplicam o mesmo padrão de feedback das sub-abas do Tesouro Direto: não exibem o texto fixo atrás do gráfico, não ocultam o gráfico durante a carga/atualização e não estabilizam a geometria da barra de progresso. A aba também aparece como `Câmbio e Ouro`, enquanto README e aba Sobre precisam refletir o novo nome `Câmbio e Reserva`.

## What Changes

- Adicionar um texto fixo `Processando as informações. Aguarde…` atrás dos gráficos do Tesouro Direto.
- Ao selecionar uma sub-aba, ocultar temporariamente os gráficos para que o texto fixo apareça; reexibi-los somente após a carga de dados e o desenho concluírem.
- Ao acionar `Atualizar`, ocultar os gráficos enquanto a atualização processa e reexibi-los somente após a carga de dados completar.
- Manter o ponteiro de espera `watch`, a statusbar e o progresso durante o processamento.
- Na troca de janela de análise, manter os gráficos visíveis e usar apenas o ponteiro de espera.
- Estabilizar a geometria para que ocultar/reexibir os gráficos e a barra de progresso não desloque o conteúdo.
- Adicionar ao início do `README.md` uma seção com o resumo das funcionalidades e replicar o mesmo texto na aba Sobre.
- Centralizar a aplicação de `tight_layout` em um helper que captura o aviso, registra-o no log com o contexto do gráfico e aplica margens conservadoras de fallback.
- Renomear a aba de nível superior de `Câmbio e Ouro` para `Câmbio e Reserva` no shell, no README e na aba Sobre.
- Aplicar às sub-abas `Dólar e Ouro` e `Reservas Internacionais` o mesmo texto fixo atrás do gráfico, ocultação durante a carga e reexibição após o desenho usados no Tesouro Direto.
- Estabilizar a geometria das sub-abas de câmbio e reservas com host fixo de progresso e rótulos de status estáveis.
- Não alterar cache, clientes HTTP, payloads nem o orçamento de testes de UI.

## Capabilities

### New Capabilities

- `feature-summary`: resumo único das funcionalidades da aplicação, publicado no início do README e replicado na aba Sobre.
- `chart-layout-hardening`: tratamento e registro dos avisos de layout não aplicável emitidos pelos gráficos.

### Modified Capabilities

- `tesouro-analise-gui`: texto fixo atrás dos gráficos e ocultação/reexibição dos gráficos durante seleção de sub-aba e `Atualizar`, até a carga concluir.
- `cambio-ouro`: ponteiro de espera, texto fixo e ocultação/reexibição do gráfico ao exibir e atualizar a sub-aba Dólar e Ouro.
- `reservas-cambiais`: ponteiro de espera, texto fixo e ocultação/reexibição do gráfico ao exibir e atualizar a sub-aba Reservas Internacionais.
- `app-tabs`: renomear a aba de nível superior para `Câmbio e Reserva`.

## Impact

- `presentation/gui/tesouro_sub_tab.py`, `presentation/gui/tesouro_sub_tab_ui.py` e `presentation/gui/tesouro_tab.py`.
- `presentation/busy.py` para o cursor de espera compartilhado.
- `presentation/gui/market_tab.py`, `presentation/gui/market_sub_tab_ui.py`, `presentation/gui/reserves_sub_tab.py` e `presentation/gui/shell.py`.
- `application/about.py`, `presentation/gui/about_tab.py` e `README.md`.
- `presentation/chart_layout.py` e os renderizadores `charts.py`, `charts_tesouro.py`, `charts_market.py` e `charts_reserves.py`.
- Testes headless do helper de ocupação, do helper de layout e de paridade do resumo; verificações Tk reais para visibilidade dos painéis e estabilidade de layout.
- Sem novas dependências, mudanças de contrato de dados, cache em disco ou empacotamento. O orçamento de testes de UI permanece inalterado.
