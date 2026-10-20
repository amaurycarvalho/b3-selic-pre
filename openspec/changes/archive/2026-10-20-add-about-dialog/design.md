## Context

Ver `proposal.md` para motivação e escopo. O estado atual relevante:

- `__version__` vive em `src/b3_selic_pre/__init__.py`; não existe `__release_date__` nem verificação de versão.
- A barra superior é montada em `presentation/gui/app.py` e já carrega ícones de `src/b3_selic_pre/icons/`.
- O diretório de logs tem fonte única em `infrastructure/logging_setup.log_dir()`.
- `GuiDependencies` já injeta adapters na GUI; `launch.py` é o composition root.
- `tests/test_architecture.py` proíbe `urllib` em `application` e `tkinter` em `infrastructure`.
- O orçamento de testes de UI está em 5/5 (`tests/test_ui_test_budget.py`); a lógica nova precisa ser testada headless.

## Goals / Non-Goals

**Goals:**

- Manter a lógica de apresentação, comparação de versões e decisão do aviso independente de Tk e de rede.
- Isolar toda I/O externa (GitHub, navegador, gerenciador de arquivos) em `infrastructure`.
- Manter o diálogo responsivo e resiliente a falhas de rede ou de integração com o desktop.
- Permitir testes headless completos sem aumentar o orçamento de UI.

**Non-Goals:**

- Não implementar download, instalação ou atualização automática.
- Não alterar o comportamento de `--version` nem o cache de dados da B3.
- Não criar o diretório de logs sob demanda.
- Não adicionar dependência de terceiros para comparação de versões.

## Decisions

### 1. Separação por camadas

- `application/about.py` (novo): dataclass imutável com os dados do diálogo, constante do texto de apresentação, parser/comparador de versões e função que decide o texto do aviso.
- `infrastructure/links.py` (novo): `open_url(url)` e `open_directory(path)`, com implementação por plataforma.
- `infrastructure/release_check.py` (novo): consulta `https://api.github.com/repos/amaurycarvalho/b3-selic-pre/releases/latest` com `urllib.request`, timeout curto e `User-Agent` obrigatório; devolve apenas a versão normalizada ou `None`.
- `presentation/gui/about.py` (novo): mixin com `_open_about`, montagem do `Toplevel` modal e atualização do aviso.
- `presentation/gui/dependencies.py`: novos callables injetáveis (`open_url`, `open_directory`, `log_directory`, `latest_version`).
- `presentation/gui/launch.py`: composition root passa os adapters reais.

Alternativa considerada: colocar tudo em `app.py`. Rejeitada por concentrar I/O, rede e UI no mesmo módulo, dificultar testes headless e violar o padrão de mixins já usado.

### 2. Verificação de versão em background com cache de sessão

- A primeira abertura do "Sobre" dispara uma `threading.Thread` daemon.
- O resultado é publicado na thread do Tk via `root.after(0, ...)`, seguindo o padrão de `fetch.py`.
- O resultado (inclusive ausência de versão mais nova) fica cacheado em memória pelo resto da sessão.
- Enquanto a verificação está pendente, o diálogo é exibido imediatamente sem aviso.
- Se o diálogo for fechado antes da resposta, a atualização é ignorada (`winfo_exists`).
- Falha, timeout, HTTP não-200, JSON inválido ou tag malformada resultam em `None`, sem aviso e sem erro visível.

Alternativas consideradas: verificação síncrona ao abrir (trava a UI por até o timeout) e verificação na inicialização (adiciona chamada externa mesmo para quem nunca abre o "Sobre"). Preferiu-se o modelo preguiçoso, cacheado e best-effort.

### 3. Comparação de versões sem dependência nova

- Normalizar a string removendo prefixo `v`.
- Interpretar até três segmentos numéricos (`X.Y.Z`), preenchendo ausentes com zero quando necessário.
- Comparar tuplas de inteiros.
- Qualquer versão malformada é tratada como ausência de informação, nunca como atualização.

Alternativa considerada: `packaging.version`. Rejeitada para não adicionar dependência de runtime só para três inteiros.

### 4. Diálogo modal e layout

- `tk.Toplevel` com `transient(root)`, `grab_set()`, `resizable(False, False)` e fechamento por `WM_DELETE_WINDOW`.
- Ícone: reutilizar `deps.icon_source()` e manter a referência `PhotoImage` viva enquanto o diálogo existir.
- Conteúdo em `ttk.Frame` com padding: ícone à esquerda; título, data e licença à direita; descrição abaixo; botões de repositório, logs e "Fechar"; rodapé reservado ao aviso de versão.
- A linha de ações ocupa a largura do conteúdo, com "Repositório" e "Diretório de logs" à esquerda e "Fechar" à direita. O botão "Fechar" usa o mesmo `_close_about` do `WM_DELETE_WINDOW`, liberando o `grab_set()` e descartando a referência do diálogo.
- A mensagem de indisponibilidade dos logs aparece em um `ttk.Label` próprio do diálogo, substituindo o aviso de versão no rodapé ou ocupando uma linha de status local. A barra de status principal não é alterada.
- O botão "Sobre" fica em `side=LEFT`, após o botão de copiar, com `padx` maior; o botão de copiar também recebe `padx` à esquerda para se afastar do botão de busca.
- O botão é somente ícone, consistente com os demais botões da barra, com tooltip "Sobre o aplicativo".
- O botão não entra em `_lockable_widgets`: permanece disponível durante buscas.

### 5. Abertura de links e diretórios

- URLs: `webbrowser.open(url)` em `infrastructure/links.py`.
- Diretórios:
  - Windows: `os.startfile(path)`.
  - macOS: `subprocess.run(["open", path])`.
  - Linux: `subprocess.run(["xdg-open", path])`.
- O adapter de diretório verifica `os.path.isdir(path)` antes de abrir e retorna um resultado booleano/erro controlado.
- A janela trata o diretório ausente exibindo a mensagem local; nenhum diretório é criado.
- Falha ao abrir um link ou diretório existente também é comunicada no diálogo, sem propagar exceção.

### 6. Data de lançamento estática

- Adicionar `__release_date__ = "2026-10-19"` em `src/b3_selic_pre/__init__.py`.
- A data não é calculada em runtime; ela representa a data do release atual.
- Atualizar `.opencode/skills/release-version/SKILL.md` para substituir `__release_date__` pela data corrente ao alterar `__version__`, `pyproject.toml` e `b3-selic-pre.spec`.

### 7. Estratégia de testes

- Testes headless para `application/about.py`: texto do aviso, versões iguais, mais novas, mais antigas, prefixo `v` e entradas malformadas.
- Testes headless para `infrastructure/release_check.py`: resposta válida, tag com `v`, HTTP não-200, timeout, JSON inválido e ausência de `tag_name`.
- Testes headless para `infrastructure/links.py`: escolha do comando por plataforma, diretório inexistente e falha de abertura.
- Nenhum teste novo de Tk; o diálogo é validado por inspeção manual e pela lógica headless.

## Risks / Trade-offs

- [Chamada externa ao GitHub conflita com a métrica "zero dependência além da B3"] → A verificação é opcional, preguiçosa, best-effort e sem efeito funcional quando falha.
- [Limite de 60 requisições/hora sem autenticação] → Uma única consulta por sessão, cacheada.
- [Resposta chegar depois de o diálogo ser fechado] → Verificar `winfo_exists` antes de atualizar.
- [Reentrância ao abrir o "Sobre" várias vezes] → Reutilizar o cache e impedir mais de uma verificação concorrente.
- [Falha do `webbrowser`/`xdg-open` em ambientes mínimos] → Comunicar no diálogo, sem exceção não tratada.
- [Caminho do ícone em build PyInstaller] → Reutilizar `icon_source()`, que já trata `sys._MEIPASS`.
- [Orçamento de testes de UI esgotado] → Toda lógica nova testável fica fora da GUI; não criar testes `@pytest.mark.ui`.

## Migration Plan

- Não há migração de dados.
- Adicionar o metadado `__release_date__` já com a data do release corrente.
- Atualizar a skill de release antes do próximo release para evitar data defasada.
- Rollback: remover o botão/diálogo e os módulos novos; nenhum formato persistido é alterado.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tarefas.
