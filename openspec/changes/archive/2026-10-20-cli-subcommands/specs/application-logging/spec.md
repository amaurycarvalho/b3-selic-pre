## ADDED Requirements

### Requirement: Registro de invocação da CLI

A CLI SHALL gravar exatamente um registro de nível INFO por invocação no arquivo ativo de log, reutilizando o formato, o timestamp local e a rotação diária já definidos para a aplicação.

O registro SHALL conter:

- o comando acionado, incluindo `gui` para a execução sem argumentos e para o subcomando `gui`;
- os argumentos reconhecidos e seus valores em formato chave=valor; quando o parsing falhar, o argv bruto;
- os instantes de início e de término em ISO 8601 com fuso local;
- a duração em segundos;
- o código de saída da invocação.

O registro SHALL ser emitido após a conclusão da invocação, inclusive para `--help`, `--version`, erro de parsing, falha de comunicação e exceção não tratada. Uma falha ao gravar o log NÃO SHALL alterar o código de saída nem impedir a operação da CLI.

#### Scenario: Invocação bem-sucedida registra metadados
- **WHEN** o usuário executa `consultar --data 2026-06-10 --curva longa` com sucesso
- **THEN** o log SHALL conter um registro com `comando=consultar`, os argumentos reconhecidos, início, fim, duração e `codigo_saida=0`

#### Scenario: Erro de parsing é registrado
- **WHEN** o usuário informa um subcomando ou parâmetro inválido
- **THEN** o log SHALL conter um registro com o argv bruto e `codigo_saida=2`

#### Scenario: Execução sem argumentos registra a GUI
- **WHEN** o usuário executa `b3-selic-pre` sem argumentos e fecha a janela normalmente
- **THEN** o log SHALL conter um registro com `comando=gui` e `codigo_saida=0`

#### Scenario: Subcomando gui registra a duração da sessão
- **WHEN** o usuário executa `b3-selic-pre gui` e fecha a janela normalmente
- **THEN** o log SHALL conter um registro com `comando=gui`, duração até o fechamento da janela e `codigo_saida=0`

#### Scenario: Ajuda e versão são registradas
- **WHEN** o usuário executa `b3-selic-pre --help` ou `b3-selic-pre --version`
- **THEN** o log SHALL conter um registro com `codigo_saida=0`

#### Scenario: Falha de comunicação é registrada com código 1
- **WHEN** uma invocação termina com falha de comunicação ou de dados
- **THEN** o log SHALL conter um registro com `codigo_saida=1`

#### Scenario: Exceção não tratada é registrada com código 1
- **WHEN** uma invocação termina com exceção não tratada
- **THEN** o log SHALL conter um registro com `codigo_saida=1`

#### Scenario: Formato e rotação são reutilizados
- **WHEN** o registro de invocação é gravado
- **THEN** a linha SHALL usar o mesmo formato `YYYY-MM-DD HH:MM:SS [LEVEL] logger: mensagem` e o mesmo arquivo ativo diário

#### Scenario: Falha de logging não altera o resultado
- **WHEN** o diretório ou o arquivo de log não pode ser aberto
- **THEN** a CLI SHALL concluir a invocação com o código de saída original

## MODIFIED Requirements

### Requirement: Retenção de backups na inicialização da GUI

Na inicialização da CLI e do modo gráfico, a aplicação SHALL apagar arquivos de backup datados anteriores ao limite de retenção, preservando o dia corrente e os `N` dias anteriores.

#### Scenario: Backups antigos são apagados

- **WHEN** existem arquivos `b3-selic-pre-YYYY-MM-DD.log` com data anterior a `hoje - N` dias
- **THEN** esses arquivos SHALL ser apagados

#### Scenario: Backups dentro da retenção são preservados

- **WHEN** existem arquivos `b3-selic-pre-YYYY-MM-DD.log` com data igual ou posterior a `hoje - N` dias
- **THEN** esses arquivos SHALL ser preservados, incluindo o dia corrente e os `N` dias anteriores

#### Scenario: Arquivo ativo nunca é apagado

- **WHEN** a retenção é executada
- **THEN** `b3-selic-pre.log` NUNCA SHALL ser apagado

#### Scenario: Arquivos fora do padrão não são apagados

- **WHEN** o diretório de logs contém arquivos que não seguem o padrão `b3-selic-pre-YYYY-MM-DD.log`
- **THEN** esses arquivos NÃO SHALL ser apagados

#### Scenario: Rotação anterior à retenção

- **WHEN** a inicialização rotaciona um arquivo ativo antigo e o backup resultante é anterior ao limite de retenção
- **THEN** esse backup SHALL ser considerado pela retenção e apagado na mesma inicialização
