# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo de tools somente leitura

O servidor SHALL expor as tools `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas`, `listar_datas`, `tesouro_vendas`, `tesouro_resgates`, `tesouro_estoque`, `mercado_serie`, `mercado_previsao`, `mercado_indicadores` e `mercado_exportar`.

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
