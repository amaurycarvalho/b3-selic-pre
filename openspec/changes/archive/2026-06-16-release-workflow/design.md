## Context

`b3-selic-pre` é uma aplicação Python single-file com interface gráfica (tkinter) e linha de comando. Atualmente distribuída apenas como código-fonte — usuário precisa clonar o repositório, instalar Python 3.10+ e dependências (`matplotlib`, `Pillow`).

O objetivo é automatizar a geração de executáveis via PyInstaller em um workflow GitHub Actions, publicando-os como assets de uma GitHub Release.

## Goals / Non-Goals

**Goals:**
- Workflow CI/CD que gere binários PyInstaller para Windows, Linux e macOS
- Executável no formato `--onefile` (único arquivo)
- Publicação automática como GitHub Release ao criar tag `v*`
- Disparo manual via `workflow_dispatch`
- Inclusão do `b3-selic-pre.desktop` no release Linux
- Arquivo `.spec` versionado para reprodutibilidade
- `CHANGELOG.md` com histórico de versões

**Non-Goals:**
- Assinatura de código (Authenticode, macOS codesign)
- Notarização macOS
- Build para outras arquiteturas (ARM, etc.)
- Publicação em lojas (Snap, Flatpak, Windows Store, Homebrew)
- Testes de regressão nos binários gerados

## Decisions

### 1. Matrix de OS runners (obrigatório)

PyInstaller não suporta cross-compilation. Cada binário deve ser gerado no SO alvo.

```
ubuntu-latest  →  b3-selic-pre-linux
windows-latest →  b3-selic-pre-windows.exe
macos-latest   →  b3-selic-pre-macos
```

**Alternativa considerada**: Docker + Wine para build Windows no Linux. Descartada por complexidade e fragilidade. Runners nativos são mais confiáveis.

### 2. `--onefile` vs `--onedir`

**Decisão: `--onefile`**. O usuário final recebe um único arquivo executável. Apesar de maior latência de inicialização (PyInstaller extrai em tmp) e tamanho maior (~30-50 MB), a simplicidade de distribuição compensa para este público.

### 3. Estrutura do workflow

Dois jobs em sequência:
- **build** (matrix 3 OS): instala dependências, roda PyInstaller, faz upload do artefato
- **release** (ubuntu, depende de build): baixa artefatos, cria GitHub Release com todos os binários

Separação clara entre build e publicação. Se o build falhar em um OS, os outros ainda sobem como artefatos, mas o release não é criado.

### 4. Trigger: push tag + dispatch manual

- Push de tag `v*` (ex: `v1.0.0`, `v2.3.1`) → release automático
- `workflow_dispatch` → permite release manual sem tag, útil para pré-releases

### 5. .spec versionado

O `.spec` do PyInstaller será versionado na raiz do projeto, permitindo:
- Reprodutibilidade de builds
- Alterações controladas via diff
- Parametrização de hidden imports, dados adicionais, etc.

### 6. Naming dos binários

Usar o nome da tag como versão. O workflow extrai o nome da tag com `github.ref_name` e nomeia os artefatos consistentemente.

### 7. CHANGELOG.md mantido manualmente

Sem automação de changelog. O desenvolvedor atualiza manualmente seguindo convenção de versionamento semântico. O workflow não extrai notas de release — o usuário as escreve na interface do GitHub Release.

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| **tkinter ausente no runner Linux** | Instalar `python3-tk` via apt antes do build |
| **matplotlib usa backend diferente no headless CI** | Forçar `MPLBACKEND=Agg` no workflow |
| **PyInstaller perde imports dinâmicos** | Mapear `--hidden-import` para tkinter, PIL, matplotlib.backends.backend_tkagg, ctypes |
| **Binário Linux precisa de xclip** | Documentar que função "Copiar gráfico" requer `xclip` instalado no sistema do usuário |
| **Windows Defender / antivírus falso-positivo** | Não mitigável sem assinatura; documentar que é esperado |
| **Tamanho do binário ~40 MB** | Aceitável para app desktop com matplotlib embutido |
