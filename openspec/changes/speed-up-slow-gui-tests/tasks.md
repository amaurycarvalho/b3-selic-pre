## 1. Refatorar a classe principal de testes de GUI para reutilizar o app

- [ ] 1.1 Converter `SelicPreAppTest.setUp`/`tearDown` em `setUpClass`/`tearDownClass` construindo uma única instância de `tk.Tk` + `SelicPreApp`
- [ ] 1.2 Implementar o helper `_reset_app_state()` que restaura `records`, `historical_data`, `_data_source`, `_historical_fetching`, `_last_reference_date`, `view_var`, `evolution_var`, `var_3d`, `sidebar_var`, `date_var`, `status_var`, estado de `cb_3d`, sidebar recolhida, `figure` limpo e `_update_button_states()`
- [ ] 1.3 Chamar `_reset_app_state()` no início de cada caso de teste (novo `setUp`)
- [ ] 1.4 Rodar `make test` e verificar que os 19 testes de GUI continuam passando e o tempo caiu

## 2. Isolar os testes de atalho em uma classe com apps compartilhados

- [ ] 2.1 Criar `SelicPreAppShortcutTest` com `setUpClass` que constrói dois apps: um com `shortcut_exists` → `False` e outro com `shortcut_exists` → `True`
- [ ] 2.2 Mover `test_shortcut_button_shown_when_no_shortcut`, `test_shortcut_button_hidden_when_shortcut_exists` e `test_shortcut_button_callback_creates_shortcut` para a nova classe, reutilizando os dois apps
- [ ] 2.3 Remover o helper `_make_app_with_shortcut` da classe principal
- [ ] 2.4 Rodar `pytest tests/test_b3_selic_pre_gui.py --durations=10 -q` e confirmar que os testes de atalho caem abaixo de 1s

## 3. Seam para injetar widget de data mais barato (opcional)

- [ ] 3.1 Introduzir ponto de extensão em `app.py` (ex.: atributo de classe `_date_entry_factory` ou método `_create_date_entry`) com default `DateEntry`
- [ ] 3.2 Ajustar os testes de GUI para injetar um widget mais leve (`ttk.Entry`) quando a seleção de data não é o foco do caso
- [ ] 3.3 Manter `test_invalid_date_shows_validation_without_fetching` exercitando o caminho real de data para cobrir o default

## 4. Verificação final

- [ ] 4.1 Rodar `make test` completo e registrar o tempo antes/depois (alvo ~7s)
- [ ] 4.2 Confirmar que nenhum teste de GUI excede 1s via `--durations=10`
- [ ] 4.3 Rodar `make lint` e `make quality-gate` para garantir que a mudança não quebra o gate
