# Tasks

## 1. Pré-requisitos e composição

- [x] 1.1 Confirmar que `add-tesouro-analise-percentuais` está implementada e expõe taxonomia, percentuais e `SeriesProvider`; verificar com teste de importação headless.
- [x] 1.2 Ajuste aplicado: `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` não entregam mais GUI (Toplevel/abas/tabelas), mantêm dados + CLI e tiveram as specs antigas de GUI removidas.
- [x] 1.3 Estender `GuiDependencies` com as fábricas/adaptr de análise do Tesouro e atualizar `launch.py` para compor o shell; verificar que `launch_gui` continua importável e que o composition root monta sem rede.

## 2. Shell de abas

- [x] 2.1 Criar `TabSpec` e `LazyTabRegistry` headless (sem Tkinter), com `ensure_built`, `mark_visible`, `is_built` e ordem determinística; verificar testes de idempotência, duplicata e ordem.
- [x] 2.2 Criar `AppShell` com `ttk.Notebook` de nível superior, registro de abas, geometria, título, escudo e `_shell_ready`; verificar teste headless do shell e adaptação dos 5 testes de UI existentes.
- [x] 2.3 Registrar `SELIC Pré` como primeira aba e `Tesouro Direto` como segunda; verificar que `Câmbio` não aparece antes de ser registrada.
- [x] 2.4 Conectar `<<NotebookTabChanged>>` ao `ensure_built` da aba visível, ignorando eventos durante a montagem; verificar teste de troca de aba e de construção única.
- [x] 2.5 Garantir que o escudo de inicialização cobre o notebook e que a troca de abas só funciona após o término; verificar teste de UI existente adaptado.

## 3. Aba SELIC Pré

- [x] 3.1 Reparentar a barra superior, opções de visualização, gráfico, toolbar e statusbar para o frame da aba `SELIC Pré`, sem reescrever a lógica; verificar que busca, gráfico, análise, cópia e exportação continuam funcionando.
- [x] 3.2 Ajustar `_lockable_widgets`, `_setup_tooltips` e `_set_ui_locked` para o escopo da aba `SELIC Pré`; verificar que controles de outras abas não são afetados.
- [x] 3.3 Restringir os atalhos globais (`F5`, `Ctrl-D`, `Ctrl-Shift-C`, `Ctrl-E`, `Ctrl-L`) à aba `SELIC Pré` ativa; verificar teste headless do guard e um teste de UI existente.
- [x] 3.4 Preservar o título atual da janela e o estado da tela ao alternar de aba; verificar teste de UI existente adaptado.

## 4. Aba Tesouro Direto e lazy sub-tabs

- [x] 4.1 Criar `TesouroDiretoTab` com sub-notebook `Visão geral`, `Estoque` e `Apetite do mercado`; verificar que as três sub-abas existem e que não há tabelas brutas.
- [x] 4.2 Implementar o lazy build das sub-abas na primeira visibilidade, com `Visão geral` como padrão; verificar teste headless de construção única e teste de UI de montagem.
- [x] 4.3 Criar controllers/view-models headless para cada sub-aba, com estado de janela, carregamento, cache, erro e habilitação; verificar testes headless.
- [x] 4.4 Implementar o seletor de janela 14d/3m/12m/3a, ancorado no último dado, e os rótulos de data-base; verificar testes de janela e ausência de períodos futuros.

## 5. Gráficos

- [x] 5.1 Implementar `render_current_share` para barras 100% empilhadas por família/título; verificar teste headless de dados/figura e teste visual manual.
- [x] 5.2 Implementar `render_evolution` para área 100% empilhada por família, com buckets diário/semanal/mensal; verificar teste headless de série e teste visual manual.
- [x] 5.3 Implementar `render_gap` para a `Visão geral` (apetite − estoque por família); verificar teste headless e teste visual manual.
- [x] 5.4 Montar os dois gráficos por sub-aba com `FigureCanvasTkAgg`, criados apenas na primeira visibilidade; verificar que abas ocultas não criam canvas no startup.
- [x] 5.5 Garantir que a presentation não calcula percentuais; ela consome `SeriesPoint` da aplicação; verificar com `tests/test_architecture.py` e teste de importação.

## 6. Cache, atualização e status

- [x] 6.1 Implementar o primeiro show cache-only: sem cache, mostrar “clique em Atualizar” e não acessar a rede; verificar teste headless e teste de UI de estado vazio.
- [x] 6.2 Implementar “Atualizar” (cache válido) e “Ignorar cache” (verificação condicional/`304`) por sub-aba; verificar testes de cache e `304`.
- [x] 6.3 Executar download/parsing/cálculo em thread e atualizar via `root.after`; verificar que a janela principal permanece responsiva.
- [x] 6.4 Implementar progresso indeterminado, desabilitação da atualização e status por sub-aba com fonte, extração e data-base; verificar testes headless de status e teste de UI.
- [x] 6.5 Tratar falha isolada por sub-aba e fechamento durante a carga sem exceção; verificar testes de falha isolada e de fechamento.

## 7. Integração, documentação e validação

- [x] 7.1 Atualizar `README.md` e `docs/misc/panels.md` (ou equivalente) com a nova estrutura de abas, lazy loading e localização dos dados brutos na CLI; verificar que a documentação descreve a navegação real.
- [x] 7.2 Rodar `make lint` e `make complexity`; corrigir violações.
- [x] 7.3 Rodar a suíte completa `make test` (justificada por alterar a janela principal, composition root e contratos compartilhados) e registrar o resultado.
- [x] 7.4 Verificar o orçamento de UI permanece em 5 testes; se algum teste atual migrar para headless, reduzir o orçamento.
- [x] 7.5 Registrar um teste manual opcional: abrir a janela, alternar `SELIC Pré`/`Tesouro Direto`, confirmar lazy build, dois gráficos por sub-aba, seletor de janela e status.

## 8. Refinamentos de UX das abas

- [x] 8.1 Registrar no proposal, design e specs o chrome das sub-abas, a aba `Sobre` e a legenda SELIC.
- [x] 8.2 Trocar o botão `Atualizar` por ícone, adicionar tooltips, statusbar com progresso e separadores nas três sub-abas.
- [x] 8.3 Adicionar texto orientativo somente leitura com `Objetivo`, `Responde a pergunta`, `Indicadores envolvidos` e `Como interpretar`, em painel redimensionável.
- [x] 8.4 Adicionar toolbar de gráfico com navegação e cópia da imagem em cada gráfico.
- [x] 8.5 Adicionar rótulos de hover nos pontos de dados dos gráficos atuais e de evolução.
- [x] 8.6 Padronizar os títulos da `Visão geral` e adicionar grades verticais nas evoluções de `Estoque` e `Apetite`.
- [x] 8.7 Exibir a legenda da aba `SELIC Pré` sempre no canto superior direito.
- [x] 8.8 Criar a aba `Sobre` à direita de `Tesouro Direto`, mantendo o botão `Sobre` existente.
- [x] 8.9 Validar com `make lint`, `make complexity`, testes headless e smoke test da GUI.

## 9. Correções de UX após validação manual

- [x] 9.1 Diagnosticar o delay: confirmar lazy por sub-aba e mover a leitura inicial do cache para thread, sem rede.
- [x] 9.2 Restringir a leitura de cache por sub-aba: Visão geral lê estoque+vendas; Estoque lê estoque; Apetite lê vendas+resgates.
- [x] 9.3 Corrigir a statusbar para reservar espaço na base antes do painel expansível.
- [x] 9.4 Deixar os títulos das seções do texto orientativo em negrito, com `:` ao final.
- [x] 9.5 Usar uma única toolbar visível abaixo do segundo gráfico, alternando entre os dois canvases.
- [x] 9.6 Adicionar ao Sobre um frame e um textbox somente leitura sobre a aplicação, a CLI e o MCP.

## 10. Feedback, detalhe e toolbars independentes

- [x] 10.1 Adicionar probe barato de cache e textos centrais de “sem dados” e “carregando” nos dois gráficos.
- [x] 10.2 Orientar a statusbar a pressionar `Atualizar` quando não houver cache.
- [x] 10.3 Mover a linha de detalhe (fluxo líquido) para ao lado do checkbox `Ignorar cache`.
- [x] 10.4 Trocar a toolbar única por uma toolbar vertical independente à esquerda de cada gráfico.
- [x] 10.5 Deixar as seções do texto da aba `Sobre` em negrito com `:` e detalhar sintaxe/parâmetros da CLI e MCP.

## 11. Ajuste visual das toolbars verticais

- [x] 11.1 Remover os separadores/spacers da toolbar vertical de cada gráfico do Tesouro Direto.

## Workflow follow-up

- Revisar a change com o usuário e arquivar após a aprovação.
- A change de Câmbio deve apenas registrar sua aba no `TabRegistry`, sem alterar o shell.
