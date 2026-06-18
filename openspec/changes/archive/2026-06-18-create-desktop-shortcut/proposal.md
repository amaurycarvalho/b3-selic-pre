## Why

Ao rodar em modo GUI, usuários não têm um atalho no desktop para iniciar a aplicação rapidamente. O arquivo `.desktop` existe apenas no repositório e precisa ser copiado manualmente — isso reduz a usabilidade, especialmente para usuários não-técnicos.

## What Changes

- Adicionar função `create_shortcut()` que gera um `.desktop` compatível com FreeDesktop
- Adicionar parâmetro CLI `--create-shortcut` que cria o atalho e sai
- No modo GUI, detectar automaticamente se o atalho já existe; se não, mostrar botão "Criar Atalho Desktop" no top_frame
- Versão bumpada de `0.3.1` para `0.4.0`
- Nome do atalho: "Taxas Referenciais SELIC (B3)"
- Categoria Linux: `Finance;Office;`
- Ícone copiado para `~/.local/share/icons/` para referência estável
- `.desktop` instalado em `~/Desktop/` e `~/.local/share/applications/`

## Capabilities

### New Capabilities
- `shortcut-installer`: Criação programática de atalho desktop FreeDesktop, com detecção de executável (binário compilado ou script Python), resolução de ícone, detecção do diretório Desktop via XDG, e instalação nos locais padrão do sistema.

### Modified Capabilities
- `desktop-entry`: O spec existente será estendido com requirements sobre detecção de existência de atalho e criação programática via CLI e GUI.
- `app-icon`: O spec existente será estendido para cobrir a cópia do ícone para `~/.local/share/icons/` durante a instalação do atalho.

## Impact

- **Arquivo principal**: `b3_selic_pre.py` — adição de ~60-80 linhas (funções `create_shortcut`, `_resolve_executable`, `_icon_source`, `_detect_desktop_dir`, `shortcut_exists`; parâmetro CLI `--create-shortcut`; botão na GUI)
- **Dependências**: Nenhuma nova. Usa `os`, `shutil`, `subprocess` da stdlib
- **Testes**: `test_b3_selic_pre_gui.py` — novos testes para o botão e fluxo de criação
- **Specs**: `shortcut-installer` (novo), `desktop-entry` e `app-icon` (modificados)
