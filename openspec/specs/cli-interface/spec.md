# CLI Interface

## Purpose

Define a interface de linha de comando baseada em subcomandos de verbo, com parâmetros comuns, seleção de representação da curva, atualização da evolução, exportação de artefatos e códigos de retorno previsíveis.

## Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `mcp`, `tesouro`, `tesouro-resgates`, `tesouro-estoque`, `gui` e `criar-atalho`.

#### Scenario: Execução sem argumentos abre a GUI
- **WHEN** o usuário executa `b3-selic-pre` sem argumentos
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Subcomando gui abre a GUI
- **WHEN** o usuário executa `b3-selic-pre gui`
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Ajuda lista os subcomandos
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar os subcomandos disponíveis e seus parâmetros

### Requirement: Remoção da sintaxe legada

A CLI SHALL rejeitar a sintaxe antiga baseada em data posicional e nas flags `--today`, `--yearly`, `--gui`, `--create-shortcut` e `--no-cache` no nível raiz.

#### Scenario: Data posicional é rejeitada
- **WHEN** o usuário executa `b3-selic-pre 2026-06-10`
- **THEN** a CLI SHALL encerrar com código de uso `2` e exibir a mensagem de ajuda

#### Scenario: Flag antiga é rejeitada
- **WHEN** o usuário executa `b3-selic-pre --gui` ou `b3-selic-pre <data> --yearly`
- **THEN** a CLI SHALL encerrar com código de uso `2` e exibir a mensagem de ajuda

### Requirement: Parâmetro comum de data

Os subcomandos `consultar`, `atualizar` e `exportar` SHALL aceitar `--data AAAA-MM-DD`, com a data local corrente como valor padrão.

A data SHALL ser validada no formato `AAAA-MM-DD`, NÃO SHALL estar no futuro e SHALL respeitar a janela máxima de histórico de 30 dias. Se a data cair em fim de semana, a CLI SHALL usar a data útil anterior.

#### Scenario: Data omitida usa hoje
- **WHEN** o usuário executa `atualizar` sem `--data`
- **THEN** a CLI SHALL usar a data local corrente

#### Scenario: Data inválida é rejeitada
- **WHEN** o usuário informa uma data fora do formato `AAAA-MM-DD`
- **THEN** a CLI SHALL encerrar com código `2` e não SHALL consultar a B3

#### Scenario: Data futura é rejeitada
- **WHEN** o usuário informa uma data posterior à data corrente
- **THEN** a CLI SHALL encerrar com código `2` e não SHALL consultar a B3

#### Scenario: Data antiga é rejeitada
- **WHEN** o usuário informa uma data anterior à janela de 30 dias
- **THEN** a CLI SHALL encerrar com código `2` e não SHALL consultar a B3

#### Scenario: Fim de semana é ajustado
- **WHEN** a data informada cai em sábado ou domingo
- **THEN** a CLI SHALL usar a sexta-feira anterior como data de referência

### Requirement: Parâmetro comum de cache

Os subcomandos `consultar`, `atualizar` e `exportar` SHALL aceitar `--no-cache`. Quando presente, a CLI SHALL ignorar o cache em disco e buscar os dados na B3.

#### Scenario: Cache ignorado
- **WHEN** o usuário executa `consultar --data 2026-06-10 --no-cache`
- **THEN** a CLI SHALL buscar as taxas na B3 mesmo que exista entrada em cache

### Requirement: Seleção de curva no subcomando consultar

O subcomando `consultar` SHALL aceitar `--curva curta|longa|ambas`, com `curta` como padrão.

- `curta` SHALL produzir a tabela bruta da data de referência com as colunas `DU252,DC365,TAXA`.
- `longa` SHALL produzir a tabela consolidada por ano com as colunas `ANO,MENOR_TAXA,MAIOR_TAXA`.
- `ambas` SHALL produzir as duas tabelas no stdout, cada uma precedida por um cabeçalho que identifica a representação.

#### Scenario: Curva curta é o padrão
- **WHEN** o usuário executa `consultar --data 2026-06-10` sem `--curva`
- **THEN** a saída SHALL ser a tabela bruta `DU252,DC365,TAXA`

#### Scenario: Curva longa produz consolidado
- **WHEN** o usuário executa `consultar --data 2026-06-10 --curva longa`
- **THEN** a saída SHALL ser a tabela `ANO,MENOR_TAXA,MAIOR_TAXA`

#### Scenario: Curva ambas produz as duas tabelas
- **WHEN** o usuário executa `consultar --data 2026-06-10 --curva ambas`
- **THEN** a saída SHALL conter a tabela bruta e a tabela consolidada, identificadas por cabeçalhos

### Requirement: Subcomando atualizar

O subcomando `atualizar` SHALL carregar a curva da data de referência e a janela de evolução de cinco datas, gerar o texto determinístico da análise da curva e o texto da evolução da curva, e imprimir ambos no stdout.

O comando SHALL aceitar `--silencioso`. Quando presente, ele SHALL apenas carregar e armazenar os dados em cache, sem imprimir a análise.

O subcomando `atualizar` NÃO SHALL aceitar `--curva`; ele SHALL sempre carregar as representações curta e longa da evolução.

#### Scenario: Atualização carrega curva e evolução
- **WHEN** o usuário executa `atualizar --data 2026-06-10`
- **THEN** a CLI SHALL carregar a curva da data e as cinco datas da evolução

#### Scenario: Atualização imprime a análise
- **WHEN** a carga de `atualizar` conclui com dados disponíveis
- **THEN** a saída SHALL conter o texto da análise da curva e o texto da evolução da curva

#### Scenario: Modo silencioso não imprime análise
- **WHEN** o usuário executa `atualizar --silencioso`
- **THEN** a CLI SHALL carregar os dados e NÃO SHALL imprimir a análise no stdout

#### Scenario: Data histórica indisponível é omitida da evolução
- **WHEN** uma ou mais datas da janela de evolução não retornam dados
- **THEN** a análise SHALL usar as datas disponíveis e a saída SHALL identificar as datas indisponíveis

### Requirement: Seleção de conteúdo no subcomando exportar

O subcomando `exportar` SHALL permitir selecionar, de forma combinável, os seguintes conteúdos:

- `--curva curta|longa|ambas`: dados da evolução da curva;
- `--analise`: texto determinístico da análise da curva e da evolução;
- `--log`: cópia do log ativo da aplicação no momento da exportação.

O comando SHALL exigir ao menos um conteúdo selecionado.

#### Scenario: Exportação exige conteúdo
- **WHEN** o usuário executa `exportar --data 2026-06-10` sem `--curva`, `--analise` ou `--log`
- **THEN** a CLI SHALL encerrar com código `2` e exibir a mensagem de ajuda

#### Scenario: Exportação combina conteúdos
- **WHEN** o usuário executa `exportar --curva ambas --analise --log`
- **THEN** a CLI SHALL produzir os dois CSVs de evolução, o texto de análise e a cópia do log

### Requirement: Formatos dos artefatos de exportação

- A curva curta SHALL ser exportada como CSV com delimitador `;` e colunas `DATA;DU252;DC365;TAXA`, uma linha por registro por data.
- A curva longa SHALL ser exportada como CSV com delimitador `;` e colunas `DATA;ANO;TAXA_MEDIA`.
- A análise SHALL ser exportada como texto com seções identificando a análise da curva e a evolução.
- O log SHALL ser exportado como cópia do arquivo ativo `b3-selic-pre.log`.

#### Scenario: Curva curta exporta todos os registros históricos
- **WHEN** `exportar --curva curta` é executado com cinco datas disponíveis
- **THEN** o CSV SHALL conter uma linha para cada registro de cada data, ordenado por data e dia útil

#### Scenario: Curva longa exporta média por ano
- **WHEN** `exportar --curva longa` é executado
- **THEN** o CSV SHALL conter uma linha por ano por data, com a taxa média

#### Scenario: Análise exportada contém os dois textos
- **WHEN** `exportar --analise` é executado com dados atuais e históricos
- **THEN** o arquivo de texto SHALL conter a análise da curva e a análise da evolução

### Requirement: Regras de saída do subcomando exportar

Quando exatamente um artefato for selecionado e `--saida` não for informado, a CLI SHALL imprimir o artefato no stdout.

Quando mais de um artefato for selecionado, a CLI SHALL exigir que `--saida` seja um diretório e SHALL gravar um arquivo por artefato, usando os nomes `curva-curta.csv`, `curva-longa.csv`, `analise.txt` e `b3-selic-pre.log`.

Quando `--saida` apontar para um arquivo e mais de um artefato for selecionado, a CLI SHALL encerrar com código `2`.

#### Scenario: Um artefato vai para stdout
- **WHEN** o usuário executa `exportar --curva longa` sem `--saida`
- **THEN** o CSV SHALL ser impresso no stdout

#### Scenario: Vários artefatos exigem diretório
- **WHEN** o usuário executa `exportar --curva ambas --analise` sem `--saida` de diretório
- **THEN** a CLI SHALL encerrar com código `2`

#### Scenario: Arquivos são gravados no diretório
- **WHEN** o usuário executa `exportar --curva ambas --analise --log --saida exports/`
- **THEN** os arquivos `curva-curta.csv`, `curva-longa.csv`, `analise.txt` e `b3-selic-pre.log` SHALL ser criados em `exports/`

### Requirement: Versão e códigos de retorno

A CLI SHALL aceitar `--version` e SHALL imprimir `b3-selic-pre <versão>` com código `0`.

A CLI SHALL usar os seguintes códigos de retorno:

- `0` para sucesso, incluindo `--help` e `--version`;
- `1` para falha de comunicação ou de dados;
- `2` para erro de uso ou de validação.

#### Scenario: Versão é exibida
- **WHEN** o usuário executa `b3-selic-pre --version`
- **THEN** a saída SHALL ser `b3-selic-pre <versão>` e o código de retorno SHALL ser `0`

#### Scenario: Falha de comunicação retorna 1
- **WHEN** uma consulta falha por comunicação com a B3
- **THEN** a CLI SHALL imprimir uma mensagem em stderr e encerrar com código `1`

#### Scenario: Erro de validação retorna 2
- **WHEN** o usuário informa uma data inválida ou uma combinação de parâmetros inválida
- **THEN** a CLI SHALL encerrar com código `2`

### Requirement: Subcomando mcp

A CLI SHALL aceitar o subcomando `mcp`, que inicia o servidor MCP via `stdio`. O subcomando SHALL aceitar os parâmetros opcionais `--atualizar` e `--data AAAA-MM-DD`.

O subcomando `mcp` NÃO SHALL aceitar `--no-cache`, `--curva`, `--analise`, `--log` ou `--saida`. A ajuda da CLI SHALL listar o subcomando e seus parâmetros.

#### Scenario: Ajuda lista o subcomando mcp

- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `mcp`
- **THEN** a ajuda do subcomando SHALL listar `--atualizar` e `--data`

#### Scenario: Parâmetro não suportado é rejeitado

- **WHEN** o usuário executa `b3-selic-pre mcp --no-cache`
- **THEN** a CLI SHALL encerrar com código de uso `2`

#### Scenario: Preparação com data

- **WHEN** o usuário executa `b3-selic-pre mcp --data 2026-06-10`
- **THEN** a CLI SHALL preparar os dados de 2026-06-10 antes de iniciar o servidor

### Requirement: Subcomando tesouro

A CLI SHALL aceitar o subcomando `tesouro`, que consulta as vendas do Tesouro Direto a partir do cache local ou de um download.

O subcomando SHALL aceitar `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json`, `--no-cache` e `--saida`.

#### Scenario: Ajuda lista o subcomando
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro`
- **THEN** a ajuda do subcomando SHALL listar todas as opções aceitas

#### Scenario: Flag raiz legada é rejeitada
- **WHEN** o usuário executa `b3-selic-pre --tesouro`
- **THEN** a CLI SHALL encerrar com código de uso `2`
- **THEN** a CLI SHALL exibir a mensagem de ajuda

### Requirement: Filtros do subcomando tesouro

O filtro `--titulo` SHALL ser parcial, sem distinção de caixa ou acentuação. `--inicio` e `--fim` SHALL ser inclusivos, no formato `AAAA-MM-DD`, sobre `data_liquidacao`.

Sem datas, o período SHALL ser de 30 dias até a maior `data_liquidacao` disponível. Datas SHALL ser usadas exatamente como informadas, sem ajuste para dia útil. `--inicio` maior que `--fim` SHALL ser erro de uso.

#### Scenario: Consulta com filtros
- **WHEN** o usuário executa `b3-selic-pre tesouro --titulo "Selic" --inicio 2026-01-01 --fim 2026-06-30`
- **THEN** a saída SHALL conter apenas as vendas correspondentes ao título e ao período de liquidação

#### Scenario: Período padrão
- **WHEN** o usuário executa `b3-selic-pre tesouro` sem `--inicio` e `--fim`
- **THEN** a saída SHALL cobrir os últimos 30 dias até a maior `data_liquidacao` disponível

#### Scenario: Datas são exatas
- **WHEN** o usuário informa `--inicio` ou `--fim` em um fim de semana ou feriado
- **THEN** a CLI SHALL usar a data exatamente como informada
- **THEN** a CLI NÃO SHALL ajustar para o dia útil mais próximo

#### Scenario: Período invertido
- **WHEN** o usuário informa `--inicio` maior que `--fim`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Data inválida
- **WHEN** o usuário informa uma data fora do formato `AAAA-MM-DD`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum download SHALL ser iniciado

### Requirement: Saída do subcomando tesouro

Sem `--json`, a saída SHALL ser CSV com delimitador `;`, datas ISO e separador decimal `.`. Com `--json`, a saída SHALL ser um payload estruturado com metadados e `registros` ou `agregados`.

`--agregar` SHALL agrupar por título. Período vazio SHALL produzir cabeçalho CSV ou lista vazia no JSON, com código `0`.

#### Scenario: Saída CSV
- **WHEN** o usuário executa `b3-selic-pre tesouro` sem `--json`
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR`
- **THEN** os valores numéricos SHALL usar separador decimal `.`

#### Scenario: Saída agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro --agregar`
- **THEN** o cabeçalho CSV SHALL ser `TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`

#### Scenario: Saída JSON
- **WHEN** o usuário executa `b3-selic-pre tesouro --json`
- **THEN** o objeto JSON SHALL conter `fonte`, `origem`, `dataset`, `resource_id`, `data_extracao`, `publicado_em`, `data_maxima_liquidacao`, `total_registros`, `periodo` e `registros`
- **THEN** os valores monetários SHALL ser strings com ponto decimal

#### Scenario: Saída JSON agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro --json --agregar`
- **THEN** o objeto JSON SHALL conter `agregados` no lugar de `registros`
- **THEN** SHALL incluir `total_agregados`

#### Scenario: Período sem registros
- **WHEN** o filtro não encontra registros
- **THEN** a CLI SHALL imprimir o cabeçalho CSV (ou lista vazia no JSON)
- **THEN** a CLI SHALL encerrar com código `0`

### Requirement: Exportação do subcomando tesouro

`--saida` SHALL gravar o artefato em vez de imprimi-lo no stdout. Se o caminho for um diretório, a CLI SHALL usar `tesouro-vendas.csv` ou `tesouro-vendas.json`; se for arquivo, SHALL gravar nesse caminho. Com `--agregar`, o nome padrão SHALL receber o sufixo `-agregado`.

Falha de escrita SHALL produzir código `1` e mensagem em `stderr`.

#### Scenario: Exportação para arquivo
- **WHEN** o usuário executa `b3-selic-pre tesouro --saida vendas.csv`
- **THEN** o CSV SHALL ser gravado em `vendas.csv`
- **THEN** nada SHALL ser impresso no stdout

#### Scenario: Exportação para diretório
- **WHEN** o usuário executa `b3-selic-pre tesouro --saida exports/`
- **THEN** o arquivo `exports/tesouro-vendas.csv` SHALL ser criado

#### Scenario: Exportação JSON
- **WHEN** o usuário executa `b3-selic-pre tesouro --json --saida exports/`
- **THEN** o arquivo `exports/tesouro-vendas.json` SHALL ser criado

#### Scenario: Exportação agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro --agregar --saida exports/`
- **THEN** o arquivo `exports/tesouro-vendas-agregado.csv` SHALL ser criado

#### Scenario: Falha de escrita
- **WHEN** o caminho de `--saida` não pode ser gravado
- **THEN** a CLI SHALL imprimir uma mensagem em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

### Requirement: Erros e códigos do subcomando tesouro

Os códigos SHALL ser `0` para sucesso, `1` para falha de comunicação ou de dados e `2` para erro de uso ou validação.

`--no-cache` SHALL forçar uma verificação condicional; `304` SHALL reutilizar o cache. Falha de rede/HTTP SHALL produzir código `1`; CSV inválido SHALL produzir código `1`.

#### Scenario: Forçar download
- **WHEN** o usuário executa `b3-selic-pre tesouro --no-cache`
- **THEN** a CLI SHALL fazer uma verificação condicional na rede mesmo que exista cache válido
- **THEN** uma resposta `304` SHALL reutilizar o cache

#### Scenario: Falha de comunicação
- **WHEN** o download falha por rede ou HTTP
- **THEN** a CLI SHALL imprimir uma mensagem em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

#### Scenario: Erro de dados
- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** a CLI SHALL imprimir uma mensagem de dados em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

### Requirement: Seleção da representação da análise no exportar

O subcomando `exportar` SHALL aceitar `--analise-curva curta|longa`, com `curta` como valor efetivo padrão. A opção SHALL selecionar a representação usada no texto da análise e NÃO SHALL alterar a seleção de artefatos de `--curva`.

`--analise-curva` SHALL ser válido apenas junto com `--analise`. Quando informado sem `--analise`, a CLI SHALL encerrar com código de uso `2`.

A análise da curva longa SHALL usar a taxa média por ano. A análise da curva curta SHALL usar os registros brutos. A opção NÃO SHALL alterar o formato dos CSVs de `--curva`.

#### Scenario: Análise longa

- **WHEN** o usuário executa `b3-selic-pre exportar --analise --analise-curva longa`
- **THEN** o artefato `analise.txt` SHALL conter a análise calculada sobre a taxa média por ano

#### Scenario: Análise curta é o padrão

- **WHEN** o usuário executa `b3-selic-pre exportar --analise`
- **THEN** o artefato `analise.txt` SHALL conter a análise calculada sobre os registros brutos

#### Scenario: Opção sem análise é rejeitada

- **WHEN** o usuário executa `b3-selic-pre exportar --curva curta --analise-curva longa` sem `--analise`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum arquivo SHALL ser gravado

#### Scenario: Curva e análise são independentes

- **WHEN** o usuário executa `b3-selic-pre exportar --curva longa --analise --analise-curva curta`
- **THEN** o CSV SHALL conter a evolução consolidada
- **THEN** a análise SHALL usar os registros brutos

### Requirement: Subcomando tesouro-resgates

A CLI SHALL aceitar o subcomando `tesouro-resgates`, que consulta recompras, cupons e vencimentos do Tesouro Direto.

O subcomando SHALL aceitar `--tipo recompra|cupom|vencimento`, `--titulo`, `--inicio`, `--fim`, `--agregar`, `--json`, `--no-cache` e `--saida`.

#### Scenario: Ajuda lista o subcomando
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro-resgates`
- **THEN** a ajuda do subcomando SHALL listar todas as opções aceitas

#### Scenario: Consulta por tipo
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --tipo recompra`
- **THEN** a saída SHALL conter apenas recompras

### Requirement: Filtros do subcomando tesouro-resgates

`--tipo` SHALL filtrar pelo tipo de resgate; sem ele, todos os tipos SHALL ser consultados. `--titulo` SHALL ser parcial, sem caixa/acentos. `--inicio` e `--fim` SHALL ser inclusivos sobre `data_resgate`, no formato `AAAA-MM-DD`.

Sem datas, o período SHALL ser de 30 dias até a maior `data_resgate` disponível. `--inicio` maior que `--fim` SHALL ser erro de uso.

#### Scenario: Período padrão
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates` sem `--inicio` e `--fim`
- **THEN** a saída SHALL cobrir os últimos 30 dias até a maior `data_resgate` disponível

#### Scenario: Filtro por título
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --titulo "IPCA"`
- **THEN** a saída SHALL conter apenas resgates cujo título corresponde parcialmente

#### Scenario: Período invertido
- **WHEN** o usuário informa `--inicio` maior que `--fim`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhum download SHALL ser iniciado

### Requirement: Saída do subcomando tesouro-resgates

Sem `--json`, a saída SHALL ser CSV com delimitador `;`, datas ISO e decimal `.`. Com `--json`, o payload SHALL conter `dataset: "resgates"` e `registros` ou `agregados`.

`--agregar` SHALL agrupar por tipo de resgate e título. Período vazio SHALL produzir cabeçalho CSV ou lista vazia no JSON, com código `0`.

#### Scenario: Saída CSV
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates` sem `--json`
- **THEN** o cabeçalho SHALL ser `TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;PU;QUANTIDADE;VALOR`

#### Scenario: Saída agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --agregar`
- **THEN** o cabeçalho SHALL ser `TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`

#### Scenario: Saída JSON
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --json`
- **THEN** o payload SHALL conter `dataset: "resgates"` e `registros` ou `agregados`

#### Scenario: Período sem registros
- **WHEN** o filtro não encontra resgates
- **THEN** a CLI SHALL imprimir o cabeçalho CSV (ou lista vazia no JSON)
- **THEN** a CLI SHALL encerrar com código `0`

### Requirement: Exportação do subcomando tesouro-resgates

`--saida` SHALL gravar o artefato em vez de imprimi-lo no stdout. Se o caminho for um diretório, a CLI SHALL usar `tesouro-resgates.csv` ou `tesouro-resgates.json`; com `--agregar`, o nome SHALL receber o sufixo `-agregado`.

Falha de escrita SHALL produzir código `1` e mensagem em `stderr`.

#### Scenario: Exportação para arquivo
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --saida resgates.csv`
- **THEN** o CSV SHALL ser gravado em `resgates.csv`

#### Scenario: Exportação para diretório
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --json --saida exports/`
- **THEN** o arquivo `exports/tesouro-resgates.json` SHALL ser criado

#### Scenario: Exportação agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --agregar --saida exports/`
- **THEN** o arquivo `exports/tesouro-resgates-agregado.csv` SHALL ser criado

#### Scenario: Falha de escrita
- **WHEN** o caminho de `--saida` não pode ser gravado
- **THEN** a CLI SHALL imprimir uma mensagem em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

### Requirement: Erros do subcomando tesouro-resgates

Os códigos SHALL ser `0` para sucesso, `1` para falha de comunicação ou de dados e `2` para erro de uso ou validação. `--no-cache` SHALL forçar verificação condicional; `304` SHALL reutilizar o cache.

#### Scenario: Erro de dados
- **WHEN** um recurso tem colunas ausentes ou valores inválidos
- **THEN** a CLI SHALL imprimir uma mensagem de dados em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

#### Scenario: Forçar download
- **WHEN** o usuário executa `b3-selic-pre tesouro-resgates --no-cache`
- **THEN** a CLI SHALL fazer uma verificação condicional
- **THEN** uma resposta `304` SHALL reutilizar o cache

### Requirement: Subcomando tesouro-estoque

A CLI SHALL aceitar o subcomando `tesouro-estoque`, que consulta o estoque mensal do Tesouro Direto.

O subcomando SHALL aceitar `--titulo`, `--inicio`, `--fim`, `--mes`, `--agregar`, `--json`, `--no-cache` e `--saida`.

#### Scenario: Ajuda lista o subcomando
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `tesouro-estoque`
- **THEN** a ajuda do subcomando SHALL listar todas as opções aceitas

#### Scenario: Último mês é o padrão
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque` sem filtros
- **THEN** a saída SHALL conter apenas o último mês disponível

### Requirement: Filtros do subcomando tesouro-estoque

`--titulo` SHALL ser parcial, sem caixa/acentos. `--inicio` e `--fim` SHALL usar `AAAA-MM` e ser inclusivos. `--mes` SHALL selecionar um único mês.

#### Scenario: Intervalo de meses
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --inicio 2025-01 --fim 2025-12`
- **THEN** a saída SHALL conter os meses do intervalo inclusivo

#### Scenario: Filtro por título
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --titulo "Selic"`
- **THEN** a saída SHALL conter apenas títulos correspondentes

### Requirement: Saída do subcomando tesouro-estoque

Sem `--json`, a saída SHALL ser CSV com delimitador `;`, mês `AAAA-MM` e decimal `.`. Com `--json`, o payload SHALL conter `dataset: "estoque"` e `registros` ou `agregados`.

`--agregar` SHALL exigir um único mês e SHALL agrupar por título. A soma de `valor_estoque` entre meses NÃO SHALL ser permitida.

#### Scenario: Saída CSV
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque` sem `--json`
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE`

#### Scenario: Agregação exige um mês
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --agregar` com `--inicio`/`--fim` cobrindo mais de um mês
- **THEN** a CLI SHALL encerrar com código `2`

#### Scenario: Saída agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --mes 2026-08 --agregar`
- **THEN** o cabeçalho SHALL ser `TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO`

#### Scenario: Saída JSON
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --json`
- **THEN** o payload SHALL conter `dataset: "estoque"` e `registros` ou `agregados`

### Requirement: Exportação do subcomando tesouro-estoque

`--saida` SHALL gravar o artefato em vez de imprimi-lo no stdout. Se o caminho for um diretório, a CLI SHALL usar `tesouro-estoque.csv` ou `tesouro-estoque.json`; com `--agregar`, o nome SHALL receber o sufixo `-agregado`.

Falha de escrita SHALL produzir código `1` e mensagem em `stderr`.

#### Scenario: Exportação para arquivo
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --saida estoque.csv`
- **THEN** o CSV SHALL ser gravado em `estoque.csv`

#### Scenario: Exportação para diretório
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --json --saida exports/`
- **THEN** o arquivo `exports/tesouro-estoque.json` SHALL ser criado

#### Scenario: Exportação agregada
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --mes 2026-08 --agregar --saida exports/`
- **THEN** o arquivo `exports/tesouro-estoque-agregado.csv` SHALL ser criado

#### Scenario: Falha de escrita
- **WHEN** o caminho de `--saida` não pode ser gravado
- **THEN** a CLI SHALL imprimir uma mensagem em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

### Requirement: Erros do subcomando tesouro-estoque

Os códigos SHALL ser `0` para sucesso, `1` para falha de comunicação ou de dados e `2` para erro de uso ou validação. `--no-cache` SHALL forçar verificação condicional; `304` SHALL reutilizar o cache.

#### Scenario: Erro de dados
- **WHEN** o recurso tem colunas ausentes ou valores inválidos
- **THEN** a CLI SHALL imprimir uma mensagem de dados em `stderr`
- **THEN** a CLI SHALL encerrar com código `1`

#### Scenario: Forçar download
- **WHEN** o usuário executa `b3-selic-pre tesouro-estoque --no-cache`
- **THEN** a CLI SHALL fazer uma verificação condicional
- **THEN** uma resposta `304` SHALL reutilizar o cache
