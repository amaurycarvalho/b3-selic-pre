# MCP Tools

## Purpose

Definir o catálogo de tools somente leitura do servidor MCP, seus argumentos, formatos de resultado, paginação e erros de domínio recuperáveis.

## Requirements

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

A tool `consultar_curva` SHALL aceitar `data`, `curva` (`curta`/`longa`), `cursor` e `limite`, todos opcionais. Sem `data`, SHALL usar a data de referência, validada como na CLI. Para `curta`, cada item SHALL conter dia útil 252, dia corrido 365, taxa numérica e texto original; para `longa`, ano, menor taxa, maior taxa e média anual. A resposta SHALL incluir `nextCursor` quando houver continuação; sem registros, SHALL retornar `sem_dados`.

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

As tools `exportar_curva_curta` e `exportar_curva_longa` SHALL aceitar `data` opcional e devolver o CSV do artefato correspondente, sem gravar arquivos. `exportar_curva_curta` SHALL usar `;` e colunas `DATA;DU252;DC365;TAXA` na janela de cinco datas; `exportar_curva_longa`, `;` e `DATA;ANO;TAXA_MEDIA`. A resposta SHALL incluir nome do artefato, tipo de conteúdo e datas indisponíveis; sem dados, SHALL retornar `sem_dados`.

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

A tool `analise` SHALL aceitar `data` e `curva` (`curta`/`longa`), com `curta` como padrão, e devolver o texto determinístico da análise e, quando disponível, o da evolução. `curta` SHALL usar registros brutos; `longa`, as taxas médias anuais. A resposta SHALL identificar a curva e listar datas indisponíveis. Análise pré-calculada PODE ser reutilizada apenas para a mesma curva; outra curva SHALL ser recalculada. Sem dados, SHALL retornar `sem_dados`.

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

### Requirement: Tool mercado_serie

A tool `mercado_serie` SHALL aceitar `ativo` opcional (`usd`, `ouro` ou `ambos`), `inicio`, `fim`, `resolucao` opcional (`auto`, `dia`, `semana` ou `mes`), `cursor` e `limite`.

A tool SHALL ler apenas o cache local e devolver itens com data, ativo, valor, unidade, origem, método, horário de extração e indicador de defasagem. A resposta SHALL incluir `nextCursor` quando houver continuação.

#### Scenario: Série do dólar

- **WHEN** o cliente chama `mercado_serie` com `ativo=usd`
- **THEN** a resposta SHALL conter apenas a série de dólar
- **THEN** cada item SHALL conter valor, unidade e origem

#### Scenario: Série do ouro

- **WHEN** o cliente chama `mercado_serie` com `ativo=ouro`
- **THEN** os valores SHALL estar em R$/g
- **THEN** o método SHALL indicar derivação quando aplicável

#### Scenario: Resolução automática

- **WHEN** `resolucao` é omitida
- **THEN** a tool SHALL aplicar a resolução em camadas da janela solicitada

#### Scenario: Paginação

- **WHEN** há mais itens do que o limite
- **THEN** a resposta SHALL incluir `nextCursor`

#### Scenario: Sem dados

- **WHEN** não há série em cache para a janela
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`
- **THEN** a tool NÃO SHALL acessar a rede

### Requirement: Tool mercado_previsao

A tool `mercado_previsao` SHALL aceitar `ativo` opcional (`usd`, `ouro` ou `ambos`) e `horizonte` opcional, com 12 meses como padrão.

A tool SHALL devolver pontos mensais com valor central, bandas de 80% e 95%, método e rótulo de cenário. A tool SHALL ler apenas o artefato pré-calculado e NÃO SHALL acessar a rede.

#### Scenario: Cenário do dólar

- **WHEN** o cliente chama `mercado_previsao` com `ativo=usd`
- **THEN** a resposta SHALL conter o cenário de 12 meses do dólar
- **THEN** o método SHALL indicar expectativa de mercado

#### Scenario: Cenário do ouro

- **WHEN** o cliente chama `mercado_previsao` com `ativo=ouro`
- **THEN** a resposta SHALL conter o cenário de 12 meses do ouro
- **THEN** o método SHALL indicar projeção estatística

#### Scenario: Bandas presentes

- **WHEN** há cenário disponível
- **THEN** cada ponto SHALL conter as bandas de 80% e 95%

#### Scenario: Pré-cálculo ausente

- **WHEN** não há cenário pré-calculado para o ativo
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`
- **THEN** a tool NÃO SHALL calcular a projeção em tempo de execução

### Requirement: Tool mercado_indicadores

A tool `mercado_indicadores` SHALL devolver os sinais de política cambial disponíveis: prêmio a termo, prêmio implícito DOL, gap Focus, volatilidade realizada de 30 e 90 dias, indicador de regime e limiar usado.

A tool SHALL ler apenas o cache local e SHALL omitir sinais cujos insumos não estejam disponíveis.

#### Scenario: Sinais disponíveis

- **WHEN** há dados suficientes em cache
- **THEN** a resposta SHALL conter os sinais calculados
- **THEN** cada sinal SHALL identificar sua origem e data de referência

#### Scenario: Sinal indisponível

- **WHEN** um insumo está ausente
- **THEN** apenas o sinal correspondente SHALL ser omitido
- **THEN** os demais sinais SHALL ser devolvidos

#### Scenario: Sem dados

- **WHEN** não há nenhum insumo em cache
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`

### Requirement: Tool mercado_exportar

A tool `mercado_exportar` SHALL aceitar `ativo` opcional, `inicio`, `fim`, `formato` (`csv` ou `json`) e `prever` opcional.

A tool SHALL devolver o conteúdo, o nome sugerido, o tipo de conteúdo e a lista de datas indisponíveis, sem gravar arquivos. A tool SHALL ler apenas o cache local.

#### Scenario: Exportação CSV

- **WHEN** o cliente chama `mercado_exportar` com `formato=csv`
- **THEN** a resposta SHALL conter CSV com delimitador `;`
- **THEN** o nome sugerido SHALL seguir o padrão `mercado-historico.csv`

#### Scenario: Exportação com cenário

- **WHEN** `prever` é verdadeiro
- **THEN** a resposta SHALL conter também o artefato de cenário
- **THEN** o cenário SHALL ser identificado como projeção

#### Scenario: Datas indisponíveis

- **WHEN** parte da janela não possui dados
- **THEN** a resposta SHALL listar as datas indisponíveis
- **THEN** os dados disponíveis SHALL ser devolvidos

#### Scenario: Sem dados

- **WHEN** não há dados para a janela
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`

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
