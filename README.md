# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3

## Instalação

Este projeto usa apenas a biblioteca padrão do Python para a consulta e para a
interface desktop inicial.

Requisito:

- Python 3.10+ recomendado.

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

### Interface desktop

Abrir a GUI com campo de data, tabela de resultados, cópia para área de
transferência e exportação CSV:

```bash
python3 b3_selic_pre.py --gui
```

Na interface, informe a data no formato `YYYY-MM-DD` e clique em `Buscar`.

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
