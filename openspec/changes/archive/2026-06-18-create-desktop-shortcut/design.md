## Context

O projeto `b3-selic-pre` é uma aplicação Python que consulta taxas SELIC Pré na B3, com interface CLI e GUI (tkinter). Atualmente o projeto inclui um `b3-selic-pre.desktop` na raiz que precisa ser copiado manualmente pelo usuário. Não há mecanismo programático para criar atalho no desktop ou instalar no menu de aplicações.

O código-fonte é um único arquivo (`b3_selic_pre.py`, ~800 linhas) e a GUI usa tkinter com matplotlib. O app pode ser executado como script Python ou compilado com PyInstaller.

## Goals / Non-Goals

**Goals:**
- Criar atalho no desktop do usuário (FreeDesktop .desktop)
- Instalar o atalho também em `~/.local/share/applications/` (menu de aplicações)
- Copiar o ícone para `~/.local/share/icons/` para referência estável
- Disponibilizar via CLI (`--create-shortcut`) e via botão na GUI
- Detectar se atalho já existe e só mostrar o botão quando ausente
- Funcionar tanto para execução como script Python quanto para binário compilado (PyInstaller)
- Detectar corretamente o diretório Desktop do usuário (considerando locale pt-BR → `~/Área de Trabalho`)

**Non-Goals:**
- Suporte a Windows (.lnk) ou macOS (.app) — escopo inicial apenas Linux
- Remoção/desinstalação do atalho
- Atalho por usuário vs. sistema (sempre por usuário)
- Integração com flatpak/snap/appimage

## Decisions

### 1. Detecção do executável: `sys.frozen` vs script

| Alternativa | Prós | Contras |
|---|---|---|
| **A. Usar `sys.frozen` + fallback** | Cobre ambos os modos; `sys.executable` aponta para o binário real; `sys._MEIPASS` dá acesso aos assets | Precisa de tratamento separado para cada modo |
| B. Sempre usar `sys.executable + script` | Simples | Quebra se o script for movido após a instalação; não funciona para binário compilado |

**Decisão: A.** Verificar `getattr(sys, 'frozen', False)` para detectar PyInstaller. Se frozen, `Exec` aponta para `sys.executable`. Caso contrário, usa `sys.executable + os.path.abspath(sys.argv[0])`. Ambos com `--gui`.

### 2. Detecção do diretório Desktop

| Alternativa | Prós | Contras |
|---|---|---|
| **A. `xdg-user-dir DESKTOP` → fallback `~/.config/user-dirs.dirs` → fallback `~/Desktop`** | Cobre todos os ambientes Linux, inclusive locale pt-BR | Requer subprocess; depende do `xdg-user-dir` estar instalado |
| B. Apenas `~/Desktop` | Mais simples | Quebra em sistemas com locale pt-BR (`~/Área de Trabalho`) |

**Decisão: A.** `subprocess.run(['xdg-user-dir', 'DESKTOP'], capture_output=True, text=True)`. Se falhar, parseia `~/.config/user-dirs.dirs` por `XDG_DESKTOP_DIR`. Se ambos falharem, `~/Desktop`.

### 3. Local do ícone no atalho

| Alternativa | Prós | Contras |
|---|---|---|
| **A. Copiar para `~/.local/share/icons/b3-selic-pre.png` + referência absoluta** | Estável mesmo se projeto for movido; não precisa de cache de ícones | Ocupa ~50KB no disco do usuário |
| B. Referência direta ao ícone no projeto (`_SCRIPT_DIR/icons/b3_selic_pre.png`) | Zero cópia | Frágil — quebra se o projeto for movido |

**Decisão: A.** Copiar o PNG para `~/.local/share/icons/b3-selic-pre.png` e referenciar com caminho absoluto no `.desktop`.

### 4. Botão na GUI: posição e lógica

O botão "Criar Atalho Desktop" fica no **top_frame**, empacotado à direita (`side=tk.RIGHT`). A verificação de existência (`shortcut_exists()`) ocorre no `__init__` do `SelicPreApp`. Se já existir, o botão não é criado. Ao clicar, chama `create_shortcut()` e destrói o botão.

## Risks / Trade-offs

- **Caminho do executável muda se o projeto for movido**: O atalho aponta para o local atual. Se o usuário mover o projeto, o atalho quebra. Mitigação: documentado no código que o atalho deve ser recriado após mover, e o botão na GUI reaparecerá se o `.desktop` em `~/.local/share/applications/` não for encontrado.
- **`xdg-user-dir` pode não estar instalado**: Sistemas mínimos (Docker, WSL) podem não tê-lo. O fallback para `~/.config/user-dirs.dirs` cobre a maioria dos casos, e o fallback final `~/Desktop` cobre o resto.
- **PyInstaller em modo `--onefile`**: O `sys.executable` é o próprio binário extraído. O ícone em `sys._MEIPASS` está disponível durante execução. A cópia do ícone é feita na hora da criação do atalho, então o `_MEIPASS` estará acessível.
- **Permissão de escrita**: Se `~/.local/share/applications/` ou `~/Desktop` não forem graváveis (raro), o `create_shortcut()` lançará um `PermissionError`. O usuário verá a mensagem de erro no status bar ou no terminal.
