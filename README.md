# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3.

[![Spec-Driven Development](https://img.shields.io/badge/SDD-OpenSpec-yellow)](openspec/specs/project-constitution/spec.md)

---

## 🧑‍💻 Para Usuários

### Como Instalar

Baixe o binário da plataforma desejada na [página de releases](https://github.com/amaurycarvalho/b3-selic-pre/releases):

| Plataforma | Arquivo                    |
| ---------- | -------------------------- |
| Linux      | `b3-selic-pre-linux`       |
| Windows    | `b3-selic-pre-windows.exe` |
| macOS      | `b3-selic-pre-macos`       |

### Como Usar

Substitua `b3-selic-pre-linux` pelo nome do arquivo da sua plataforma.

```bash
./b3-selic-pre-linux                              # interface gráfica
./b3-selic-pre-linux gui                          # interface gráfica
./b3-selic-pre-linux consultar --data 2026-06-10  # curva curta
./b3-selic-pre-linux consultar --data 2026-06-10 --curva longa
./b3-selic-pre-linux atualizar --data 2026-06-10   # carrega evolução e análise
./b3-selic-pre-linux exportar --curva ambas --analise --saida exports/
./b3-selic-pre-linux tesouro --titulo Selic --agregar
./b3-selic-pre-linux tesouro --json --saida exports/
./b3-selic-pre-linux criar-atalho                  # criar atalho no desktop (Linux)
./b3-selic-pre-linux --help                       # exibir ajuda
./b3-selic-pre-linux --version                    # exibir versão
```

### Linha de Comando

A CLI usa subcomandos de verbo. Os principais são:

| Comando | Uso |
| --- | --- |
| `consultar` | Consulta as taxas de uma data (`--curva curta\|longa\|ambas`). |
| `atualizar` | Carrega a evolução da curva e imprime a análise determinística. |
| `exportar` | Exporta curvas, análise e/ou log da aplicação. |
| `tesouro` | Consulta vendas do Tesouro Direto (`--titulo`, `--inicio`, `--fim`, `--agregar`, `--json`, `--no-cache`, `--saida`). |
| `mcp` | Inicia o servidor MCP via `stdio`, somente leitura. |
| `gui` | Abre a interface gráfica (também é o padrão sem argumentos). |
| `criar-atalho` | Cria o atalho no desktop e no menu de aplicações. |

Parâmetros comuns: `--data AAAA-MM-DD` (padrão: hoje), `--no-cache` e
`--curva curta|longa|ambas`. A sintaxe antiga (`--today`, `--yearly`, `--gui`,
`--create-shortcut` e data posicional) foi removida.

O subcomando `tesouro` consulta as vendas do Tesouro Direto com filtros por
título e período, agregação por título, saída CSV/JSON e exportação via
`--saida`. Por padrão, usa os últimos 30 dias até a maior data de liquidação
disponível e mantém um cache cumulativo do CSV em
`$XDG_CACHE_HOME/b3-selic-pre/tesouro/`.

Consulte [Linha de Comando (CLI)](docs/misc/cli.md) para parâmetros, formatos de
exportação, regras de `--saida`, validação de data, logging e códigos de retorno.

### Servidor MCP

O comando `b3-selic-pre mcp` inicia um servidor MCP via `stdio`, somente
leitura, para agentes externos consultarem a curva, a evolução, a análise e as
estatísticas usando o cache local.

```bash
./b3-selic-pre-linux mcp                 # atende usando o cache existente
./b3-selic-pre-linux mcp --atualizar     # carrega hoje antes de atender
./b3-selic-pre-linux mcp --data 2026-06-10
```

Durante o atendimento o servidor não acessa a B3/CVM e não grava estado. Ele
expõe as tools `data_referencia`, `consultar_curva`, `exportar_curva_curta`,
`exportar_curva_longa`, `analise`, `evolucao`, `estatisticas`, `listar_datas` e
`tesouro_vendas`. A tool de Tesouro lê apenas o cache local; prepare-o antes com
`b3-selic-pre tesouro`. Detalhes de protocolo, tools e execução em Docker estão
em [Servidor MCP](docs/misc/mcp.md).

### Interface Gráfica

Vide a [documentação](docs/misc/panels.md) da interface, com indicadores e parametrizações disponíveis.

---

## 👨‍🔧 Para Desenvolvedores

### Como Instalar

#### Baixando o codigo fonte

```bash
git clone https://github.com/amaurycarvalho/b3-selic-pre.git
```

#### Como Compilar

```bash
make install   # cria .venv/ e instala dependências
make build     # gera executável em dist/
```

O executável será gerado em `dist/b3-selic-pre` (Linux), `dist/b3-selic-pre.exe` (Windows) ou `dist/b3-selic-pre` (macOS).

Requisitos:

- Python 3.10+
- matplotlib, Pillow e pyxclip

#### Linting e Testes Unitários

```bash
make lint test
```

#### Quality Gate

O _quality gate_ impõe limites para complexidade, duplicação, cobertura, mutação e segurança (RFC-002).

Execute-o localmente com:

```bash
make quality-gate
```

Verificações individuais: `make complexity`, `make duplication`, `make mutation-check`,
`make security`. Saiba mais em [Quality Gate](docs/adrs/ADR-002.md).

### Mutation testing

Garanta que tudo esteja instalado:

```bash
make install-quality-tools
```

Execute-o localmente (isso pode levar muito tempo e exigir processamento significativo):

```bash
make mutation-run
```

Em seguida, gere o relatório de resultados e utilize-o com seu agente de IA para corrigir seus testes unitários:

```bash
make mutation-results
```

Por fim, execute novamente os testes de mutação e verifique se eles passam pelo _quality gate_.

### Como Usar

#### A partir do código fonte

Via o binário após `make build`:

```bash
.venv/bin/b3-selic-pre                              # interface gráfica
.venv/bin/b3-selic-pre gui                          # interface gráfica
.venv/bin/b3-selic-pre consultar --data 2026-06-10  # curva curta
.venv/bin/b3-selic-pre consultar --data 2026-06-10 --curva longa
.venv/bin/b3-selic-pre atualizar --data 2026-06-10   # evolução + análise
.venv/bin/b3-selic-pre exportar --curva ambas --analise --saida exports/
.venv/bin/b3-selic-pre criar-atalho                  # criar atalho no desktop (Linux)
.venv/bin/b3-selic-pre --help                        # exibir ajuda
.venv/bin/b3-selic-pre --version                     # exibir versão
```

Ou via módulo Python:

```bash
.venv/bin/python3 -m b3_selic_pre                     # interface gráfica
.venv/bin/python3 -m b3_selic_pre consultar --data 2026-06-10
```

#### A partir do executável gerado pelo Makefile

```bash
dist/b3-selic-pre                              # interface gráfica
dist/b3-selic-pre gui                          # interface gráfica
dist/b3-selic-pre consultar --data 2026-06-10  # curva curta
dist/b3-selic-pre consultar --data 2026-06-10 --curva longa
dist/b3-selic-pre atualizar --data 2026-06-10   # evolução + análise
dist/b3-selic-pre exportar --curva ambas --analise --saida exports/
dist/b3-selic-pre criar-atalho                  # criar atalho no desktop (Linux)
dist/b3-selic-pre --help                        # exibir ajuda
dist/b3-selic-pre --version                     # exibir versão
```

---

## Fontes de Dados

A aplicação consulta apenas os endpoints do portal de derivativos da B3
(`GetList` e `GetDownloadFile`), sem autenticação nem telemetria. URLs, payloads,
paginação, retry, cache e riscos estão documentados em
[Fontes de dados externas](docs/misc/datasources.md).

## Saiba Mais

- [Repositório do projeto](https://github.com/amaurycarvalho/b3-selic-pre)
- [Releases com binários pré-compilados](https://github.com/amaurycarvalho/b3-selic-pre/releases)
- [Taxas referenciais na B3 - Selic x pré](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-de-derivativos/precos-referenciais/taxas-referenciais-bm-fbovespa/)
