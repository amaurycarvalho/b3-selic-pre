## Context

O build do PyInstaller está hardcoded no `.github/workflows/release.yml` com comandos inline. Não há um jeito padronizado de fazer build local. O Makefile resolve isso centralizando a instalação de dependências e o comando de build em targets reutilizáveis.

```
Estado atual:
  release.yml ──► pip install && pyinstaller (inline)

Estado desejado:
  release.yml ──► make install && make build ──► Makefile ──► .venv/ + pip install && pyinstaller
                   ▲                         ▲
           workflow só chama     lógica de build centralizada
           make targets          (uso local + CI)
```

## Goals / Non-Goals

**Goals:**
- Criar Makefile com targets `install` (cria `.venv` e instala dependências) e `build` (pyinstaller via `.venv/bin/pyinstaller`)
- Workflow de release usa `make install` + `make build`
- Bump de versão para 0.2.3
- `dist/` já está no `.gitignore` (verificado)

**Non-Goals:**
- NÃO mover instalação de dependências de sistema (python3-tk) para o Makefile — é específica do runner Linux
- NÃO mover renomeação do binário (`mv dist/b3-selic-pre* dist/$artifact_name`) — usa variável da matrix do GitHub Actions
- NÃO alterar lógica de publish/release
- NÃO adicionar linters ou formatação no Makefile

## Decisions

1. **Targets separados `install` e `build`** em vez de um target único `all`:
   - O CI precisa instalar deps de sistema entre `install` e `build`
   - `install` é um pré-requisito declarado do `build` no Makefile, mas o CI pode chamar separadamente se precisar
   - Alternativa considerada: target único que faz tudo. Rejeitada porque o CI precisa injetar passos (deps de sistema) entre install e build.

2. **`make install` cria `.venv/` local em vez de instalar system-wide**:
   - Sistemas Debian/Ubuntu modernos têm PEP 668 ativo, impedindo `pip install` fora de venv
   - O desenvolvedor pode ter pyinstaller via pipx, mas sem matplotlib/PIL disponíveis no mesmo ambiente
   - `.venv/` resolve ambos os problemas: ambiente isolado e autocontido
   - Alternativa considerada: `--break-system-packages`. Rejeitada por ser má prática e quebrar em CI.

3. **`make build` usa `.venv/bin/pyinstaller`**:
   - Garante que o pyinstaller correto (com hooks compatíveis) é usado
   - Evita conflito com pyinstaller do pipx ou system-wide

4. **`make build` não depende mais de `install` como prerequisite, mas de `.venv/`**:
   - `.venv/` é um target de ordem-only que, se não existir, roda `make install` automaticamente
   - Isso permite `make build` direto sem passo manual de `make install`

5. **Bump de versão e CHANGELOG incluídos na mesma change**:
   - São mudanças atômicas e superficiais que acompanham a release. Faz sentido agrupar.

6. **Uso do `pyxclip` para clipboard de imagens em vez de subprocessos + xclip/ctypes/osascript**:
   - `pyxclip` é uma extensão Rust (PyO3 + arboard) que acessa APIs nativas do SO diretamente — sem depender de `xclip`, `wl-copy`, `pbcopy` ou `pywin32`
   - Reduz ~80 linhas de código com branches por plataforma para 3 linhas: `pyxclip.copy((width, height, pixels))`
   - Elimina travamentos do `xclip` em ambientes sem DISPLAY (a exceção `ClipboardError` é capturada com fallback amigável)
   - Pre-built wheels disponíveis no PyPI para todas as plataformas (não requer Rust compiler)
   - Alternativa considerada: `pyperclipimg` (mesmo autor do pyperclip). Rejeitada porque no Linux ainda depende de `xclip`/`wl-copy` externamente.

## Risks / Trade-offs

- [Makefile não funciona no Windows] → O workflow usa runners Linux/macOS para build. O Makefile é usado apenas no CI (ubuntu-latest, macos-latest) e localmente em sistemas Unix. Builds Windows também rodam no CI via `make` disponível no runner windows-latest (GitHub Actions inclui make).
- [Manter dois lugares de verdade: Makefile e workflow] → O Makefile é a fonte única para build Python. O workflow só orquestra o ambiente (SO, deps de sistema, rename). Isso reduz duplicação, não aumenta.
- [`.venv/` não versionado] → `.venv/` já está no `.gitignore`. Cada desenvolvedor precisa rodar `make install` na primeira vez, o que é documentado no README.
- [Hidden imports do PyInstaller podem mudar entre versões] → Manter `b3-selic-pre.spec` versionado e testar o binário após upgrades de dependências.
