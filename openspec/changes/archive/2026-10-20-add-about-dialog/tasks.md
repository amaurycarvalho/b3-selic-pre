## 1. Metadados e lógica de apresentação

- [x] 1.1 Adicionar `__release_date__ = "2026-10-19"` em `src/b3_selic_pre/__init__.py`; verificar com `python -c "import b3_selic_pre; print(b3_selic_pre.__version__, b3_selic_pre.__release_date__)"`.
- [x] 1.2 Criar `src/b3_selic_pre/application/about.py` com `AboutInfo`, texto de apresentação, normalização/comparação de versões e função que produz o aviso `Nova versão vX.Y.Z disponível`; verificar com `pytest tests/test_about.py`.
- [x] 1.3 Criar `tests/test_about.py` cobrindo versões iguais, mais novas, mais antigas, prefixo `v`, entradas malformadas, ausência de aviso e composição dos metadados; verificar com `pytest tests/test_about.py`.

## 2. Adapters de infraestrutura

- [x] 2.1 Criar `src/b3_selic_pre/infrastructure/links.py` com `open_url` e `open_directory`, usando `webbrowser` para URLs e o comando adequado por plataforma para diretórios; verificar com `pytest tests/test_links.py`.
- [x] 2.2 Criar `tests/test_links.py` cobrindo Linux, macOS, Windows, diretório inexistente e falha de abertura, com mocks de `webbrowser`, `subprocess` e `os.startfile`; verificar com `pytest tests/test_links.py`.
- [x] 2.3 Criar `src/b3_selic_pre/infrastructure/release_check.py` consultando `https://api.github.com/repos/amaurycarvalho/b3-selic-pre/releases/latest` com `urllib.request`, `User-Agent`, timeout curto e retorno `None` em falha; verificar com `pytest tests/test_release_check.py`.
- [x] 2.4 Criar `tests/test_release_check.py` cobrindo resposta válida, tag com `v`, HTTP não-200, timeout, JSON inválido, `tag_name` ausente e URL correta; verificar com `pytest tests/test_release_check.py`.

## 3. Integração com a GUI

- [x] 3.1 Estender `GuiDependencies` com `open_url`, `open_directory`, `log_directory` e `latest_version`, e injetar os adapters reais em `presentation/gui/launch.py`; verificar com `pytest tests/test_architecture.py tests/test_b3_selic_pre_gui.py` e inspeção do composition root.
- [x] 3.2 Carregar `help-about.png` em `_load_icons`, adicionar o botão "Sobre" à direita do botão de copiar com espaçamento de destaque, tooltip e sem incluí-lo em `_lockable_widgets`; verificar por execução manual da GUI.
- [x] 3.3 Criar `src/b3_selic_pre/presentation/gui/about.py` com o `Toplevel` modal, ícone, título/versão, data ISO, licença, descrição, botões de repositório/logs e rodapé de aviso; verificar por execução manual da GUI.
- [x] 3.4 Implementar no diálogo a verificação em background na primeira abertura, cache por sessão, atualização via `root.after` e descarte seguro quando a janela já foi fechada; verificar por execução manual com resposta simulada de versão mais nova e de falha.
- [x] 3.5 Implementar no diálogo a mensagem local de diretório de logs indisponível, sem criar o diretório e sem alterar a barra de status principal; verificar por execução manual com `XDG_CACHE_HOME` apontando para um diretório sem logs.
- [x] 3.6 Confirmar que nenhum teste `@pytest.mark.ui` foi adicionado e que o orçamento continua em 5; verificar com `pytest tests/test_ui_test_budget.py`.

## 4. Processo de release

- [x] 4.1 Atualizar `.opencode/skills/release-version/SKILL.md` para substituir `__release_date__` pela data corrente ao alterar `__version__`, `pyproject.toml` e `b3-selic-pre.spec`; verificar relendo a skill e conferindo os passos e a saída esperada.

## 5. Validação final

- [x] 5.1 Executar `make lint` e corrigir eventuais violações.
- [x] 5.2 Executar `make complexity` e corrigir eventuais violações de complexidade.
- [x] 5.3 Executar os testes diretamente relacionados: `pytest tests/test_about.py tests/test_links.py tests/test_release_check.py tests/test_architecture.py tests/test_ui_test_budget.py`.
- [x] 5.4 Executar `make test` por se tratar de mudança em comportamento global da GUI e nos metadados do pacote.
- [x] 5.5 Executar `openspec validate add-about-dialog --strict` e corrigir eventuais problemas dos artefatos.
- [x] 5.6 Verificação manual final: abrir a GUI, conferir posição/espaçamento/tooltip do "Sobre", conteúdo e modalidade do diálogo, abertura do repositório e dos logs, e o aviso de nova versão com uma resposta simulada.

## 6. Botão "Fechar" no diálogo Sobre

- [x] 6.1 Adicionar o botão "Fechar" à linha de ações do diálogo, alinhado à direita e usando o mesmo fluxo de `_close_about` do `WM_DELETE_WINDOW`; verificar por execução manual da GUI.
- [x] 6.2 Confirmar que o botão encerra o diálogo, libera a interação da janela principal e permite reabrir o "Sobre"; verificar manualmente sob `xvfb-run`.
- [x] 6.3 Executar `make lint`, `make complexity`, os testes diretamente relacionados e `openspec validate add-about-dialog --strict`.
