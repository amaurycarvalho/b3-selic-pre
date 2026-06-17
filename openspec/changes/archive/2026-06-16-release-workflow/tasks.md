## 1. CHANGELOG.md

- [x] 1.1 Create `CHANGELOG.md` na raiz com formato Keep a Changelog, seção `[Unreleased]`

## 2. .spec do PyInstaller

- [x] 2.1 Criar `b3-selic-pre.spec` na raiz com configuração completa: `--onefile`, `--name b3-selic-pre`, `--add-data b3_selic_pre.png:.`, `--hidden-import tkinter`, `--hidden-import PIL`, `--hidden-import matplotlib.backends.backend_tkagg`, `--hidden-import ctypes`, entry point `b3_selic_pre.py`

## 3. Workflow de Release

- [x] 3.1 Criar `.github/workflows/release.yml` com trigger em `push: tags: ['v*']` e `workflow_dispatch`
- [x] 3.2 Configurar job `build` com matrix `os: [ubuntu-latest, windows-latest, macos-latest]` e artifact naming por OS
- [x] 3.3 Adicionar step de instalação de dependências de sistema no Linux (`apt install python3-tk`)
- [x] 3.4 Adicionar step de instalação de dependências Python (`pip install -r requirements.txt pyinstaller`)
- [x] 3.5 Adicionar step de build com PyInstaller usando o `.spec` versionado e `MPLBACKEND=Agg`
- [x] 3.6 Adicionar step de upload de artefato (`actions/upload-artifact@v4`)
- [x] 3.7 Configurar job `release` com `needs: build`, download de artefatos e criação de GitHub Release (`softprops/action-gh-release@v2`) incluindo os binários e o `b3-selic-pre.desktop`
- [x] 3.8 Garantir que o release só seja criado se todos os builds da matrix forem bem-sucedidos

## 4. Verificação

- [ ] 4.1 Testar workflow manualmente via `workflow_dispatch` e confirmar que os 3 binários são gerados (requer push ao GitHub)
- [ ] 4.2 Verificar que os binários iniciam sem erro (`--help` e `--gui`) (requer download dos artefatos)
- [ ] 4.3 Verificar que o `.desktop` é incluído no release do Linux (requer execução do workflow no GitHub)
