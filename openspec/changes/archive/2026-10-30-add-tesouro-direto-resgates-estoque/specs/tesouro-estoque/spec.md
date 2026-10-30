## Purpose

Descrever a aquisição, o cache, o processamento e a formatação do estoque mensal do Tesouro Direto, sem depender da presentation e reutilizando a infraestrutura da feature de vendas.

## ADDED Requirements

### Requirement: Descoberta do recurso de estoque

O sistema SHALL descobrir o dataset `estoque-do-tesouro-direto` pela API CKAN JSON e SHALL selecionar o recurso CSV de estoque.

O sistema SHALL validar `success: true`, SHALL exigir exatamente um recurso com formato CSV e NÃO SHALL extrair o PDF de metadados.

#### Scenario: Recurso é descoberto

- **WHEN** o sistema consulta `package_show?id=estoque-do-tesouro-direto`
- **THEN** a resposta SHALL conter o recurso "Estoque do Tesouro Direto"
- **THEN** o sistema SHALL extrair a URL e o identificador do CSV

#### Scenario: Recurso ausente

- **WHEN** o recurso CSV não existe ou está ambíguo
- **THEN** o sistema SHALL levantar `TesouroDataError`

#### Scenario: Nenhum scraping de HTML

- **WHEN** o sistema descobre o recurso
- **THEN** ele SHALL usar apenas JSON da API CKAN
- **THEN** ele NÃO SHALL interpretar HTML da página do portal

### Requirement: Download e cache do estoque

O sistema SHALL baixar o CSV de estoque com timeout padrão de 60 segundos, usando `ETag`/`If-None-Match` e `Last-Modified`/`If-Modified-Since` quando disponíveis.

Uma resposta `304` SHALL reutilizar o cache e atualizar apenas `checked_at`. Falhas transitórias SHALL ser repetidas com backoff/jitter e, após os retries, sinalizadas como `CommunicationError`.

#### Scenario: Download bem-sucedido

- **WHEN** o recurso responde HTTP 200 com CSV válido
- **THEN** o sistema SHALL baixar em chunks
- **THEN** o conteúdo SHALL ser validado antes de substituir o cache

#### Scenario: 304 reutiliza o cache

- **WHEN** o servidor responde `304 Not Modified`
- **THEN** o CSV SHALL ser reutilizado
- **THEN** apenas `checked_at` do metadata SHALL ser atualizado

#### Scenario: Falha preserva a versão anterior

- **WHEN** o download falha
- **THEN** a versão válida anterior SHALL permanecer disponível

#### Scenario: Cache com TTL

- **WHEN** o cache tem menos de 24 horas
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede
- **WHEN** o cache tem 24 horas ou mais
- **THEN** o sistema SHALL tentar um download condicional

#### Scenario: Corpo parcial ou não-CSV

- **WHEN** o corpo baixado é parcial ou o `Content-Type` não começa por `text/csv`
- **THEN** o sistema SHALL tratar como falha transitória
- **THEN** após os retries, SHALL levantar `CommunicationError`

### Requirement: Modelo de estoque

O sistema SHALL representar cada linha como um frozen dataclass `EstoqueTesouroDireto` com `tipo_titulo`, `vencimento`, `mes`, `pu`, `quantidade` e `valor_estoque`.

`vencimento` SHALL ser uma string ISO `AAAA-MM-DD`; `mes` SHALL ser `AAAA-MM`; `pu`, `quantidade` e `valor_estoque` SHALL ser `Decimal`.

#### Scenario: Modelo é imutável

- **WHEN** um registro de estoque é criado
- **THEN** seus campos NÃO SHALL ser modificáveis

#### Scenario: Mês no formato AAAA-MM

- **WHEN** `mes` é preenchido
- **THEN** ele SHALL estar no formato `AAAA-MM`

#### Scenario: Valores usam Decimal

- **WHEN** `pu`, `quantidade` e `valor_estoque` são preenchidos
- **THEN** eles SHALL ser `Decimal`

### Requirement: Parsing do estoque

O sistema SHALL interpretar o CSV com o cabeçalho:

```text
Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;Valor Estoque
```

O parsing SHALL converter `Vencimento do Titulo` de `DD/MM/YYYY` para ISO, `Mes Estoque` de `MM/YYYY` para `AAAA-MM` e decimais com vírgula para `Decimal`.

#### Scenario: Cabeçalho é validado

- **WHEN** o CSV é interpretado
- **THEN** o sistema SHALL exigir as seis colunas confirmadas

#### Scenario: Mês é convertido

- **WHEN** `Mes Estoque` é `09/2020`
- **THEN** `mes` SHALL ser `2020-09`

#### Scenario: Valor inválido

- **WHEN** uma data, mês ou valor não pode ser convertido
- **THEN** o sistema SHALL levantar `TesouroDataError` com linha e coluna

#### Scenario: CSV vazio

- **WHEN** o conteúdo não tem registros além do cabeçalho
- **THEN** o sistema SHALL levantar `TesouroDataError`
- **THEN** nenhum cache SHALL ser gravado

### Requirement: Filtros e comparação de meses

O sistema SHALL filtrar por título e por intervalo inclusivo de `mes`.

O padrão da CLI SHALL ser o último mês disponível. A agregação por título SHALL exigir um único mês e NÃO SHALL somar `valor_estoque` entre meses.

#### Scenario: Último mês na CLI

- **WHEN** o usuário executa `tesouro-estoque` sem filtros
- **THEN** a saída SHALL conter apenas o último mês disponível

#### Scenario: Intervalo de meses

- **WHEN** o usuário informa `--inicio 2025-01 --fim 2025-12`
- **THEN** a saída SHALL conter os meses do intervalo inclusivo

#### Scenario: Filtro por título

- **WHEN** o usuário filtra por parte do título
- **THEN** o sistema SHALL usar correspondência parcial sem caixa/acentos

#### Scenario: Agregação exige um mês

- **WHEN** a agregação é solicitada com um intervalo que cobre mais de um mês
- **THEN** o sistema SHALL levantar erro de uso
- **THEN** nenhum resultado agregado SHALL ser produzido

#### Scenario: Não somar estoque entre meses

- **WHEN** o intervalo contém mais de um mês
- **THEN** o total de `valor_estoque` NÃO SHALL ser somado entre meses
- **THEN** a agregação SHALL ser feita apenas dentro de um mês

### Requirement: Formatação do estoque

O sistema SHALL formatar o estoque em CSV e JSON.

O CSV SHALL usar `;`, datas ISO, mês `AAAA-MM` e ponto decimal. O CSV de estoque SHALL ter o cabeçalho `TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE`. O CSV agregado SHALL ter `TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO`.

O JSON SHALL seguir o envelope de vendas, com `dataset: "estoque"` e `mes` nos registros.

#### Scenario: CSV de estoque

- **WHEN** o estoque é formatado como CSV
- **THEN** o cabeçalho SHALL ser o definido
- **THEN** `PU` SHALL ter 6 casas; `quantidade` e `valor_estoque`, 2 casas

#### Scenario: CSV agregado

- **WHEN** o estoque de um mês é agregado
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO`

#### Scenario: JSON de estoque

- **WHEN** o estoque é formatado como JSON
- **THEN** o payload SHALL conter `dataset`, `mes`, metadados e `registros` ou `agregados`

#### Scenario: Mês sem registros

- **WHEN** o filtro não encontra registros
- **THEN** o resultado SHALL ser vazio, sem erro de transporte

### Requirement: Erros e processamento headless

O sistema SHALL classificar rede/HTTP/timeout como `CommunicationError` e CSV/schema/valores inválidos como `TesouroDataError`. O processamento, os filtros, a agregação e a formatação SHALL residir em `application` e NÃO SHALL importar `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede.

#### Scenario: Erro de comunicação

- **WHEN** o download falha por rede ou HTTP
- **THEN** o erro SHALL ser `CommunicationError`
- **THEN** a mensagem de log SHALL ocupar uma única linha

#### Scenario: Erro de dados

- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** o erro SHALL ser `TesouroDataError`

#### Scenario: Processamento sem display

- **WHEN** um teste exercita o processamento de estoque
- **THEN** ele SHALL importar apenas módulos de `application` e `domain`
- **THEN** nenhuma janela ou figura SHALL ser criada
