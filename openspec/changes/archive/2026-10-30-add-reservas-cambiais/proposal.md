# Proposal

## Why

O aplicativo acompanha SELIC Pré e Tesouro Direto, e a change `add-cambio-ouro-forecast` trará a leitura de câmbio e ouro. Falta a peça central do colchão externo: a evolução do estoque de reservas internacionais brasileiras em dólares. Sem ela, não é possível distinguir melhora de fluxo cambial de deterioração das reservas.

## What Changes

- Nova sub-aba `Reservas Internacionais` dentro da aba `Câmbio e Ouro`, lazy, com `Atualizar` próprio e carregamento inicial apenas do cache.
- Série diária do BCB SGS 13621 (reservas internacionais, conceito de liquidez, US$ milhões), com janela padrão de 12 meses e opção de 3 anos.
- Cache reutilizando o core de `add-cambio-ouro-forecast`: snapshot bruto normalizado por fonte, hash canônico dos pares `(data, valor)`, busca incremental com overlap de revisões, TTL por recência e escrita atômica.
- Pré-cálculo invalidado pelo hash da matriz de origem e pelos parâmetros, disparado pelo `Atualizar` da sub-aba; falha preserva o artefato anterior.
- Housekeeping de 3 anos ancorado na maior data disponível, com o hash calculado sobre a janela retida para a limpeza não invalidar o pré-cálculo.
- Indicadores determinísticos de direção: nível atual, variações de 1/3/12 meses, tendência de 90 dias, drawdown de 12 meses, posição na faixa de 12 meses e regime `aumento | estavel | deterioracao`, com limiares configuráveis.
- Gráfico de linha/área com seletor de janela, médias móveis, selo de regime e proveniência/defasagem.
- Exportação via CLI no subcomando `reservas` (CSV/JSON) e tools MCP somente leitura: `reservas_serie`, `reservas_indicadores` e `reservas_exportar`.
- Reuso das estruturas de `add-cambio-ouro-forecast` (`BcbSgsClient`, `SourceRef`, `MarketSeries`, `Bucket`, precompute, housekeeping e regras de `--saida`), sem novas dependências de terceiros.

## Capabilities

### New Capabilities

- `reservas-cambiais`: série histórica das reservas internacionais, cache derivado e pré-cálculo, indicadores de deterioração, dados de gráfico e payloads de exportação.

### Modified Capabilities

- `app-tabs`: registrar a sub-aba `Reservas Internacionais` no sub-notebook de `Câmbio e Ouro`, com construção lazy e `Atualizar` próprio.
- `cli-interface`: adicionar o subcomando `reservas` com filtros de janela, formatos CSV/JSON, `--saida`, `--atualizar` e `--no-cache`.
- `mcp-tools`: adicionar as tools `reservas_serie`, `reservas_indicadores` e `reservas_exportar` ao catálogo somente leitura.
- `market-data-cache`: estender o cache de mercado para aceitar snapshot normalizado por fonte e hash canônico da janela retida, sem alterar o comportamento de dólar e ouro.

## Impact

- Novos módulos em `domain`, `application`, `infrastructure` e `presentation`, respeitando as fronteiras de camada e o composition root da CLI/GUI.
- Nova sub-aba no sub-notebook de `Câmbio e Ouro`, novo subcomando na CLI, novas tools no catálogo MCP e novos artefatos sob o cache XDG de mercado.
- Depende de `add-cambio-ouro-forecast` implementado e arquivado antes desta change, porque reutiliza seu cliente BCB, cache, pré-cálculo, housekeeping e helpers de exportação.
- Testes headless para série, indicadores, cache, pré-cálculo e payloads; nenhum aumento do orçamento de testes de UI.
- Nenhuma mudança destrutiva nas abas, comandos ou tools existentes.
