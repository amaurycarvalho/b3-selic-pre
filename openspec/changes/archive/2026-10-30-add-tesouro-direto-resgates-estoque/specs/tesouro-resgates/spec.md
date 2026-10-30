## Purpose

Descrever a aquisição, o cache, o processamento e a formatação dos resgates do Tesouro Direto (recompras, cupom e vencimentos), sem depender da presentation e reutilizando a infraestrutura da feature de vendas.

## ADDED Requirements

### Requirement: Descoberta dos recursos de resgates

O sistema SHALL descobrir o dataset `resgates-do-tesouro-direto` pela API CKAN JSON e SHALL selecionar três recursos lógicos: `recompra`, `cupom` e `vencimento`.

O sistema SHALL validar `success: true`, SHALL considerar apenas recursos `format == "CSV"` e SHALL selecionar o recurso de cupom com maior `last_modified` quando houver mais de um com o mesmo nome.

#### Scenario: Recursos são descobertos

- **WHEN** o sistema consulta `package_show?id=resgates-do-tesouro-direto`
- **THEN** a resposta SHALL conter os recursos de recompras, cupom e vencimentos
- **THEN** o sistema SHALL mapear cada recurso para seu tipo lógico

#### Scenario: Cupom duplicado

- **WHEN** existem dois recursos CSV com o nome "Pagamento de Cupom de Juros do Tesouro Direto"
- **THEN** o sistema SHALL selecionar o recurso com maior `last_modified`
- **THEN** o recurso antigo NÃO SHALL ser usado

#### Scenario: Recurso ausente

- **WHEN** um dos três recursos lógicos não existe ou está ambíguo
- **THEN** o sistema SHALL levantar `TesouroDataError`

#### Scenario: Nenhum scraping de HTML

- **WHEN** o sistema descobre os recursos
- **THEN** ele SHALL usar apenas JSON da API CKAN
- **THEN** ele NÃO SHALL interpretar HTML da página do portal

### Requirement: Download e cache por recurso

O sistema SHALL baixar e cachear cada recurso de resgates independentemente, com timeout padrão de 60 segundos por recurso.

O download SHALL usar `ETag`/`If-None-Match` e `Last-Modified`/`If-Modified-Since`, SHALL tratar `304` como cache válido e SHALL repetir falhas transitórias com backoff/jitter.

#### Scenario: Download bem-sucedido

- **WHEN** um recurso responde HTTP 200 com CSV válido
- **THEN** o sistema SHALL baixar em chunks
- **THEN** o conteúdo SHALL ser validado antes de substituir o cache daquele recurso

#### Scenario: 304 reutiliza o recurso

- **WHEN** o servidor responde `304 Not Modified` para um recurso
- **THEN** o CSV daquele recurso SHALL ser reutilizado
- **THEN** apenas `checked_at` do metadata daquele recurso SHALL ser atualizado

#### Scenario: Falha isolada

- **WHEN** o download de um recurso falha
- **THEN** a versão anterior daquele recurso SHALL ser preservada
- **THEN** os demais recursos SHALL permanecer disponíveis

#### Scenario: Cache por recurso

- **WHEN** os resgates são carregados
- **THEN** cada recurso SHALL ter seu próprio CSV e seu próprio metadata
- **THEN** o TTL SHALL ser aplicado individualmente
- **THEN** recompras SHALL usar 1 hora quando contiver o dia corrente ou o último dia útil e 6 horas quando o dado for histórico
- **THEN** cupom e vencimentos SHALL usar 24 horas

#### Scenario: Corpo parcial ou não-CSV

- **WHEN** o corpo baixado é parcial ou o `Content-Type` não começa por `text/csv`
- **THEN** o sistema SHALL tratar como falha transitória
- **THEN** após os retries, SHALL levantar `CommunicationError`

### Requirement: Modelo de resgate

O sistema SHALL representar cada resgate como um frozen dataclass `ResgateTesouroDireto` com `tipo_resgate`, `tipo_titulo`, `vencimento`, `data_resgate`, `pu`, `quantidade` e `valor`.

`tipo_resgate` SHALL ser `recompra`, `cupom` ou `vencimento`. `pu` SHALL ser `None` para recompras. `vencimento` e `data_resgate` SHALL ser strings ISO. `quantidade` e `valor` SHALL ser `Decimal`.

#### Scenario: Modelo é imutável

- **WHEN** um resgate é criado
- **THEN** seus campos NÃO SHALL ser modificáveis

#### Scenario: Recompra sem PU

- **WHEN** o resgate é do tipo `recompra`
- **THEN** `pu` SHALL ser `None`

#### Scenario: Cupom e vencimento com PU

- **WHEN** o resgate é do tipo `cupom` ou `vencimento`
- **THEN** `pu` SHALL ser `Decimal`

### Requirement: Parsing dos recursos de resgates

O sistema SHALL interpretar cada recurso conforme seu cabeçalho:

- recompras: `Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade;Valor`;
- cupom e vencimentos: `Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor`.

O parsing SHALL converter `Data Resgate` de `DD/MM/YYYY` para ISO, decimais com vírgula para `Decimal` e SHALL derivar `tipo_resgate` do recurso lógico.

#### Scenario: Cabeçalho de recompras

- **WHEN** o recurso de recompras é interpretado
- **THEN** o sistema SHALL exigir as cinco colunas confirmadas
- **THEN** `pu` SHALL ser `None`

#### Scenario: Cabeçalho de cupom/vencimentos

- **WHEN** cupom ou vencimentos é interpretado
- **THEN** o sistema SHALL exigir as seis colunas confirmadas
- **THEN** `pu` SHALL ser convertido para `Decimal`

#### Scenario: Datas e decimais

- **WHEN** uma data `DD/MM/YYYY` ou um decimal com vírgula é lido
- **THEN** o sistema SHALL convertê-los para ISO e `Decimal`
- **THEN** valores inválidos SHALL gerar `TesouroDataError` com linha e coluna

#### Scenario: CSV vazio

- **WHEN** um recurso não tem registros além do cabeçalho
- **THEN** o sistema SHALL levantar `TesouroDataError`
- **THEN** nenhum cache daquele recurso SHALL ser gravado

### Requirement: Filtros, agregação e ordenação de resgates

O sistema SHALL filtrar por `tipo_resgate`, título e período inclusivo de `data_resgate`.

A agregação SHALL agrupar por `tipo_resgate` e `tipo_titulo`, somar `quantidade` e `valor` e calcular `PU` médio ponderado apenas quando todas as linhas do grupo tiverem `PU`.

A ordenação SHALL ser `data_resgate` desc, `tipo_resgate`, `tipo_titulo`, `vencimento` e `pu`.

#### Scenario: Filtro por tipo

- **WHEN** o usuário filtra por `recompra`
- **THEN** o resultado SHALL conter apenas recompras

#### Scenario: Filtro por título

- **WHEN** o usuário filtra por parte do título
- **THEN** o sistema SHALL usar correspondência parcial sem caixa/acentos

#### Scenario: Agregação de recompras

- **WHEN** recompras são agregadas
- **THEN** `quantidade` e `valor` SHALL ser somados
- **THEN** `PU_MEDIO` SHALL ser vazio

#### Scenario: Agregação de cupom/vencimentos

- **WHEN** cupom ou vencimentos são agregados
- **THEN** `PU_MEDIO` SHALL ser `valor_total / quantidade_total`

#### Scenario: Ordenação determinística

- **WHEN** os resgates são exibidos
- **THEN** eles SHALL seguir a ordenação definida
- **THEN** a ordem do CSV de origem NÃO SHALL ser usada como garantia

### Requirement: Formatação de resgates

O sistema SHALL formatar resgates em CSV e JSON.

O CSV SHALL usar `;`, datas ISO e ponto decimal. O CSV de resgates SHALL ter o cabeçalho `TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;PU;QUANTIDADE;VALOR`. O CSV agregado SHALL ter `TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`.

O JSON SHALL seguir o envelope de vendas, com `dataset: "resgates"` e `tipo_resgate` nos registros.

#### Scenario: CSV de resgates

- **WHEN** os resgates são formatados como CSV
- **THEN** o cabeçalho SHALL ser o definido
- **THEN** `PU` SHALL ter 6 casas; `quantidade` e `valor`, 2 casas

#### Scenario: CSV agregado

- **WHEN** os resgates são agregados
- **THEN** o cabeçalho SHALL ser `TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`

#### Scenario: JSON de resgates

- **WHEN** os resgates são formatados como JSON
- **THEN** o payload SHALL conter `dataset`, `tipo_resgate`, metadados e `registros` ou `agregados`

#### Scenario: Período sem registros

- **WHEN** o filtro não encontra resgates
- **THEN** o resultado SHALL ser vazio, sem erro de transporte

### Requirement: Erros e processamento headless

O sistema SHALL classificar rede/HTTP/timeout como `CommunicationError` e CSV/schema/valores inválidos como `TesouroDataError`. O processamento, os filtros, a agregação e a formatação SHALL residir em `application` e NÃO SHALL importar `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede.

#### Scenario: Erro de comunicação

- **WHEN** um download falha por rede ou HTTP
- **THEN** o erro SHALL ser `CommunicationError`
- **THEN** a mensagem de log SHALL ocupar uma única linha

#### Scenario: Erro de dados

- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** o erro SHALL ser `TesouroDataError`

#### Scenario: Processamento sem display

- **WHEN** um teste exercita o processamento de resgates
- **THEN** ele SHALL importar apenas módulos de `application` e `domain`
- **THEN** nenhuma janela ou figura SHALL ser criada
