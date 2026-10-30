## MODIFIED Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `mcp`, `tesouro`, `gui` e `criar-atalho`.

#### Scenario: Execução sem argumentos abre a GUI
- **WHEN** o usuário executa `b3-selic-pre` sem argumentos
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Subcomando gui abre a GUI
- **WHEN** o usuário executa `b3-selic-pre gui`
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Ajuda lista os subcomandos
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar os subcomandos disponíveis e seus parâmetros

## ADDED Requirements

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
