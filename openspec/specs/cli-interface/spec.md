# CLI Interface

## Purpose

Define a interface de linha de comando baseada em subcomandos de verbo, com parâmetros comuns, seleção de representação da curva, atualização da evolução, exportação de artefatos e códigos de retorno previsíveis.

## Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `gui` e `criar-atalho`.

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
