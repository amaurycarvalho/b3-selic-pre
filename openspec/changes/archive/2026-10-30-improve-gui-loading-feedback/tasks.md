# Tasks

## 1. Indicador de ocupação compartilhado

- [x] 1.1 Criar `presentation/busy.py` com `WaitCursor` e `BusyIndicator`: contagem de referências por janela raiz, cursor `watch` enquanto houver referência, restauração ao sair, tolerância a janela destruída e label opcional com `enter`/`leave` simétricos; verificar com novo teste headless `tests/test_gui_busy.py` usando raiz e label falsos.
- [x] 1.2 Aplicar o cursor `watch` recursivamente à árvore de widgets (incluindo `tk.Text` e canvas), restaurando o cursor original de cada widget ao sair; verificar em `tests/test_gui_busy.py` que texto e canvas recebem o cursor e voltam ao valor original, inclusive para widgets criados durante o estado ocupado.

## 2. Texto fixo e visibilidade dos gráficos do Tesouro

- [x] 2.1 Em `presentation/gui/tesouro_sub_tab_ui.py`, criar o texto fixo `Processando as informações. Aguarde…` atrás dos painéis com `place`/`lower()`, ocultar os dois painéis com `pack_forget` e reempacotá-los após o desenho; verificar com teste Tk real de que os painéis ficam ocultos, o texto visível e o sash/largura do canvas não mudam.
- [x] 2.2 Ao selecionar/reexibir a sub-aba, ocultar os gráficos antes da leitura do cache e do desenho e reexibi-los somente após a carga concluir; verificar com teste Tk real e com teste manual de troca de sub-abas.
- [x] 2.3 Ao acionar `Atualizar`, ocultar os gráficos e exibir o texto fixo durante a busca, o processamento e o desenho; em `_finish_load`, aplicar `update_loading_state(False)` antes de `_draw` e só reexibir os gráficos depois do desenho e de um `draw_idle()` adicional; verificar com teste Tk real e teste manual do botão `Atualizar`.
- [x] 2.4 Na troca de janela de análise, manter os gráficos visíveis, sem o texto fixo, usando apenas o ponteiro de espera; verificar com teste Tk real e teste manual do seletor de janela.
- [x] 2.5 Restaurar os gráficos após falha de carga/desenho e manter a orientação de cache vazio quando não houver carga nem dados; verificar com teste manual de sub-aba sem cache e de falha simulada.
- [x] 2.6 Em `presentation/gui/tesouro_tab.py`, criar um aviso de construção oculto por frame de sub-aba, mostrá-lo antes de construir, forçar a pintura com `update_idletasks()` e escondê-lo após a construção, sem deixar resíduos; verificar com teste Tk real de que nenhum label está mapeado antes de `enter`.
- [x] 2.7 Estabilizar a geometria: host fixo de 140 px para o progresso, rótulos de status/detalhe com `width=1` e `fill=X`, e ocultação/reexibição dos painéis sem alterar largura, sash ou canvas; verificar com teste Tk real de que as dimensões permanecem iguais antes/depois da carga.

## 3. Feedback de Câmbio e Reserva

- [x] 3.1 Em `presentation/gui/market_tab.py` e `presentation/gui/reserves_sub_tab.py`, compartilhar um `BusyIndicator` por sub-aba e entrar/sair durante o `Atualizar`, mantendo o ponteiro `watch` até o desenho terminar; verificar com teste manual da seção 5.
- [x] 3.2 Restaurar o ponteiro também em falha total e parcial, sem esconder o estado da statusbar, e garantir simetria em `close()`; verificar com teste manual forçando falha de fonte e fechando a janela durante a atualização.

## 4. Resumo de funcionalidades no README e na aba Sobre

- [x] 4.1 Adicionar em `application/about.py` o título `Funcionalidades`, a lista `FEATURES_SUMMARY` e `features_text()`, cobrindo interface gráfica por abas, curva SELIC Pré, Tesouro Direto, Câmbio e Ouro, Reservas Internacionais, Feriados, CLI, MCP, cache local, logging e exportação; verificar com teste headless da constante.
- [x] 4.2 Inserir no início de `README.md`, antes de `Como Instalar`/`Como Usar`, a seção `Funcionalidades` com exatamente o texto de `features_text()`; verificar com o teste de paridade.
- [x] 4.3 Em `presentation/gui/about_tab.py`, acrescentar a seção `Funcionalidades` ao painel somente leitura usando `features_text()`, com `Aplicação:` antes de `Funcionalidades:`; verificar com teste headless que lê o fonte da aba e confirma o uso da constante (sem importar Tk/GUI) e com teste manual da seção 5.
- [x] 4.4 Criar `tests/test_feature_summary.py` que extrai a seção `Funcionalidades` do README, normaliza espaços/quebras e compara com `features_text()`, além de garantir que a seção aparece antes de `Como Instalar`; verificar executando o novo teste.

## 5. Validação

- [x] 5.1 Executar `make lint` e verificar que termina sem erros.
- [x] 5.2 Executar `make complexity` e verificar que termina sem violações.
- [x] 5.3 Executar `python -m pytest tests/test_gui_busy.py tests/test_tesouro_analise_gui_view_model.py tests/test_feature_summary.py -q` e verificar que todos passam.
- [x] 5.4 Executar `make test` porque a mudança toca a GUI, o conteúdo da aba Sobre e o README.
- [x] 5.5 Teste manual opcional: selecionar cada sub-aba do Tesouro Direto e confirmar que os gráficos somem, o texto fixo aparece e os gráficos voltam após a carga.
- [x] 5.6 Teste manual opcional: acionar `Atualizar` e confirmar que os gráficos ficam ocultos até a carga completar e depois são reexibidos, com o ponteiro `watch`.
- [x] 5.7 Teste manual opcional: abrir a aba Sobre e comparar a seção `Funcionalidades` com a seção do README.

## 6. Hardening do layout dos gráficos

- [x] 6.1 Criar `presentation/chart_layout.py` com `apply_tight_layout`: capturar `UserWarning` de tight layout, registrar contexto no log, reemitir avisos não relacionados, aplicar margens conservadoras e registrar falhas sem interromper o desenho.
- [x] 6.2 Substituir as chamadas diretas a `tight_layout` em `charts.py`, `charts_tesouro.py`, `charts_market.py` e `charts_reserves.py` pelo helper compartilhado, preservando `pad=0.4` onde existia.
- [x] 6.3 Criar `tests/test_chart_layout.py` cobrindo log do aviso, fallback, passagem de `pad`, reemissão de avisos não relacionados e falha ao aplicar layout ou margens.
- [x] 6.4 Validar com `make lint`, `make complexity`, `python -m pytest tests/test_chart_layout.py tests/test_charts_tesouro.py tests/test_charts_render.py tests/test_reserves_presentation.py tests/test_market_presentation.py -q` e `make test`.

## 7. Renomeação e feedback de carregamento em Câmbio e Reserva

- [x] 7.1 Renomear a aba de nível superior para `Câmbio e Reserva` em `presentation/gui/shell.py`, `application/about.py`, `README.md` e textos derivados da aba Sobre; atualizar os testes de registro de abas e de paridade do resumo.
- [x] 7.2 Em `presentation/gui/market_sub_tab_ui.py` e `presentation/gui/market_tab.py`, adicionar texto fixo atrás do gráfico, ocultar o painel na seleção e no `Atualizar`, reexibir após desenho e `draw_idle()`, manter o painel visível na troca de opção e restaurar em falha.
- [x] 7.3 Em `presentation/gui/reserves_sub_tab.py`, aplicar o mesmo padrão de texto fixo, ocultação/reexibição, restauração em falha e ponteiro de espera na troca de janela.
- [x] 7.4 Em `presentation/gui/market_tab.py` e nas barras de status, adicionar aviso de construção oculto por frame de sub-aba, host fixo de 140 px para o progresso e rótulos de status com `width=1`.
- [x] 7.5 Cobrir as decisões com testes de fonte para as sub-abas de mercado e reservas e atualizar os testes de nome da aba, do resumo e do shell.
- [x] 7.6 Validar com `make lint`, `make complexity`, testes direcionados de mercado, reservas, resumo, busy e layout, e `make test`.
- [x] 7.7 Manter o primeiro item do resumo de funcionalidades com o texto `Dólar e Ouro`, preservando `Câmbio e Reserva` no rótulo da aba e na linha descritiva do mercado, e atualizar README, aba Sobre e teste de paridade.
