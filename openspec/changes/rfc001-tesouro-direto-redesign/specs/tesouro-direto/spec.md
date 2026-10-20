## Purpose

Descrever a aquisição, o cache, o processamento e a formatação dos dados do Tesouro Direto, usando a API CKAN, a biblioteca padrão e sem depender da presentation.

## ADDED Requirements

### Requirement: Descoberta do dataset via API CKAN

O sistema SHALL descobrir o dataset do Tesouro Direto por meio da API CKAN JSON, sem scraping de HTML. A resposta SHALL fornecer os metadados do dataset e a URL do recurso CSV.

O recurso PDF de metadados NÃO SHALL ser extraído nesta change, pois não é consumido por nenhum requisito.

#### Scenario: Metadados são obtidos da API

- **WHEN** o sistema consulta `package_show` no CKAN
- **THEN** a resposta SHALL conter título, autor, versão, data de última atualização e a lista de recursos

#### Scenario: URL do CSV é extraída

- **WHEN** a lista de recursos contém um recurso com formato CSV
- **THEN** o sistema SHALL extrair a URL e o identificador desse recurso

#### Scenario: Recurso CSV ausente

- **WHEN** a lista de recursos não contém um recurso CSV
- **THEN** o sistema SHALL levantar um erro de dados identificando que o CSV não foi encontrado

#### Scenario: Nenhum scraping de HTML

- **WHEN** o sistema descobre o dataset
- **THEN** ele SHALL usar apenas JSON da API CKAN
- **THEN** ele NÃO SHALL interpretar HTML da página do portal

### Requirement: Download do CSV com retry e cabeçalhos condicionais

O sistema SHALL baixar o CSV com `urllib`, lendo a resposta em chunks e respeitando um timeout configurável (padrão de 60 segundos).

O download SHALL usar `ETag`/`If-Modified-Since` quando disponíveis. Uma resposta `304 Not Modified` SHALL reutilizar o cache existente. Falhas de rede, HTTP ou corpo vazio após os retries SHALL ser sinalizadas como `CommunicationError`.

#### Scenario: Download bem-sucedido

- **WHEN** a URL do CSV responde com HTTP 200 e conteúdo válido
- **THEN** o sistema SHALL obter o conteúdo em chunks
- **THEN** o conteúdo SHALL ser validado antes de substituir o cache

#### Scenario: Resposta 304 reutiliza o cache

- **WHEN** o servidor responde `304 Not Modified`
- **THEN** o sistema SHALL reutilizar o CSV já armazenado
- **THEN** nenhuma nova gravação SHALL ocorrer

#### Scenario: Cabeçalhos são armazenados

- **WHEN** um download conclui com sucesso
- **THEN** o sistema SHALL armazenar `ETag` e `Last-Modified` nos metadados do cache

#### Scenario: Falha de comunicação

- **WHEN** ocorre erro de rede, timeout ou status HTTP inválido
- **THEN** o sistema SHALL levantar `CommunicationError`
- **THEN** o cache válido anterior NÃO SHALL ser descartado

#### Scenario: Corpo vazio após retries

- **WHEN** o servidor responde com corpo vazio após todas as tentativas
- **THEN** o sistema SHALL levantar `CommunicationError`
- **THEN** nenhum resultado vazio SHALL ser cacheado

### Requirement: Cache cumulativo atômico

O sistema SHALL manter um único CSV cumulativo e um arquivo de metadados no diretório XDG `.../b3-selic-pre/tesouro/`.

O cache SHALL aplicar TTL de 6 horas, gravação atômica e validação antes da substituição. Um cache corrompido SHALL ser tratado como miss e baixado novamente. O sistema NÃO SHALL manter housekeeping de arquivos datados, pois o dataset é cumulativo.

#### Scenario: Cache válido dentro do TTL

- **WHEN** o CSV em cache é válido e tem menos de 6 horas
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede

#### Scenario: Cache expirado

- **WHEN** o CSV em cache tem 6 horas ou mais
- **THEN** o sistema SHALL tentar um download condicional

#### Scenario: Cache corrompido

- **WHEN** o CSV ou os metadados em cache estão vazios ou inválidos
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

### Requirement: Modelo provisório de registro

O sistema SHALL representar cada registro como um frozen dataclass. A versão preliminar usa `RegistroTesouroDireto` com os campos `data`, `titulo`, `venda`, `resgate`, `saldo` e `vencimento`; o spike bloqueante SHALL confirmar ou renomear o modelo e os campos finais antes da implementação.

#### Scenario: Modelo é imutável

- **WHEN** um registro é criado
- **THEN** seus campos NÃO SHALL ser modificáveis

#### Scenario: Campos provisórios estão acessíveis

- **WHEN** o registro é instanciado com os campos provisórios
- **THEN** todos os campos SHALL estar acessíveis como atributos

#### Scenario: Datas usam formato ISO

- **WHEN** `data` e `vencimento` são preenchidos
- **THEN** eles SHALL ser strings no formato `AAAA-MM-DD`

### Requirement: Parsing e validação do CSV

O sistema SHALL interpretar o CSV usando o módulo `csv` da biblioteca padrão, a partir dos bytes baixados, sem realizar I/O de arquivo ou rede.

O parsing SHALL tentar UTF-8 com BOM, UTF-8 e Latin-1, nessa ordem, e SHALL validar o delimitador e as colunas obrigatórias. O mapeamento de colunas SHALL ignorar diferenças de caixa e acentuação. Linhas inválidas SHALL produzir erros que identifiquem a linha e a coluna.

#### Scenario: Delimitador é validado

- **WHEN** o CSV usa `;` ou `,`
- **THEN** o sistema SHALL detectar e validar o delimitador antes de interpretar as linhas

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
- **THEN** o sistema SHALL levantar um erro de dados identificando a coluna ausente

#### Scenario: Valor numérico inválido

- **WHEN** um campo monetário não pode ser convertido
- **THEN** o sistema SHALL levantar um erro de dados indicando a linha e a coluna

#### Scenario: CSV vazio

- **WHEN** o conteúdo não tem registros além do cabeçalho
- **THEN** o sistema SHALL levantar um erro de dados
- **THEN** nenhum cache SHALL ser gravado

### Requirement: Filtros e agregação

O sistema SHALL oferecer funções puras para filtrar por título, filtrar por período e agregar por título.

O filtro de título SHALL ser parcial e sem distinção de caixa/acentos. O filtro de período SHALL ser inclusivo. A agregação SHALL somar `venda`, `resgate` e `saldo` por título.

#### Scenario: Filtro por título

- **WHEN** o usuário filtra por parte do nome de um título
- **THEN** o sistema SHALL retornar apenas os registros correspondentes

#### Scenario: Filtro por período

- **WHEN** o usuário informa início e fim
- **THEN** o sistema SHALL retornar registros dentro do intervalo inclusivo

#### Scenario: Agregação por título

- **WHEN** os registros são agregados
- **THEN** o resultado SHALL conter o total de `venda`, `resgate` e `saldo` de cada título

### Requirement: Formatação CSV e JSON

O sistema SHALL formatar os registros em CSV para consumo por planilhas e em JSON para consumo estruturado.

O CSV SHALL usar delimitador `;` e separador decimal `.`. O JSON SHALL conter `fonte`, `data_extracao`, `total_registros`, `periodo` e `registros`.

#### Scenario: CSV é gerado

- **WHEN** os registros são formatados como CSV
- **THEN** o cabeçalho SHALL corresponder ao schema confirmado
- **THEN** os valores numéricos SHALL usar separador decimal `.`

#### Scenario: JSON é gerado

- **WHEN** os registros são formatados como JSON
- **THEN** o payload SHALL conter os metadados e a lista de registros

#### Scenario: Período sem registros

- **WHEN** o filtro de período não encontra registros
- **THEN** o resultado SHALL ser vazio, sem erro de transporte

### Requirement: Classificação de erros e logging

O sistema SHALL distinguir falhas de comunicação de erros de dados. Falhas de rede, HTTP, timeout e corpo vazio após retries SHALL usar `CommunicationError`. CSV malformado, colunas ausentes e valores inválidos SHALL usar erro de dados.

Falhas de comunicação SHALL ser registradas em uma única linha, sem traceback. Exceções inesperadas SHALL ser registradas com traceback completo.

#### Scenario: Falha de comunicação é recuperável

- **WHEN** o download falha por rede ou HTTP
- **THEN** o erro SHALL ser classificado como `CommunicationError`
- **THEN** a mensagem de log SHALL ocupar uma única linha

#### Scenario: Erro de dados não é falha de transporte

- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** o resultado SHALL ser um erro de dados
- **THEN** o erro NÃO SHALL ser classificado como `CommunicationError`

### Requirement: Processamento headless

O processamento, os filtros, a agregação e a formatação SHALL residir na camada `application` e NÃO SHALL importar `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede.

#### Scenario: Processamento sem display

- **WHEN** um teste exercita o processamento e os filtros
- **THEN** ele SHALL importar apenas módulos de `application` e `domain`
- **THEN** nenhuma janela ou figura SHALL ser criada

#### Scenario: Aplicação não conhece a presentation

- **WHEN** os módulos de processamento são importados
- **THEN** nenhum módulo de `presentation` ou `infrastructure` SHALL ser necessário
