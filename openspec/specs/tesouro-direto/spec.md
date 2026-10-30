# Tesouro Direto Specification

## Purpose

Descrever a aquisição, o cache, o processamento e a formatação das vendas do Tesouro Direto, usando a API CKAN, a biblioteca padrão e sem depender da presentation.

## Requirements

### Requirement: Descoberta do dataset via API CKAN

O sistema SHALL descobrir o dataset `vendas-do-tesouro-direto` por meio da API CKAN JSON, sem scraping de HTML. A resposta SHALL fornecer os metadados do dataset e a URL do recurso CSV.

O sistema SHALL validar `success: true`, SHALL exigir exatamente um recurso com formato CSV e NÃO SHALL extrair o PDF de metadados.

#### Scenario: Metadados são obtidos da API

- **WHEN** o sistema consulta `package_show?id=vendas-do-tesouro-direto`
- **THEN** a resposta SHALL conter título, organização, data de última atualização e a lista de recursos
- **THEN** `success` SHALL ser verdadeiro

#### Scenario: URL do CSV é extraída

- **WHEN** a lista de recursos contém exatamente um recurso com formato CSV
- **THEN** o sistema SHALL extrair a URL e o identificador desse recurso

#### Scenario: Recurso CSV ausente

- **WHEN** a lista de recursos não contém um recurso CSV
- **THEN** o sistema SHALL levantar `TesouroDataError` identificando que o CSV não foi encontrado

#### Scenario: Nenhum scraping de HTML

- **WHEN** o sistema descobre o dataset
- **THEN** ele SHALL usar apenas JSON da API CKAN
- **THEN** ele NÃO SHALL interpretar HTML da página do portal

### Requirement: Download do CSV com retry e cabeçalhos condicionais

O sistema SHALL baixar o CSV com `urllib`, em chunks, com timeout de 60 segundos e retry transitório com backoff/jitter. O download SHALL usar cabeçalhos condicionais quando disponíveis. Falhas transitórias não recuperadas SHALL virar `CommunicationError`.

#### Scenario: Download bem-sucedido

- **WHEN** a URL do CSV responde com HTTP 200 e conteúdo válido
- **THEN** o sistema SHALL obter o conteúdo em chunks
- **THEN** o conteúdo SHALL ser validado antes de substituir o cache

#### Scenario: Resposta 304 reutiliza o cache

- **WHEN** o servidor responde `304 Not Modified`
- **THEN** o sistema SHALL reutilizar o CSV já armazenado
- **THEN** o CSV NÃO SHALL ser regravado
- **THEN** o metadata SHALL ter `checked_at` atualizado atomicamente

#### Scenario: Cabeçalhos são armazenados

- **WHEN** um download conclui com sucesso
- **THEN** o sistema SHALL armazenar `ETag`, `Last-Modified`, `downloaded_at`, `size_bytes`, `sha256` e `row_count` nos metadados do cache

#### Scenario: Corpo parcial

- **WHEN** o total de bytes baixados diverge do total informado em `Content-Range`
- **THEN** o sistema SHALL tratar como falha transitória
- **THEN** após os retries, SHALL levantar `CommunicationError`
- **THEN** o cache válido anterior NÃO SHALL ser descartado

#### Scenario: Falha de comunicação

- **WHEN** ocorre erro de rede, timeout ou status HTTP inválido
- **THEN** o sistema SHALL levantar `CommunicationError`
- **THEN** o cache válido anterior NÃO SHALL ser descartado

#### Scenario: Corpo vazio após retries

- **WHEN** o servidor responde com corpo vazio após todas as tentativas
- **THEN** o sistema SHALL levantar `CommunicationError`
- **THEN** nenhum resultado vazio SHALL ser cacheado

#### Scenario: Resposta não-CSV

- **WHEN** o servidor responde HTTP 200 com `Content-Type` que não começa por `text/csv`
- **THEN** o sistema SHALL tratar como falha transitória
- **THEN** após os retries, SHALL levantar `CommunicationError`

### Requirement: Cache cumulativo atômico

O sistema SHALL manter um único CSV cumulativo `vendastesourodireto.csv` e um `metadata.json` no diretório XDG.

O cache SHALL usar TTL condicional (1 hora para o dia corrente/último dia útil; 6 horas para histórico), gravação atômica em bytes e validação antes da substituição. Cache corrompido SHALL ser miss. O cache bruto NÃO SHALL ter housekeeping; a retenção de 3 anos pertence ao cache analítico.

#### Scenario: Dado corrente expira em 1 hora

- **WHEN** o CSV em cache contém o dia corrente ou o último dia útil e `checked_at` tem menos de 1 hora
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede
- **WHEN** `checked_at` tem 1 hora ou mais
- **THEN** o sistema SHALL tentar um download condicional

#### Scenario: Dado histórico expira em 6 horas

- **WHEN** o dado mais recente do CSV é histórico e `checked_at` tem menos de 6 horas
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede
- **WHEN** `checked_at` tem 6 horas ou mais
- **THEN** o sistema SHALL tentar um download condicional

#### Scenario: Cache corrompido

- **WHEN** o CSV ou os metadados em cache estão vazios, inválidos ou têm `schema_version` antigo
- **THEN** o sistema SHALL tratar a entrada como miss
- **THEN** o sistema SHALL baixar novamente e substituir o cache

#### Scenario: Escrita atômica

- **WHEN** um download válido conclui
- **THEN** o novo CSV SHALL ser gravado em arquivo temporário e substituído atomicamente
- **THEN** um leitor concorrente NÃO SHALL ver conteúdo parcial

#### Scenario: Falha preserva a versão anterior

- **WHEN** o download falha depois de existir um cache válido
- **THEN** a versão anterior SHALL permanecer disponível

#### Scenario: Leitura somente leitura

- **WHEN** o cache é lido em modo somente leitura
- **THEN** entradas ausentes, vencidas ou corrompidas SHALL ser tratadas como miss
- **THEN** nenhum arquivo SHALL ser removido, renomeado ou alterado

#### Scenario: Metadados completos

- **WHEN** um download ou uma resposta `304` conclui
- **THEN** o metadata SHALL conter `schema_version`, `dataset_name`, `dataset_id`, `resource_id`, `resource_url`, `etag`, `last_modified`, `downloaded_at`, `checked_at`, `size_bytes`, `sha256`, `row_count`, `first_data_date` e `last_data_date`

### Requirement: Modelo de venda do Tesouro Direto

O sistema SHALL representar cada venda como um frozen dataclass `VendaTesouroDireto` com os campos `tipo_titulo`, `vencimento`, `data_liquidacao`, `pu`, `quantidade` e `valor`.

`vencimento` e `data_liquidacao` SHALL ser strings ISO `AAAA-MM-DD`. `pu`, `quantidade` e `valor` SHALL ser `Decimal`. `data_liquidacao` SHALL representar a liquidação (D+1 da operação), não a data da venda.

#### Scenario: Modelo é imutável

- **WHEN** um registro é criado
- **THEN** seus campos NÃO SHALL ser modificáveis

#### Scenario: Campos estão acessíveis

- **WHEN** o registro é instanciado com os campos confirmados
- **THEN** todos os campos SHALL estar acessíveis como atributos

#### Scenario: Datas usam formato ISO

- **WHEN** `vencimento` e `data_liquidacao` são preenchidos
- **THEN** eles SHALL ser strings no formato `AAAA-MM-DD`

#### Scenario: Valores usam Decimal

- **WHEN** `pu`, `quantidade` e `valor` são preenchidos
- **THEN** eles SHALL ser instâncias de `Decimal`

### Requirement: Parsing e validação do CSV

O sistema SHALL interpretar o CSV usando o módulo `csv` da biblioteca padrão, a partir dos bytes baixados, sem realizar I/O de arquivo ou rede.

O parsing SHALL tentar UTF-8 com BOM, UTF-8 e Latin-1, nessa ordem, e SHALL usar `;` como delimitador. O sistema NÃO SHALL usar `csv.Sniffer`. O cabeçalho SHALL ser validado contra as seis colunas confirmadas. O mapeamento de colunas SHALL ignorar diferenças de caixa e acentuação. Linhas inválidas SHALL produzir erros que identifiquem a linha e a coluna.

#### Scenario: Cabeçalho é validado

- **WHEN** o CSV é interpretado
- **THEN** o sistema SHALL exigir `Tipo Titulo`, `Vencimento do Titulo`, `Data de Liquidacao da Venda`, `PU`, `Quantidade` e `Valor`
- **THEN** o sistema NÃO SHALL inferir o delimitador por `csv.Sniffer`

#### Scenario: Encoding alternativo

- **WHEN** a leitura em UTF-8 falha
- **THEN** o sistema SHALL tentar Latin-1 antes de levantar erro

#### Scenario: Colunas são mapeadas sem caixa/acentos

- **WHEN** o cabeçalho contém variações de caixa ou acentuação dos nomes esperados
- **THEN** o sistema SHALL mapear as colunas corretamente

#### Scenario: Colunas desconhecidas são ignoradas

- **WHEN** o CSV contém colunas fora do conjunto esperado
- **THEN** o sistema SHALL registrar um aviso e ignorar essas colunas

#### Scenario: Coluna obrigatória ausente

- **WHEN** uma coluna obrigatória não está no cabeçalho
- **THEN** o sistema SHALL levantar `TesouroDataError` identificando a coluna ausente

#### Scenario: Datas são convertidas

- **WHEN** uma data `DD/MM/YYYY` é lida
- **THEN** o sistema SHALL convertê-la para ISO `AAAA-MM-DD`
- **THEN** uma data inválida SHALL gerar `TesouroDataError` com linha e coluna

#### Scenario: Decimais com vírgula

- **WHEN** um campo monetário ou de quantidade usa vírgula decimal
- **THEN** o sistema SHALL convertê-lo para `Decimal`
- **THEN** o sistema SHALL aceitar ponto como separador de milhar quando houver vírgula

#### Scenario: Valor numérico inválido

- **WHEN** um campo não pode ser convertido
- **THEN** o sistema SHALL levantar `TesouroDataError` indicando a linha e a coluna

#### Scenario: CSV vazio

- **WHEN** o conteúdo não tem registros além do cabeçalho
- **THEN** o sistema SHALL levantar `TesouroDataError`
- **THEN** nenhum cache SHALL ser gravado

#### Scenario: Duplicatas são preservadas

- **WHEN** duas linhas têm o mesmo `tipo_titulo`, `vencimento` e `data_liquidacao`
- **THEN** ambas SHALL permanecer no resultado
- **THEN** o sistema NÃO SHALL deduplicar

### Requirement: Filtros, agregação e ordenação

O sistema SHALL oferecer funções puras para filtrar por título, filtrar por período, agregar por título e ordenar os registros.

O filtro de título SHALL ser parcial e sem distinção de caixa/acentos. O filtro de período SHALL ser inclusivo sobre `data_liquidacao`. A agregação SHALL somar `quantidade` e `valor` por título e calcular o `PU` médio ponderado por `valor / quantidade`. A ordenação SHALL ser `data_liquidacao` desc, `tipo_titulo` asc, `vencimento` asc e `pu` asc.

#### Scenario: Filtro por título

- **WHEN** o usuário filtra por parte do nome de um título
- **THEN** o sistema SHALL retornar apenas os registros correspondentes

#### Scenario: Filtro por período

- **WHEN** o usuário informa início e fim
- **THEN** o sistema SHALL retornar registros com `data_liquidacao` dentro do intervalo inclusivo

#### Scenario: Agregação por título

- **WHEN** os registros são agregados
- **THEN** o resultado SHALL conter o total de `quantidade` e `valor` de cada título
- **THEN** o `PU` médio SHALL ser `valor_total / quantidade_total`
- **THEN** o `PU` NÃO SHALL ser somado

#### Scenario: Ordenação determinística

- **WHEN** os registros são exibidos
- **THEN** eles SHALL seguir a ordenação definida
- **THEN** a ordem do CSV de origem NÃO SHALL ser usada como garantia

### Requirement: Formatação CSV e JSON

O sistema SHALL formatar vendas em CSV e JSON. O CSV SHALL usar `;`, decimal `.`, datas ISO e os cabeçalhos de vendas/agregado. O JSON SHALL conter os metadados do dataset, `registros` ou `agregados` e valores monetários como strings.

#### Scenario: CSV é gerado

- **WHEN** os registros são formatados como CSV
- **THEN** o cabeçalho SHALL corresponder ao schema confirmado
- **THEN** os valores numéricos SHALL usar separador decimal `.`
- **THEN** `PU` SHALL ter 6 casas; `quantidade` e `valor`, 2 casas

#### Scenario: CSV agregado é gerado

- **WHEN** os registros são agregados
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`

#### Scenario: JSON é gerado

- **WHEN** os registros são formatados como JSON
- **THEN** o payload SHALL conter os metadados e a lista de registros
- **THEN** os valores monetários SHALL ser strings com ponto decimal

#### Scenario: JSON agregado é gerado

- **WHEN** a agregação é solicitada
- **THEN** o payload SHALL usar `agregados` no lugar de `registros`

#### Scenario: Período sem registros

- **WHEN** o filtro de período não encontra registros
- **THEN** o resultado SHALL ser vazio, sem erro de transporte

### Requirement: Classificação de erros e logging

O sistema SHALL distinguir falhas de comunicação de erros de dados. Falhas de rede, HTTP, timeout, corpo vazio/parcial e resposta não-CSV SHALL usar `CommunicationError`. CSV malformado, colunas ausentes, datas/valores inválidos e CSV vazio SHALL usar `TesouroDataError`.

Falhas esperadas SHALL ser registradas em uma única linha, sem traceback. Exceções inesperadas SHALL ser registradas com traceback completo.

#### Scenario: Falha de comunicação é recuperável

- **WHEN** o download falha por rede ou HTTP
- **THEN** o erro SHALL ser classificado como `CommunicationError`
- **THEN** a mensagem de log SHALL ocupar uma única linha

#### Scenario: Erro de dados não é falha de transporte

- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** o resultado SHALL ser `TesouroDataError`
- **THEN** o erro NÃO SHALL ser classificado como `CommunicationError`

### Requirement: Processamento headless

O processamento, os filtros, a agregação, a ordenação e a formatação SHALL residir na camada `application` e NÃO SHALL importar `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede.

#### Scenario: Processamento sem display

- **WHEN** um teste exercita o processamento e os filtros
- **THEN** ele SHALL importar apenas módulos de `application` e `domain`
- **THEN** nenhuma janela ou figura SHALL ser criada

#### Scenario: Aplicação não conhece a presentation

- **WHEN** os módulos de processamento são importados
- **THEN** nenhum módulo de `presentation` ou `infrastructure` SHALL ser necessário
