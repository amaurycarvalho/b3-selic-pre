# Tasks

## 1. View-model headless

- [x] 1.1 Ajustar `TesouroAnaliseViewModel.status_text`/`status_kind` para priorizar carga sobre erro e sobre cache vazio, usando `loading_origin` e `loading_stage`; verificar com testes em `tests/test_tesouro_analise_gui_view_model.py` para carga sem cache, carga com cache e retentativa após erro.
- [x] 1.2 Ajustar `placeholder_message` para exibir carregamento sempre que `loading` for verdadeiro; verificar com teste de sub-aba sem cache durante atualização sem o texto "Pressione Atualizar".
- [x] 1.3 Renderizar `Erro ao ler o cache: …` quando `error_context` indicar leitura de cache e manter `Erro ao carregar: …` nos demais erros; verificar com testes de view-model dos dois contextos.

## 2. Controller e loaders

- [x] 2.1 Adicionar `begin_load(cache_only=...)` ao controller, limpando `error`, definindo `loading_origin` e permitindo que `load()` reutilize o mesmo início; verificar com teste de que uma retentativa não expõe o erro anterior antes da primeira atualização.
- [x] 2.2 Registrar falha de leitura `cache_only` como erro com contexto de cache, mantendo cache miss (`None`) como ausência não errada; verificar em `tests/test_tesouro_analise_controller.py`.
- [x] 2.3 Adicionar `note_cache_presence(cache_present)` e verificar a decisão headless de recarregar cache apenas quando ele passa de ausente para presente, sem dados e sem carga em andamento.
- [x] 2.4 Propagar `stage_callback` opcional por `TesouroAnaliseController.load` e `make_loader`, emitindo `vendas`, `resgates` e `estoque` antes de cada operação de rede e mantendo loaders de duas posições compatíveis; verificar em `tests/test_tesouro_loaders.py` e `tests/test_tesouro_analise_controller.py`.

## 3. Ligação da GUI

- [x] 3.1 Chamar `begin_load` em `_start_load` antes de montar o primeiro view-model e limpar `loading_stage` ao concluir; verificar com revisão estática e com os testes headless de controller.
- [x] 3.2 Repassar o callback de etapa do worker para a thread da UI com `root.after`, aplicando `loading_stage` e reaplicando `status_text`/`status_kind`; verificar com teste manual da seção 4.4 e revisão estática de que callbacks tardios respeitam `_closed`.
- [x] 3.3 Ao reexibir sub-aba sem dados, reavaliar a presença de cache (`cache_available` + `series_available`) e iniciar leitura `cache_only` apenas quando `note_cache_presence` indicar; verificar com teste headless de `note_cache_presence` e com o roteiro manual de cache preenchido por outra sub-aba.

## 4. Validação

- [x] 4.1 Executar `make lint` e verificar que termina sem erros.
- [x] 4.2 Executar `make complexity` e verificar que termina sem violações.
- [x] 4.3 Executar `python -m pytest tests/test_tesouro_analise_gui_view_model.py tests/test_tesouro_analise_controller.py tests/test_tesouro_loaders.py -q` e verificar que todos passam.
- [ ] 4.4 Teste manual opcional: sem cache, abrir cada sub-aba, confirmar o aviso e o clique em `Atualizar` mostrando `Atualizando… (etapa)`; provocar falha, tentar de novo e confirmar que o erro antigo desaparece durante a nova carga.
- [ ] 4.5 Teste manual opcional: abrir uma sub-aba sem cache, preencher o cache por outra sub-aba e reexibir a primeira; confirmar que ela lê o cache sem rede e deixa de orientar `Atualizar`.
