## 1. Configuração e camadas internas

- [x] 1.1 Remover o import de `presentation.settings` de `application/analyze/_config.py`, substituindo `from_settings` por construção a partir de mapping
- [x] 1.2 Atualizar `application/analyze` para usar defaults/configuração injetada sem depender da presentation
- [x] 1.3 Mover `SHORTCUT_CHECK_PATH` de `domain/constants.py` para `infrastructure/desktop.py` e remover `import os` do domain
- [x] 1.4 Atualizar a GUI para montar `CurvaJurosConfig` a partir de `Settings` e injetar em `analyze`/`analyze_evolution`
- [x] 1.5 Exportar `montar_evolucao_resumo` pela API pública de `application.analyze` e remover imports de `_texto_evolucao` pela GUI

## 2. Serviços de aplicação headless

- [x] 2.1 Tornar `days_ago` público e atualizar imports em `infrastructure` e testes
- [x] 2.2 Implementar `nearest_business_day` na application e remover o cálculo de `presentation/gui/window.py`
- [x] 2.3 Implementar validação de data de consulta (formato, data futura, idade máxima do histórico) na application, preservando as mensagens atuais
- [x] 2.4 Implementar estatísticas de taxas (mínimo/máximo) na application
- [x] 2.5 Implementar seleção do payload de exportação (bruto, consolidado, evolução, sem dados) na application
- [x] 2.6 Atualizar `presentation/gui/fetch.py`, `window.py` e `actions.py` para usar os serviços da application

## 3. View-model e dispatch de apresentação

- [x] 3.1 Criar `presentation/view_model.py` sem imports de Tkinter, com estatísticas, estados de controles, modo de gráfico e texto de exportação
- [x] 3.2 Atualizar `presentation/gui/chart.py` para consumir o view-model em estatísticas, habilitação de botões e seleção de renderizador
- [x] 3.3 Atualizar `presentation/gui/actions.py` para copiar o texto produzido pelo serviço de exportação
- [x] 3.4 Adicionar testes headless para o view-model cobrindo dados vazios, erro, modos de visualização e evolução

## 4. Dados de gráfico headless

- [x] 4.1 Criar `application/chart_data.py` e mover `_nearest_ticks`, `_interpolate_rates`, `_nearest_rate`, `_consolidated_3d_data`, `_daily_3d_data` e `_interpolate_3d_surface`
- [x] 4.2 Atualizar `presentation/charts.py` para importar as transformações da application e manter apenas renderização
- [x] 4.3 Atualizar imports em `tests/test_charts_data.py`, `tests/test_charts_render.py` e `tests/test_b3_selic_pre.py`
- [x] 4.4 Adicionar/ajustar testes headless garantindo que a grade 3D e as marcações são calculadas sem matplotlib

## 5. Injeção de adapters e composition root

- [x] 5.1 Adicionar parâmetros opcionais de dependência em `SelicPreApp` (cliente, `shortcut_exists`, `create_shortcut`, `icon_source`, `settings`)
- [x] 5.2 Atualizar `launch_gui` para instanciar adapters de infrastructure e injetá-los na aplicação
- [x] 5.3 Remover imports de infrastructure de `presentation/gui/app.py` e `presentation/gui/actions.py`
- [x] 5.4 Refatorar `presentation/cli.py` para delegar resolução de data, seleção de saída e formatação aos serviços de application, mantendo apenas parsing e composição
- [x] 5.5 Atualizar testes de CLI e GUI para injetar fakes em vez de depender de infraestrutura concreta

## 6. Migração dos testes de UI para headless

- [x] 6.1 Criar testes headless para validação de data, sucesso/vazio/erro, estados de botões e modos de evolução/3D
- [x] 6.2 Criar testes headless para exportação bruta, consolidada, evolução e ausência de dados
- [x] 6.3 Criar testes headless para dispatch de gráfico e cálculo de estatísticas
- [x] 6.4 Migrar o teste de callback de atalho para o serviço de ação; manter na UI apenas wiring necessário
- [x] 6.5 Remover de `tests/test_b3_selic_pre_gui.py` os testes já cobertos headless, mantendo somente montagem/apresentação de widgets
- [x] 6.6 Reduzir `UI_TEST_BUDGET` em `tests/test_ui_test_budget.py` para a contagem real (meta: ≤ 6)
- [x] 6.7 Remover de `tests/architecture_allowlist.py` as aprovações que deixarem de ser necessárias, mantendo apenas composition roots legítimos

## 7. Validação

- [x] 7.1 Executar `make lint`
- [x] 7.2 Executar `make complexity`
- [x] 7.3 Executar os testes diretamente impactados (application, charts data, view-model, CLI, GUI e guards de arquitetura/orçamento)
- [x] 7.4 Executar a suíte completa justificadamente, pois a change altera contratos compartilhados entre application, GUI e CLI
- [x] 7.5 Registrar teste manual opcional da GUI (abrir a janela, buscar uma data, alternar curva curta/longa, evolução, 3D e copiar dados) para o usuário validar visualmente
