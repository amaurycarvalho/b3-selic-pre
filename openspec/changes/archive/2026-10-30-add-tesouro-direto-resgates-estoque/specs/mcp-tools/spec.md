## MODIFIED Requirements

### Requirement: Catálogo de tools somente leitura

O servidor SHALL expor as tools `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas`, `listar_datas`, `tesouro_vendas`, `tesouro_resgates` e `tesouro_estoque`.

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

### Requirement: Tool tesouro_resgates

A tool `tesouro_resgates` SHALL aceitar `tipo`, `titulo`, `inicio`, `fim`, `agregar`, `cursor` e `limite` opcionais. Ela SHALL ler apenas o cache local de resgates, sem rede, download ou escrita de arquivos.

A resposta SHALL conter `dataset: "resgates"`, `origem: "cache"`, `data_extracao`, `total_registros`, `periodo`, `registros` ou `agregados`, e `nextCursor` quando houver continuação.

#### Scenario: Resposta estruturada

- **WHEN** o cliente chama `tesouro_resgates`
- **THEN** a resposta SHALL conter os metadados do dataset e `registros` ou `agregados`
- **THEN** a origem SHALL ser `cache`

#### Scenario: Cache vazio

- **WHEN** não há cache de resgates
- **THEN** a tool SHALL devolver erro de domínio `cache_vazio`
- **THEN** a dica SHALL indicar o subcomando `tesouro-resgates` para preparar o cache

### Requirement: Filtros e agregação da tool tesouro_resgates

`tipo` SHALL filtrar `recompra`, `cupom` ou `vencimento`; sem ele, todos SHALL ser consultados. `titulo` SHALL ser parcial, sem caixa/acentos. `inicio`/`fim` SHALL ser inclusivos em `AAAA-MM-DD`.

Sem datas, o período SHALL ser de 30 dias até a maior `data_resgate`. `agregar` SHALL agrupar por tipo e título; `PU_MEDIO` SHALL ficar vazio para recompras.

#### Scenario: Consulta por tipo

- **WHEN** o cliente chama `tesouro_resgates` com `tipo="recompra"`
- **THEN** a resposta SHALL conter apenas recompras

#### Scenario: Período padrão

- **WHEN** o cliente chama `tesouro_resgates` sem `inicio` e `fim`
- **THEN** a resposta SHALL cobrir os últimos 30 dias até a maior `data_resgate`

#### Scenario: Agregação

- **WHEN** o cliente chama `tesouro_resgates` com `agregar=true`
- **THEN** a resposta SHALL conter `agregados` por tipo e título
- **THEN** `PU_MEDIO` SHALL ser vazio para recompras

#### Scenario: Paginação

- **WHEN** há mais registros do que `limite`
- **THEN** a resposta SHALL incluir `nextCursor`

#### Scenario: Período sem registros

- **WHEN** o filtro não encontra resgates
- **THEN** a resposta SHALL conter `registros: []`
- **THEN** `total_registros` SHALL ser `0`
- **THEN** a tool NÃO SHALL acessar a rede

### Requirement: Tool tesouro_estoque

A tool `tesouro_estoque` SHALL aceitar `titulo`, `inicio`, `fim`, `mes`, `agregar`, `cursor` e `limite` opcionais. Ela SHALL ler apenas o cache local de estoque, sem rede, download ou escrita de arquivos.

A resposta SHALL conter `dataset: "estoque"`, `origem: "cache"`, `data_extracao`, `total_registros`, `periodo`, `registros` ou `agregados`, e `nextCursor` quando houver continuação.

#### Scenario: Resposta estruturada

- **WHEN** o cliente chama `tesouro_estoque`
- **THEN** a resposta SHALL conter os metadados do dataset e `registros` ou `agregados`
- **THEN** a origem SHALL ser `cache`

#### Scenario: Cache vazio

- **WHEN** não há cache de estoque
- **THEN** a tool SHALL devolver erro de domínio `cache_vazio`
- **THEN** a dica SHALL indicar o subcomando `tesouro-estoque` para preparar o cache

### Requirement: Filtros e agregação da tool tesouro_estoque

`titulo` SHALL ser parcial, sem caixa/acentos. `inicio`/`fim` SHALL usar `AAAA-MM` e ser inclusivos. `mes` SHALL selecionar um único mês. Sem filtros, SHALL ser retornado o último mês disponível.

`agregar` SHALL exigir um único mês e agrupar por título. A soma de `valor_estoque` entre meses NÃO SHALL ser permitida.

#### Scenario: Último mês é o padrão

- **WHEN** o cliente chama `tesouro_estoque` sem filtros
- **THEN** a resposta SHALL conter apenas o último mês disponível

#### Scenario: Intervalo de meses

- **WHEN** o cliente chama `tesouro_estoque` com `inicio` e `fim`
- **THEN** a resposta SHALL conter os meses do intervalo inclusivo

#### Scenario: Agregação exige um mês

- **WHEN** o cliente chama `tesouro_estoque` com `agregar=true` e um intervalo com mais de um mês
- **THEN** a tool SHALL devolver erro de domínio de uso inválido
- **THEN** nenhum agregado SHALL ser produzido

#### Scenario: Paginação

- **WHEN** há mais registros do que `limite`
- **THEN** a resposta SHALL incluir `nextCursor`

#### Scenario: Período sem registros

- **WHEN** o filtro não encontra estoque
- **THEN** a resposta SHALL conter `registros: []`
- **THEN** `total_registros` SHALL ser `0`
- **THEN** a tool NÃO SHALL acessar a rede
