# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3

## Instalação

### 1. Manual (código fonte)

```bash
pip install -r requirements.txt
```

Requisitos:
- Python 3.10+
- matplotlib, Pillow e pyxclip (veja `requirements.txt`)

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
python3 b3_selic_pre.py                     # consultar data atual
python3 b3_selic_pre.py 2026-06-10          # data específica
python3 b3_selic_pre.py 2026-06-10 --yearly # consolidado por ano
python3 b3_selic_pre.py --gui               # interface gráfica
python3 b3_selic_pre.py --version           # exibir versão
```

### A partir do executável gerado pelo Makefile

```bash
dist/b3-selic-pre                           # consultar data atual
dist/b3-selic-pre 2026-06-10                # data específica
dist/b3-selic-pre 2026-06-10 --yearly       # consolidado por ano
dist/b3-selic-pre --gui                     # interface gráfica
dist/b3-selic-pre --version                 # exibir versão
```

### A partir do binário pré-compilado

```bash
./b3-selic-pre-linux                        # consultar data atual
./b3-selic-pre-linux 2026-06-10             # data específica
./b3-selic-pre-linux 2026-06-10 --yearly    # consolidado por ano
./b3-selic-pre-linux --gui                  # interface gráfica
./b3-selic-pre-linux --version              # exibir versão
```

Substitua `b3-selic-pre-linux` pelo nome do arquivo da sua plataforma.

### Interface desktop

Na interface, informe a data no formato `YYYY-MM-DD` e clique em `Buscar`.
Marque **Consolidar por ano** para alternar entre a curva completa (DU252 ×
TAXA, linhas a cada 20 dias) e a visualização anual consolidada (taxa mínima
em azul, máxima em vermelho).

Recursos disponíveis:
- Zoom e pan no gráfico
- Cópia de dados para área de transferência
- Cópia do gráfico como imagem
- Exportação do gráfico em PNG

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
