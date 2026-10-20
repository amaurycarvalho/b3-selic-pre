## 1. Módulo do escudo

- [x] 1.1 Criar `src/b3_selic_pre/presentation/gui/startup.py` com a constante `SETTLE_MS = 200` e uma classe `StartupShield` que cria um `ttk.Frame` opaco filho do root, com `ttk.Label` centralizado contendo "Aguarde a inicialização da aplicação…"; verificar importando o módulo em `xvfb-run -a .venv/bin/python -c "from b3_selic_pre.presentation.gui.startup import StartupShield, SETTLE_MS"`.
- [x] 1.2 Implementar em `StartupShield` os métodos `show()` (cria frame/label, `place(relwidth=1, relheight=1)`, `lift()` e `update_idletasks()`), `raise_above_siblings()` (`lift()`) e `destroy()` (remove frame e limpa referências); verificar com um script curto sob `xvfb-run` que o frame cobre 100% de um root de teste após `raise_above_siblings()`.
- [x] 1.3 Implementar o bloqueio de teclado no escudo: `takefocus` habilitado, `focus_set()` após ficar visível e bindings de `<KeyPress>`, `<Tab>`, `<Shift-Tab>` e `<ISO_Left_Tab>` retornando `"break"`; verificar com `event_generate` sob `xvfb-run` que Tab não muda o foco e que F5 não dispara callback registrado no root.
- [x] 1.4 Garantir que `StartupShield` não dependa de `matplotlib` nem de outros módulos pesados e que use imports de Tkinter locais, seguindo o padrão dos demais mixins; verificar com `make lint` ao final do grupo e por inspeção dos imports.

## 2. Integração no `SelicPreApp`

- [x] 2.1 Em `src/b3_selic_pre/presentation/gui/app.py`, criar o escudo em `__init__` depois de `_apply_saved_settings()` e do bind de `<Configure>`, mas antes de `_build_top_bar()`, chamando `show()`; verificar com inicialização manual sob cache frio que o escudo aparece antes da construção da barra superior.
- [x] 2.2 Após construir barra superior, opções, gráfico, toolbar e statusbar, chamar `raise_above_siblings()` no escudo; verificar manualmente que nenhum controle da barra superior fica visível acima do escudo.
- [x] 2.3 Remover as chamadas de `_setup_shortcuts()` e `_setup_tooltips()` do `__init__` e criar `_finish_startup()` para destruir o escudo, chamar `_update_button_states()`, registrar atalhos e tooltips e limpar a referência ao escudo; agendar via `root.after(SETTLE_MS, self._finish_startup)` ao final do `__init__`; verificar manualmente que atalhos e tooltips funcionam somente após o dismiss.
- [x] 2.4 Desabilitar os widgets de `_lockable_widgets` ao final do build enquanto o escudo estiver ativo, deixando `_finish_startup()` restaurar o estado correto por `_update_button_states()`; verificar que `pytest tests/test_b3_selic_pre_gui.py -m slow` continua passando e que os controles ficam desabilitados durante o escudo.
- [x] 2.5 Tornar `_finish_startup()` tolerante a root já destruído e a chamadas repetidas (checar `winfo_exists()` e usar uma flag ou limpar a referência antes de operar); verificar fechando a janela durante o intervalo de settle e confirmando que nenhum erro é exibido ou registrado.

## 3. Tooltips e eventos enfileirados

- [x] 3.1 Confirmar que nenhum `Tooltip` é criado durante o escudo, pois `_setup_tooltips()` passou para `_finish_startup()`; verificar manualmente passando o mouse sobre a área da barra superior durante a inicialização e confirmando que nenhum popup amarelo aparece.
- [x] 3.2 Verificar que, após o encerramento, o hover na barra superior volta a exibir tooltips normalmente; repetir a verificação com pelo menos o seletor de data e o botão de busca.
- [x] 3.3 Verificar que cliques e teclas gerados durante o build não disparam ações depois do encerramento: durante o escudo, clicar na posição futura do botão "Buscar" e pressionar F5; após o dismiss, confirmar que nenhuma busca foi iniciada e que o estado inicial permanece.

## 4. Verificação manual de comportamento

- [x] 4.1 Executar a GUI com cache frio (`XDG_CACHE_HOME` e `XDG_CONFIG_HOME` apontando para diretórios temporários) e confirmar que o escudo fica visível durante o build, com a mensagem centralizada e sem controles aparecendo acima dele.
- [x] 4.2 Durante o escudo, verificar bloqueio de ponteiro e teclado: clicar sobre rótulo, entrada de data, botões e área de combobox da barra superior; pressionar F5, Ctrl+D, Ctrl+Shift+C, Ctrl+E, Ctrl+L, Tab e Shift+Tab; confirmar que nenhuma ação ocorre e que o foco permanece no escudo.
- [x] 4.3 Durante o escudo, redimensionar e maximizar a janela; confirmar que o escudo continua cobrindo toda a área útil.
- [x] 4.4 Confirmar que fechar a janela durante o escudo encerra a aplicação normalmente, sem exceção no terminal ou no log.
- [x] 4.5 Após o dismiss, confirmar que a mensagem inicial "Informe uma data e clique em Buscar." está visível, que os controles refletem o estado sem dados e que atalhos e tooltips voltam a funcionar.
- [x] 4.6 Repetir a inicialização com cache quente, com geometria salva, com `window_maximized` e com `sidebar` ativado; confirmar que o escudo cobre os redimensionamentos agendados e que o encerramento ocorre sem piscar a barra superior.
- [x] 4.7 Verificar em uma segunda plataforma disponível (Windows, se possível) que `update_idletasks()` pinta o escudo antes do build; registrar o resultado da verificação manual.

## 5. Qualidade e validação

- [x] 5.1 Executar `make lint` e corrigir eventuais violações.
- [x] 5.2 Executar `make complexity` e corrigir eventuais violações de complexidade.
- [x] 5.3 Executar os testes diretamente relacionados: `xvfb-run -a .venv/bin/python -m pytest -m slow tests/test_b3_selic_pre_gui.py` e `pytest tests/test_architecture.py tests/test_ui_test_budget.py`.
- [x] 5.4 Executar `make test` por se tratar de mudança no comportamento global da GUI.
- [x] 5.5 Executar `openspec validate add-startup-shield --strict` e corrigir eventuais problemas dos artefatos.
- [x] 5.6 Confirmar que nenhum teste `@pytest.mark.ui` novo foi adicionado e que o orçamento continua em 5, verificando com `pytest tests/test_ui_test_budget.py`.
