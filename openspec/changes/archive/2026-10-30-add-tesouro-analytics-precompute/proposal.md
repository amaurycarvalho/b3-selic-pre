## Why

A primeira exibição das sub-abas de `Tesouro Direto` ainda lê e reprocessa os CSVs brutos: o parse de vendas e resgates chega a ~15 s e a montagem dos gráficos de 3 anos a ~7 s. O cache analítico já existe em `infrastructure/tesouro_analytics_cache.py`, mas não tem consumidor em `src/`; a GUI atual contradiz a spec `tesouro-analise-gui`, que exige leitura apenas do cache analítico na primeira exibição.

## What Changes

- Pré-calcular séries normalizadas por fonte (`estoque`, `demanda` de vendas e `fluxo` de vendas menos resgates) após uma atualização bem-sucedida, de forma automática e fora da thread da UI.
- Guardar as séries no cache analítico existente, com escrita atômica, lock dedicado e retenção de 3 anos.
- Invalidar e recalcular apenas a fonte cujo CSV bruto mudou (`sha256`); resposta `304` ou conteúdo idêntico não reprocessa nada.
- Reutilizar os registros já parseados pelo refresh e agregar em uma passada em lote, sem reler o CSV logo em seguida.
- Fazer a GUI ler as séries pré-calculadas na primeira exibição e ao trocar de janela, sem parse de CSV e sem rede.
- Quando só houver cache bruto, montar as séries uma vez em background e persistir, preservando o comportamento atual sem exigir novo download.
- Manter o cache bruto e os comandos CLI atuais inalterados.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a camada analítica já está coberta por `tesouro-analise`. -->

### Modified Capabilities

- `tesouro-analise`: adicionar o pré-cálculo de séries normalizadas por fonte, sua invalidação por hash e a reutilização por todas as janelas.
- `tesouro-analise-gui`: mudar a leitura inicial e a troca de janela para consumir as séries pré-calculadas, com fallback único a partir do cache bruto.

## Impact

- `application/tesouro/`: agregação em lote das séries por fonte, sem importar UI, rede ou infraestrutura.
- `infrastructure/`: uso do cache analítico existente para snapshots de séries, com metadados por fonte.
- `presentation/`: loaders, controller e view-model passam a receber/consultar séries prontas; composição em `gui/launch.py`.
- Testes headless de pré-cálculo, invalidação, fallback, janelas e contrato do provider; teste de UI preservado no orçamento atual.
- Nenhuma dependência externa nova e nenhuma alteração no formato do cache bruto.
