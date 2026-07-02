# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3.

[![Spec-Driven Development](https://img.shields.io/badge/SDD-OpenSpec-yellow)](openspec/specs/project-constitution/spec.md)

## Instalação

### 1. Via PyPI (código fonte)

```bash
pip install .
```

Requisitos:

- Python 3.10+
- matplotlib, Pillow e pyxclip

### 2. Via Makefile (build local)

```bash
make install   # cria .venv/ e instala dependências
make build     # gera executável em dist/
```

O executável será gerado em `dist/b3-selic-pre` (Linux), `dist/b3-selic-pre.exe` (Windows) ou `dist/b3-selic-pre` (macOS).

### 3. Binário pré-compilado

Baixe o binário da plataforma desejada na [página de releases](https://github.com/amaurycarvalho/b3-selic-pre/releases):

| Plataforma | Arquivo                    |
| ---------- | -------------------------- |
| Linux      | `b3-selic-pre-linux`       |
| Windows    | `b3-selic-pre-windows.exe` |
| macOS      | `b3-selic-pre-macos`       |

## Como usar

### A partir do código fonte

Via o binário após `make build`:

```bash
.venv/bin/b3-selic-pre --today                      # consultar data atual
.venv/bin/b3-selic-pre 2026-06-10                   # data específica
.venv/bin/b3-selic-pre 2026-06-10 --yearly          # consolidado por ano
.venv/bin/b3-selic-pre --gui                        # interface gráfica
.venv/bin/b3-selic-pre --create-shortcut            # criar atalho no desktop (Linux)
.venv/bin/b3-selic-pre --help                       # exibir ajuda com todos os parâmetros
.venv/bin/b3-selic-pre --version                    # exibir versão
```

Ou via módulo Python:

```bash
.venv/bin/python3 -m b3_selic_pre --today           # consultar data atual
.venv/bin/python3 -m b3_selic_pre --gui             # interface gráfica
```

### A partir do executável gerado pelo Makefile

```bash
dist/b3-selic-pre --today                   # consultar data atual
dist/b3-selic-pre 2026-06-10                # data específica
dist/b3-selic-pre 2026-06-10 --yearly       # consolidado por ano
dist/b3-selic-pre --gui                     # interface gráfica
dist/b3-selic-pre --create-shortcut         # criar atalho no desktop (Linux)
dist/b3-selic-pre --help                    # exibir ajuda com todos os parâmetros
dist/b3-selic-pre --version                 # exibir versão
```

### A partir do binário pré-compilado do repositório

```bash
./b3-selic-pre-linux --today                # consultar data atual
./b3-selic-pre-linux 2026-06-10             # data específica
./b3-selic-pre-linux 2026-06-10 --yearly    # consolidado por ano
./b3-selic-pre-linux --gui                  # interface gráfica
./b3-selic-pre-linux --create-shortcut      # criar atalho no desktop (Linux)
./b3-selic-pre-linux --help                 # exibir ajuda com todos os parâmetros
./b3-selic-pre-linux --version              # exibir versão
```

Substitua `b3-selic-pre-linux` pelo nome do arquivo da sua plataforma.

### Interface gráfica

Vide a [documentação](panels.md) da interface, com indicadores e parametrizações disponíveis.

### Testes

#### Manual (via Makefile)

```bash
make test
```

#### CI (pytest)

```bash
pip install pytest
pytest
```

## Saiba mais

- [Repositório do projeto](https://github.com/amaurycarvalho/b3-selic-pre)
- [Releases com binários pré-compilados](https://github.com/amaurycarvalho/b3-selic-pre/releases)
- [Taxas referenciais na B3 - Selic x pré](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-de-derivativos/precos-referenciais/taxas-referenciais-bm-fbovespa/)
