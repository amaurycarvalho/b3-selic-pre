# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3

## Instalação

```bash
pip install -r requirements.txt
```

Requisitos:

- Python 3.10+.
- matplotlib e Pillow (veja `requirements.txt`).

## Como usar

### Linha de comando

Consultar a data atual:

```bash
python3 b3_selic_pre.py
```

Consultar uma data específica:

```bash
python3 b3_selic_pre.py 2026-06-10
```

Exibir taxas consolidadas por ano (mínima e máxima de cada ano):

```bash
python3 b3_selic_pre.py 2026-06-10 --yearly
```

### Interface desktop

Abrir a GUI com campo de data, gráfico de linha, zoom/pan, cópia para área de
transferência e exportação PNG:

```bash
python3 b3_selic_pre.py --gui
```

Na interface, informe a data no formato `YYYY-MM-DD` e clique em `Buscar`.
Marque **Consolidar por ano** para alternar entre a curva completa (DU252 ×
TAXA, linhas a cada 20 dias) e a visualização anual consolidada (taxa mínima
em azul, máxima em vermelho).

### Testes

Executar os testes focados nas funções de payload, validação, normalização e
exportação:

```bash
python3 -m unittest discover -s tests
```

## Saiba mais

- [Repositório do projeto](https://github.com/amaurycarvalho/b3-selic-pre);
- [Taxas referenciais na B3 - Selic x pré](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-de-derivativos/precos-referenciais/taxas-referenciais-bm-fbovespa/);
- [OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md).
