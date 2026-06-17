## Why

O projeto `b3-selic-pre` é uma aplicação desktop Python (tkinter + matplotlib) que consulta taxas SELIC Pré na B3. Atualmente só roda via `python b3_selic_pre.py`, exigindo que o usuário tenha Python e dependências instaladas. Um workflow de release com PyInstaller permite distribuir binários prontos para Windows, Linux e macOS — qualquer pessoa baixa e executa sem setup.

## What Changes

- Criar workflow GitHub Actions que gera executáveis com PyInstaller para Windows, Linux e macOS
- Publicar os binários como assets de uma GitHub Release
- Adicionar arquivo `.spec` versionado do PyInstaller
- Incluir o arquivo `b3-selic-pre.desktop` no release do Linux
- Adicionar `CHANGELOG.md` para registrar versões
- Disparar o workflow via push de tag `v*` ou manualmente (`workflow_dispatch`)
- Executáveis em formato `--onefile` (único arquivo)

## Capabilities

### New Capabilities
- `release-automation`: Pipeline de build, empacotamento e publicação de releases para Windows, Linux e macOS via GitHub Actions

### Modified Capabilities
<!-- Nenhuma capability existente é modificada — é uma adição nova, sem alterar requisitos das existentes -->

## Impact

- Novo diretório `.github/workflows/release.yml`
- Novo arquivo `b3-selic-pre.spec` na raiz do projeto
- Novo arquivo `CHANGELOG.md` na raiz do projeto
- Dependência de build: `pyinstaller` (apenas no CI, não em runtime)
- CI existente (`test.yml`) não é alterado
