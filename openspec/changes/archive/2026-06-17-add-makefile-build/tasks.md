## 1. Makefile

- [x] 1.1 Criar `Makefile` na raiz com target `install` (cria `.venv/` e instala requirements.txt + pyinstaller via .venv/bin/pip)
- [x] 1.2 Criar target `build` com dependência em `install` (pyinstaller b3-selic-pre.spec com MPLBACKEND=Agg)
- [x] 1.3 Criar target `clean` (rm -rf dist/ build/ __pycache__/)

## 2. Workflow

- [x] 2.1 Substituir passo "Install Python dependencies" em release.yml por `make install`
- [x] 2.2 Substituir passo "Build with PyInstaller" em release.yml por `make build`

## 3. Correções de runtime

- [x] 3.1 Adicionar `PIL._tkinter_finder`, `matplotlib` e `matplotlib.figure` aos hidden imports do `b3-selic-pre.spec`
- [x] 3.2 Substituir `copy_chart` (threads + xclip/ctypes/osascript) por `pyxclip` — síncrono, cross-platform, sem dependências externas
- [x] 3.3 Adicionar `pyxclip>=0.2.0` ao `requirements.txt`
- [x] 3.4 Adicionar `pyxclip` aos hidden imports do `b3-selic-pre.spec`

## 4. Versionamento e docs

- [x] 4.1 Alterar `__version__` em `b3_selic_pre.py` de `"0.2.2"` para `"0.2.3"`
- [x] 4.2 Adicionar entrada unreleased no `CHANGELOG.md` documentando Makefile, workflow e bump
- [x] 4.3 Atualizar `README.md` com instruções de instalação (manual, Makefile, binário pré-compilado) e uso nas três modalidades

## 5. Verificação

- [x] 5.1 Executar `make install && make build` localmente e confirmar que o executável é gerado em `dist/`
- [x] 5.2 Executar `make clean` e confirmar que diretórios de build são removidos
