## MODIFIED Requirements

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

## ADDED Requirements

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
