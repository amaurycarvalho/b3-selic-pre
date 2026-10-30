## MODIFIED Requirements

### Requirement: Catálogo de tools somente leitura

O servidor SHALL expor as tools `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas`, `listar_datas` e `tesouro_vendas`.

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

### Requirement: Tool tesouro_vendas

A tool `tesouro_vendas` SHALL aceitar `titulo`, `inicio`, `fim`, `agregar`, `cursor` e `limite` opcionais. Ela SHALL ler apenas o cache local de vendas, sem rede, download ou escrita de arquivos.

A resposta SHALL conter `dataset: "vendas"`, `origem: "cache"`, `data_extracao`, `publicado_em`, `data_maxima_liquidacao`, `total_registros`, `periodo`, `registros` ou `agregados`, `total_agregados` quando agregada, e `nextCursor` quando houver continuação.

#### Scenario: Resposta estruturada

- **WHEN** o cliente chama `tesouro_vendas`
- **THEN** a resposta SHALL conter os metadados do dataset e `registros` ou `agregados`
- **THEN** a origem SHALL ser `cache`

### Requirement: Filtros e agregação da tool tesouro_vendas

Sem datas, o período SHALL ser de 30 dias até a maior `data_liquidacao`. `titulo` SHALL ser parcial, sem caixa/acentos; `inicio`/`fim` SHALL ser inclusivos em `AAAA-MM-DD`; `agregar` SHALL agrupar por título.

#### Scenario: Consulta com filtros

- **WHEN** o cliente chama `tesouro_vendas` com `titulo` e `inicio`/`fim`
- **THEN** a resposta SHALL conter apenas as vendas correspondentes
- **THEN** cada registro SHALL conter título, vencimento, data de liquidação, PU, quantidade e valor

#### Scenario: Período padrão

- **WHEN** o cliente chama `tesouro_vendas` sem `inicio` e `fim`
- **THEN** a resposta SHALL cobrir os últimos 30 dias até a maior `data_liquidacao`

#### Scenario: Agregação por título

- **WHEN** o cliente chama `tesouro_vendas` com `agregar=true`
- **THEN** a resposta SHALL conter `agregados` com `quantidade` e `valor` somados por título
- **THEN** `PU_MEDIO` SHALL ser `valor_total / quantidade_total`

#### Scenario: Paginação

- **WHEN** há mais registros do que `limite`
- **THEN** a resposta SHALL incluir `nextCursor`
- **THEN** o cliente SHALL poder continuar a partir do cursor

#### Scenario: Cache vazio

- **WHEN** não há cache de vendas
- **THEN** a tool SHALL devolver erro de domínio `cache_vazio`
- **THEN** a dica SHALL indicar o subcomando `tesouro` para preparar o cache

#### Scenario: Período sem registros

- **WHEN** o filtro não encontra vendas
- **THEN** a resposta SHALL conter `registros: []`
- **THEN** `total_registros` SHALL ser `0`
- **THEN** a tool NÃO SHALL acessar a rede

#### Scenario: Cursor inválido

- **WHEN** o cliente envia um cursor inválido
- **THEN** o servidor SHALL responder com código `-32602`
