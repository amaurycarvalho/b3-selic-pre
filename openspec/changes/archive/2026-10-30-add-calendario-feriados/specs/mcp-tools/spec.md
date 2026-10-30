# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo de tools somente leitura

O servidor SHALL expor as tools `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas`, `listar_datas`, `tesouro_vendas`, `tesouro_resgates`, `tesouro_estoque`, `feriados_listar`, `feriados_consultar` e `feriados_exportar`.

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

### Requirement: Tools de feriados

As tools `feriados_listar`, `feriados_consultar` e `feriados_exportar` SHALL ler apenas o cache do calendário, NÃO SHALL acessar rede e NÃO SHALL gravar arquivos. Sem cache para o ano solicitado, SHALL devolver erro de domínio `sem_dados` com dica de atualização.

#### Scenario: Listagem paginada
- **WHEN** o cliente chama `feriados_listar` para um ano em cache
- **THEN** a resposta SHALL conter data, dia da semana, nome e origem de cada feriado
- **THEN** a paginação SHALL usar os cursores opacos existentes

#### Scenario: Consulta de data
- **WHEN** o cliente chama `feriados_consultar` com uma data
- **THEN** a resposta SHALL informar se é dia útil
- **THEN** quando não for, SHALL informar o motivo e o nome do feriado

#### Scenario: Exportação sem arquivo
- **WHEN** o cliente chama `feriados_exportar` com formato CSV ou JSON
- **THEN** a tool SHALL devolver o conteúdo no payload
- **THEN** nenhum arquivo SHALL ser gravado

#### Scenario: Ano sem cache
- **WHEN** o ano solicitado não está no cache
- **THEN** a tool SHALL devolver erro de domínio `sem_dados`
- **THEN** a dica SHALL orientar a executar uma carga com atualização do calendário

### Requirement: Ajuste de data nos payloads

As tools que aceitam `data` SHALL informar quando a data foi ajustada para um dia útil. O payload SHALL conter `data_solicitada`, `data_resolvida`, `ajustada`, `motivo` e, quando aplicável, o nome do feriado.

#### Scenario: Data não útil é ajustada
- **WHEN** uma tool recebe uma data que é feriado ou fim de semana
- **THEN** o payload SHALL usar a data útil anterior
- **THEN** SHALL conter os campos de ajuste e o motivo

#### Scenario: Data útil é preservada
- **WHEN** uma tool recebe uma data útil
- **THEN** `data_resolvida` SHALL ser igual a `data_solicitada`
- **THEN** `ajustada` SHALL ser falso
