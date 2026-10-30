# MCP Tools

## Purpose

Definir o catálogo de tools somente leitura do servidor MCP, seus argumentos, formatos de resultado, paginação e erros de domínio recuperáveis.

## Requirements

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

### Requirement: Tool data_referencia

A tool `data_referencia` SHALL não aceitar argumentos de entrada e SHALL devolver a data de referência resolvida da última carga de dados.

A data SHALL ser lida das configurações da aplicação. Se a configuração não existir ou for inválida, o sistema SHALL usar a maior data válida presente no cache local. Se não houver cache, a tool SHALL devolver erro de domínio `cache_vazio`.

A tool SHALL ser somente leitura e NÃO SHALL alterar a data de referência.

#### Scenario: Data da última carga

- **WHEN** a última carga bem-sucedida foi de 2026-06-10
- **THEN** `data_referencia` SHALL devolver 2026-06-10

#### Scenario: Fallback para o cache

- **WHEN** a configuração não contém uma data de referência válida e o cache contém 2026-06-10
- **THEN** `data_referencia` SHALL devolver 2026-06-10
- **THEN** a origem SHALL indicar que a data veio do cache

#### Scenario: Cache vazio

- **WHEN** não há data de referência válida nem dados no cache
- **THEN** `data_referencia` SHALL devolver erro de domínio com motivo `cache_vazio`

#### Scenario: Data sem entrada no cache

- **WHEN** a data de referência é válida mas não há registros em cache para ela
- **THEN** a tool SHALL devolver a data com indicação de indisponibilidade
- **THEN** a tool NÃO SHALL baixar dados

### Requirement: Tool consultar_curva

A tool `consultar_curva` SHALL aceitar `data` opcional, `curva` opcional com valores `curta` ou `longa`, `cursor` opcional e `limite` opcional.

Quando `data` for omitida, a tool SHALL usar a data de referência. A data SHALL seguir as mesmas regras de validação da CLI: formato `AAAA-MM-DD`, não futura, dentro da janela de 30 dias e ajustada para o dia útil anterior em fins de semana.

Para `curva=curta`, cada item SHALL conter o dia útil 252, o dia corrido 365, a taxa numérica e a representação textual original da taxa. Para `curva=longa`, cada item SHALL conter o ano, a menor taxa, a maior taxa e a taxa média anual.

A resposta SHALL incluir `nextCursor` quando houver continuação. Se não houver registros para a data, a tool SHALL devolver erro de domínio `sem_dados`.

#### Scenario: Consulta da curva curta

- **WHEN** o cliente chama `consultar_curva` com `curva=curta` para uma data em cache
- **THEN** a resposta SHALL conter os registros brutos da data
- **THEN** os valores numéricos SHALL ser adequados para cálculo por agentes

#### Scenario: Consulta da curva longa

- **WHEN** o cliente chama `consultar_curva` com `curva=longa` para uma data em cache
- **THEN** a resposta SHALL conter uma linha por ano com menor taxa, maior taxa e taxa média

#### Scenario: Data omitida usa a referência

- **WHEN** o cliente chama `consultar_curva` sem `data`
- **THEN** a tool SHALL usar a data de referência resolvida

#### Scenario: Data inválida

- **WHEN** o cliente informa uma data fora do formato, futura ou fora da janela de 30 dias
- **THEN** a tool SHALL devolver erro de domínio com o motivo correspondente
- **THEN** a tool NÃO SHALL consultar a B3

#### Scenario: Data sem dados

- **WHEN** não há registros em cache para a data solicitada
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`
- **THEN** a dica SHALL indicar como preparar o cache

#### Scenario: Paginação da curva

- **WHEN** há mais registros do que o limite da página
- **THEN** a resposta SHALL incluir `nextCursor`
- **THEN** o cliente SHALL poder continuar a partir do cursor

### Requirement: Tools exportar_curva_curta e exportar_curva_longa

As tools `exportar_curva_curta` e `exportar_curva_longa` SHALL aceitar `data` opcional e SHALL devolver o conteúdo CSV do artefato correspondente ao subcomando `exportar`, sem gravar arquivos.

`exportar_curva_curta` SHALL devolver CSV com delimitador `;` e colunas `DATA;DU252;DC365;TAXA`, cobrindo a janela de evolução de cinco datas. `exportar_curva_longa` SHALL devolver CSV com delimitador `;` e colunas `DATA;ANO;TAXA_MEDIA`.

As respostas SHALL incluir o nome do artefato, o tipo de conteúdo e a lista de datas indisponíveis. Se não houver nenhum dado, a tool SHALL devolver erro de domínio `sem_dados`.

#### Scenario: Exportação da curva curta

- **WHEN** o cliente chama `exportar_curva_curta`
- **THEN** a resposta SHALL conter CSV detalhado das datas disponíveis
- **THEN** os nomes e formatos SHALL corresponder ao artefato `curva-curta.csv`

#### Scenario: Exportação da curva longa

- **WHEN** o cliente chama `exportar_curva_longa`
- **THEN** a resposta SHALL conter CSV com a taxa média por ano e data
- **THEN** os nomes e formatos SHALL corresponder ao artefato `curva-longa.csv`

#### Scenario: Datas indisponíveis são informadas

- **WHEN** uma ou mais datas da janela de evolução não possuem registros em cache
- **THEN** a resposta SHALL listar essas datas
- **THEN** a tool SHALL devolver os dados disponíveis quando houver ao menos uma data

#### Scenario: Nenhum dado disponível

- **WHEN** nenhuma data da janela possui registros em cache
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`

### Requirement: Tool analise

A tool `analise` SHALL aceitar `data` opcional e `curva` opcional com valores `curta` ou `longa`, com `curta` como padrão. A tool SHALL devolver o texto determinístico da análise da curva e, quando houver data anterior disponível, o texto da evolução.

Para `curva=curta`, a análise SHALL usar os registros brutos. Para `curva=longa`, a análise SHALL usar a série de taxas médias por ano. A resposta SHALL identificar a curva usada e SHALL listar as datas indisponíveis.

Se existir uma análise pré-calculada para a curva solicitada, o sistema PODE reutilizá-la. Se a análise pré-calculada for de outra curva, o sistema SHALL recalcular o texto em tempo de execução. Uma análise de uma curva NUNCA SHALL ser devolvida para a outra.

Se não houver dados para a data, a tool SHALL devolver erro de domínio `sem_dados`.

#### Scenario: Análise curta é o padrão

- **WHEN** o cliente chama `analise` sem `curva`
- **THEN** a análise SHALL usar os registros brutos
- **THEN** a resposta SHALL identificar `curva=curta`

#### Scenario: Análise longa

- **WHEN** o cliente chama `analise` com `curva=longa`
- **THEN** a análise SHALL usar a taxa média por ano
- **THEN** a resposta SHALL identificar `curva=longa`

#### Scenario: Análise pré-calculada de outra curva é recalculada

- **WHEN** a análise pré-calculada disponível é da curva curta e o cliente pede a curva longa
- **THEN** o sistema SHALL recalcular a análise com a série de médias anuais
- **THEN** o texto devolvido SHALL corresponder à curva longa

#### Scenario: Sem dados para análise

- **WHEN** não há registros em cache para a data solicitada
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`

### Requirement: Tool evolucao

A tool `evolucao` SHALL aceitar `data` opcional, `cursor` opcional e `limite` opcional. Ela SHALL devolver um resumo estruturado da janela de evolução, com um item por data contendo a data, o total de registros, a menor taxa, a maior taxa, a taxa curta, a taxa longa e a inclinação em pontos-base.

A resposta SHALL listar as datas indisponíveis e SHALL incluir `nextCursor` quando houver continuação. Se nenhuma data possuir registros, a tool SHALL devolver erro de domínio `sem_dados`.

#### Scenario: Resumo da evolução

- **WHEN** o cliente chama `evolucao`
- **THEN** a resposta SHALL conter um item por data disponível
- **THEN** cada item SHALL conter os indicadores resumidos da curva

#### Scenario: Datas indisponíveis

- **WHEN** uma ou mais datas da janela não possuem registros
- **THEN** a resposta SHALL listar essas datas
- **THEN** a tool SHALL devolver os itens disponíveis

#### Scenario: Paginação da evolução

- **WHEN** houver mais datas do que o limite da página
- **THEN** a resposta SHALL incluir `nextCursor`

### Requirement: Tool estatisticas

A tool `estatisticas` SHALL aceitar `data` opcional e SHALL devolver estatísticas da curva da data: total de registros, menor taxa, maior taxa, taxa curta, taxa longa, inclinação em pontos-base e juro real implícito.

A taxa curta SHALL ser o primeiro vértice da curva e a taxa longa SHALL ser o último. Se não houver dados, a tool SHALL devolver erro de domínio `sem_dados`.

#### Scenario: Estatísticas da curva

- **WHEN** o cliente chama `estatisticas` para uma data em cache
- **THEN** a resposta SHALL conter as estatísticas calculadas a partir dos registros
- **THEN** a inclinação SHALL ser expressa em pontos-base

#### Scenario: Sem dados para estatísticas

- **WHEN** não há registros em cache para a data
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`

### Requirement: Tool listar_datas

A tool `listar_datas` SHALL aceitar `cursor` opcional e `limite` opcional. Ela SHALL devolver as datas com entradas válidas no cache local, ordenadas da mais recente para a mais antiga, com metadados de quantidade de registros, instante de cache e fonte.

A resposta SHALL incluir `nextCursor` quando houver continuação. Um cache vazio SHALL produzir uma lista vazia, não um erro.

#### Scenario: Listagem das datas em cache

- **WHEN** o cache contém as datas 2026-06-10 e 2026-06-17
- **THEN** a resposta SHALL listar 2026-06-17 antes de 2026-06-10
- **THEN** cada item SHALL conter os metadados da entrada

#### Scenario: Cache vazio na listagem

- **WHEN** não há entradas válidas no cache
- **THEN** a resposta SHALL conter uma lista vazia
- **THEN** a tool NÃO SHALL devolver erro

#### Scenario: Paginação das datas

- **WHEN** houver mais datas do que o limite da página
- **THEN** a resposta SHALL incluir `nextCursor`

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

### Requirement: Paginação com cursores opacos

As respostas de listagem SHALL usar cursores opacos e estáveis. A ausência de `nextCursor` SHALL indicar o fim dos resultados. Um cursor inválido SHALL ser rejeitado com erro JSON-RPC `-32602`.

O tamanho da página SHALL ser determinado pelo servidor; o cliente NÃO SHALL assumir um tamanho fixo.

#### Scenario: Cursor inválido

- **WHEN** o cliente envia um cursor inválido
- **THEN** o servidor SHALL responder com código `-32602`

#### Scenario: Fim da paginação

- **WHEN** não há mais resultados
- **THEN** a resposta NÃO SHALL conter `nextCursor`

### Requirement: Envelope de erros de domínio

Erros de domínio recuperáveis SHALL ser devolvidos como resultado estruturado com `motivo`, `detalhe` e `dica`, sem `isError`.

Os motivos SHALL incluir, no mínimo, `data_invalida`, `data_futura`, `data_antiga`, `sem_dados` e `cache_vazio`.

#### Scenario: Erro recuperável não é falha de transporte

- **WHEN** uma tool devolve um erro de domínio
- **THEN** o resultado NÃO SHALL conter `isError`
- **THEN** o conteúdo estruturado SHALL conter `motivo`, `detalhe` e `dica`

#### Scenario: Dica acionável

- **WHEN** o erro é `sem_dados` ou `cache_vazio`
- **THEN** a dica SHALL indicar como preparar ou atualizar o cache

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
