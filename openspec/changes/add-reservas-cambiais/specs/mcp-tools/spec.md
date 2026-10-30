# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo de tools somente leitura

O servidor SHALL expor as tools `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas`, `listar_datas`, `tesouro_vendas`, `tesouro_resgates`, `tesouro_estoque`, `mercado_serie`, `mercado_previsao`, `mercado_indicadores`, `mercado_exportar`, `reservas_serie`, `reservas_indicadores` e `reservas_exportar`.

Todas as tools SHALL ser somente leitura e SHALL declarar `readOnlyHint` verdadeiro, `openWorldHint` falso e `idempotentHint` verdadeiro.

O catálogo NÃO SHALL incluir tools de log, de metadados de log, de atualização, de download ou de escrita de arquivos.

#### Scenario: Catálogo lista exatamente as tools previstas

- **WHEN** o cliente lista as tools
- **THEN** o catálogo SHALL conter as tools previstas neste catálogo
- **THEN** nenhuma tool de log, atualização, download ou escrita SHALL estar presente

#### Scenario: Tools são anunciadas como somente leitura

- **WHEN** o cliente inspeciona uma tool
- **THEN** as anotações SHALL indicar leitura somente e ausência de acesso ao mundo externo

## ADDED Requirements

### Requirement: Tool reservas_serie

A tool `reservas_serie` SHALL aceitar `inicio`, `fim`, `janela` (`12m` ou `3a`), `cursor` e `limite` opcionais.

A tool SHALL ler apenas o cache local e devolver itens com data, valor em US$ milhões, unidade, origem, método, horário de extração e indicador de defasagem. A resposta SHALL incluir `nextCursor` quando houver continuação.

#### Scenario: Série de reservas

- **WHEN** o cliente chama `reservas_serie` para uma janela em cache
- **THEN** a resposta SHALL conter os pontos da janela
- **THEN** cada item SHALL conter valor, unidade e origem

#### Scenario: Janela de três anos

- **WHEN** o cliente chama `reservas_serie` com `janela=3a`
- **THEN** a resposta SHALL cobrir até 36 meses anteriores à maior data em cache

#### Scenario: Paginação

- **WHEN** há mais itens do que o limite
- **THEN** a resposta SHALL incluir `nextCursor`

#### Scenario: Sem dados

- **WHEN** não há série em cache para a janela
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`
- **THEN** a tool NÃO SHALL acessar a rede

### Requirement: Tool reservas_indicadores

A tool `reservas_indicadores` SHALL devolver nível atual, variações de 1, 3 e 12 meses, tendência de 90 dias, drawdown de 12 meses, posição na faixa de 12 meses, regime e limiares usados.

A tool SHALL ler apenas o cache local e SHALL omitir métricas cujos insumos não estejam disponíveis.

#### Scenario: Indicadores disponíveis

- **WHEN** há dados suficientes em cache
- **THEN** a resposta SHALL conter os indicadores calculados
- **THEN** o regime SHALL ser `aumento`, `estavel` ou `deterioracao`

#### Scenario: Métrica indisponível

- **WHEN** falta histórico para uma métrica
- **THEN** apenas essa métrica SHALL ser omitida
- **THEN** as demais SHALL ser devolvidas

#### Scenario: Sem dados

- **WHEN** não há dados em cache
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`

### Requirement: Tool reservas_exportar

A tool `reservas_exportar` SHALL aceitar `inicio`, `fim`, `janela` e `formato` (`csv` ou `json`).

A tool SHALL devolver o conteúdo, o nome sugerido, o tipo de conteúdo e a lista de datas indisponíveis, sem gravar arquivos. A tool SHALL ler apenas o cache local.

#### Scenario: Exportação CSV

- **WHEN** o cliente chama `reservas_exportar` com `formato=csv`
- **THEN** a resposta SHALL conter CSV com delimitador `;`
- **THEN** o nome sugerido SHALL ser `reservas-serie.csv`

#### Scenario: Exportação JSON

- **WHEN** o cliente chama `reservas_exportar` com `formato=json`
- **THEN** a resposta SHALL conter série e indicadores
- **THEN** o nome sugerido SHALL ser `reservas.json`

#### Scenario: Datas indisponíveis

- **WHEN** parte da janela não possui dados
- **THEN** a resposta SHALL listar as datas indisponíveis
- **THEN** os dados disponíveis SHALL ser devolvidos

#### Scenario: Sem dados

- **WHEN** não há dados para a janela
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`
