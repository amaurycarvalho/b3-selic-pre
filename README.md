# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3

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

| Plataforma | Arquivo |
|------------|---------|
| Linux | `b3-selic-pre-linux` |
| Windows | `b3-selic-pre-windows.exe` |
| macOS | `b3-selic-pre-macos` |

## Como usar

### A partir do código fonte

```bash
b3-selic-pre                              # consultar data atual
b3-selic-pre 2026-06-10                   # data específica
b3-selic-pre 2026-06-10 --yearly          # consolidado por ano
b3-selic-pre --gui                        # interface gráfica
b3-selic-pre --create-shortcut            # criar atalho no desktop (Linux)
b3-selic-pre --help                       # exibir ajuda com todos os parâmetros
b3-selic-pre --version                    # exibir versão
```

Ou via módulo Python:

```bash
python3 -m b3_selic_pre                   # consultar data atual
python3 -m b3_selic_pre --gui             # interface gráfica
```

### A partir do executável gerado pelo Makefile

```bash
dist/b3-selic-pre                           # consultar data atual
dist/b3-selic-pre 2026-06-10                # data específica
dist/b3-selic-pre 2026-06-10 --yearly       # consolidado por ano
dist/b3-selic-pre --gui                     # interface gráfica
dist/b3-selic-pre --create-shortcut         # criar atalho no desktop (Linux)
dist/b3-selic-pre --help                    # exibir ajuda com todos os parâmetros
dist/b3-selic-pre --version                 # exibir versão
```

### A partir do binário pré-compilado

```bash
./b3-selic-pre-linux                        # consultar data atual
./b3-selic-pre-linux 2026-06-10             # data específica
./b3-selic-pre-linux 2026-06-10 --yearly    # consolidado por ano
./b3-selic-pre-linux --gui                  # interface gráfica
./b3-selic-pre-linux --create-shortcut      # criar atalho no desktop (Linux)
./b3-selic-pre-linux --help                 # exibir ajuda com todos os parâmetros
./b3-selic-pre-linux --version              # exibir versão
```

Substitua `b3-selic-pre-linux` pelo nome do arquivo da sua plataforma.

### Interface desktop

#### Modos de visualização

Dois modos base selecionáveis por radio button, com opção adicional de evolução:

| Modo | Descrição |
|------|-----------|
| **Detalhado** | Curva completa Dias úteis × taxa (linha verde), com grid trimestral (~66 DU) e ticks finos a cada ~22 DU |
| **Consolidado** | Envelope anual consolidado (taxa mínima em azul, máxima em vermelho), com grid trienal (3 anos) e ticks finos a cada ano |
| **Evolução da curva** ☐ | Checkbox que sobrepõe 5 curvas históricas (hoje, 7, 14, 21, 28 dias atrás) com gradiente de cor e flechas quiver nos ticks secundários (~22 DU / ~1 ano), combinável com qualquer modo base |

Na interface, informe a data no formato `YYYY-MM-DD` e clique em `Buscar`.
Use o botão `📅` ao lado do campo de data para abrir um calendário popup.

**Limite de consulta**: nos modos Detalhado e Consolidado, apenas datas nos últimos 30 dias corridos são aceitas.

**Evolução da curva**: ao marcar o checkbox, a data é automaticamente alterada para a data atual. O sistema busca as 5 curvas (28, 21, 14, 7, 0 dias atrás) em paralelo e as sobrepõe ao gráfico do modo base ativo.

Recursos disponíveis:
- Zoom e pan no gráfico
- Cópia de dados para área de transferência
- Cópia do gráfico como imagem
- Exportação do gráfico em PNG
- Criação de atalho no desktop (botão "Criar Atalho Desktop" ou `--create-shortcut`)

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
