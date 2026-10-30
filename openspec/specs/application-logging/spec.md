# Application Logging

## Purpose

Define um histórico diário de execução da aplicação, com formato consistente, retenção configurável e tratamento uniforme de falhas de comunicação e de defeitos inesperados.

## Requirements

### Requirement: Logging compartilhado entre CLI e GUI

A aplicação SHALL configurar logging para os entry points de CLI e GUI, gravando os registros no mesmo arquivo ativo diário.

#### Scenario: CLI grava no log

- **WHEN** a CLI executa uma busca, com sucesso ou com falha
- **THEN** os registros SHALL ser gravados no arquivo ativo de log

#### Scenario: GUI grava no mesmo log

- **WHEN** a GUI é iniciada
- **THEN** os registros SHALL ser gravados no mesmo arquivo ativo usado pela CLI

#### Scenario: Início de execução registrado

- **WHEN** a aplicação inicia em modo CLI ou GUI
- **THEN** SHALL ser gravado um registro de nível INFO contendo a versão da aplicação e o modo de execução

### Requirement: Formato consistente com timestamp

Todo registro gravado no arquivo de log SHALL conter data e hora locais. O formato da linha e o formato da data SHALL ser definidos de forma centralizada nos argumentos `format` e `datefmt` da configuração de logging, de modo que o mesmo formato valha para todos os handlers usados pela aplicação.

#### Scenario: Registro contém timestamp

- **WHEN** qualquer registro é gravado no arquivo
- **THEN** a linha SHALL conter a data e a hora locais no formato `YYYY-MM-DD HH:MM:SS`

#### Scenario: Formato aplicado a todos os handlers

- **WHEN** a configuração de logging é aplicada
- **THEN** todos os handlers usados pela aplicação SHALL utilizar o mesmo `format` e o mesmo `datefmt`

### Requirement: Arquivo ativo diário

A aplicação SHALL manter um arquivo ativo `b3-selic-pre.log` no diretório de logs, contendo os registros do dia local corrente, e SHALL rotacioná-lo na virada do dia local.

#### Scenario: Arquivo ativo reúne o dia corrente

- **WHEN** a aplicação grava registros durante o dia local corrente
- **THEN** os registros SHALL ser gravados em `b3-selic-pre.log`

#### Scenario: Rotação na virada do dia

- **WHEN** o primeiro registro após a meia-noite local é emitido
- **THEN** o arquivo ativo SHALL ser renomeado para `b3-selic-pre-YYYY-MM-DD.log`, usando a data local do dia encerrado
- **AND** um novo arquivo ativo SHALL ser aberto para os registros seguintes

#### Scenario: Rotação preguiçosa sem atividade

- **WHEN** não há registros após a meia-noite local
- **THEN** a rotação SHALL ocorrer no próximo registro ou na próxima inicialização da aplicação, sem misturar registros de dias distintos no mesmo arquivo

### Requirement: Rotação do arquivo ativo na inicialização

Na inicialização, a aplicação SHALL verificar a data de modificação do arquivo ativo antes de abrir o handler de log.

#### Scenario: Arquivo ativo de dia anterior é rotacionado

- **WHEN** `b3-selic-pre.log` existe e sua data de modificação local é anterior ao dia local corrente
- **THEN** o arquivo SHALL ser renomeado para `b3-selic-pre-YYYY-MM-DD.log`, usando a data local da última modificação
- **AND** um novo arquivo ativo SHALL ser aberto para o dia corrente

#### Scenario: Destino de rotação já existe

- **WHEN** o arquivo de destino `b3-selic-pre-YYYY-MM-DD.log` já existe
- **THEN** o conteúdo do arquivo ativo SHALL ser anexado ao destino
- **AND** o arquivo ativo SHALL ser removido após a cópia

#### Scenario: Arquivo ativo ausente

- **WHEN** `b3-selic-pre.log` não existe na inicialização
- **THEN** nenhuma rotação SHALL ocorrer

#### Scenario: Arquivo ativo já pertence ao dia corrente

- **WHEN** a data de modificação de `b3-selic-pre.log` pertence ao dia local corrente
- **THEN** nenhuma rotação SHALL ocorrer

### Requirement: Registro de invocação da CLI

A CLI SHALL gravar exatamente um registro de nível INFO por invocação no arquivo ativo de log, reutilizando formato, timestamp local e rotação diária.

O registro SHALL conter o comando (`gui` quando aplicável), os argumentos reconhecidos ou o argv bruto em falha de parsing, início e fim em ISO 8601, duração em segundos e código de saída. Ele SHALL ser emitido após a conclusão, inclusive em erro; falha ao gravar o log NÃO SHALL alterar o código de saída.

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

### Requirement: Diretório de logs compatível com XDG e plataforma

A aplicação SHALL armazenar os logs no diretório de cache da plataforma, no subdiretório `b3-selic-pre/logs/`.

#### Scenario: Linux usa XDG_CACHE_HOME

- **WHEN** a aplicação roda no Linux com `XDG_CACHE_HOME` definido
- **THEN** os logs SHALL ser armazenados em `$XDG_CACHE_HOME/b3-selic-pre/logs/`

#### Scenario: Linux sem XDG_CACHE_HOME

- **WHEN** a aplicação roda no Linux sem `XDG_CACHE_HOME`
- **THEN** os logs SHALL ser armazenados em `~/.cache/b3-selic-pre/logs/`

#### Scenario: Outras plataformas usam o cache da plataforma

- **WHEN** a aplicação roda no Windows ou macOS
- **THEN** os logs SHALL ser armazenados no diretório de cache correspondente à plataforma, sob `b3-selic-pre/logs/`

### Requirement: Falhas de comunicação em linha única

Quando uma falha de comunicação de rede/HTTP prevista e tolerada é registrada, a aplicação SHALL escrever uma única linha contendo o tipo e a mensagem da exceção e NÃO SHALL incluir o call stack completo. A classificação SHALL considerar a exceção direta ou encadeada como causa ou contexto.

#### Scenario: Exceção de comunicação direta

- **WHEN** uma exceção de rede/HTTP é registrada
- **THEN** o log SHALL conter uma única linha com o tipo e a mensagem da exceção
- **AND** essa linha NÃO SHALL conter traceback

#### Scenario: Exceção de comunicação encadeada

- **WHEN** uma exceção não-comunicação tem uma exceção de rede/HTTP como causa ou contexto
- **THEN** o log SHALL conter uma única linha com o tipo e a mensagem da exceção de comunicação
- **AND** essa linha NÃO SHALL conter traceback

#### Scenario: Mensagem multilinha é normalizada

- **WHEN** a mensagem da exceção de comunicação contém quebras de linha
- **THEN** o registro SHALL permanecer em uma única linha física

#### Scenario: Exceção que não é de comunicação

- **WHEN** uma exceção que não é de rede/HTTP é registrada
- **THEN** o log SHALL conter o traceback completo da exceção

### Requirement: Tratamento de falhas na CLI

A CLI SHALL registrar falhas de busca e comunicar o resultado ao usuário.

#### Scenario: Falha de comunicação na CLI

- **WHEN** a CLI sofre uma falha de comunicação durante a busca
- **THEN** a falha SHALL ser registrada em linha única no arquivo de log
- **AND** a CLI SHALL imprimir uma mensagem amigável em stderr
- **AND** a CLI SHALL encerrar com código de saída `1`, sem imprimir traceback

#### Scenario: Falha não-comunicação na CLI

- **WHEN** a CLI sofre uma exceção que não é de comunicação durante a busca
- **THEN** a falha SHALL ser registrada com traceback completo no arquivo de log
- **AND** a exceção SHALL ser relançada

### Requirement: Exceções não tratadas

A aplicação SHALL registrar exceções não tratadas com traceback completo, por meio de hooks para a thread principal, threads secundárias e callbacks do Tk.

#### Scenario: Exceção não tratada na thread principal

- **WHEN** uma exceção não tratada alcança `sys.excepthook`
- **THEN** ela SHALL ser registrada no arquivo de log com traceback completo

#### Scenario: Exceção não tratada em thread secundária

- **WHEN** uma exceção não tratada alcança `threading.excepthook`
- **THEN** ela SHALL ser registrada no arquivo de log com traceback completo

#### Scenario: Exceção não tratada em callback do Tk

- **WHEN** um callback do Tk levanta uma exceção não tratada
- **THEN** ela SHALL ser registrada no arquivo de log com traceback completo

### Requirement: Inicialização de logging resiliente

Uma falha ao criar o diretório ou o arquivo de log NÃO SHALL impedir a inicialização ou a operação da aplicação.

#### Scenario: Diretório de logs indisponível

- **WHEN** o diretório de logs não pode ser criado ou o arquivo não pode ser aberto
- **THEN** a aplicação SHALL continuar sua inicialização e operação normal
- **AND** a falha de logging NÃO SHALL ser propagada como erro fatal

### Requirement: Logging do modo MCP em stderr

No modo MCP, a aplicação SHALL escrever logs e diagnósticos em `stderr`, incluindo o progresso da preparação opcional. A aplicação NÃO SHALL gravar no arquivo de log ativo durante o atendimento MCP.

O `stdout` SHALL permanecer exclusivo para mensagens JSON-RPC válidas.

#### Scenario: Progresso da preparação em stderr

- **WHEN** o usuário executa `b3-selic-pre mcp --atualizar`
- **THEN** o progresso da preparação SHALL ser escrito em `stderr`
- **THEN** `stdout` NÃO SHALL receber texto de progresso

#### Scenario: Atendimento não grava log em arquivo

- **WHEN** o servidor MCP está atendendo requisições
- **THEN** os logs e diagnósticos SHALL ir para `stderr`
- **THEN** o arquivo de log ativo NÃO SHALL ser gravado pelo servidor

#### Scenario: Erro de protocolo não corrompe stdout

- **WHEN** ocorre um erro de parsing ou uma falha interna
- **THEN** o diagnóstico SHALL ser escrito em `stderr`
- **THEN** qualquer resposta em `stdout` SHALL ser uma mensagem JSON-RPC válida

### Requirement: Registro de falhas de atualização na GUI

Falhas de leitura de cache, de atualização e de fontes parciais nas sub-abas de dados da interface gráfica SHALL ser registradas no arquivo ativo de log, identificando a sub-aba e a operação afetada.

O registro SHALL seguir a classificação de `Falhas de comunicação em linha única`: falhas de comunicação sem traceback e demais defeitos com traceback. A mesma exceção NÃO SHALL ser registrada mais de uma vez.

#### Scenario: Falha ao atualizar o Tesouro Direto

- **WHEN** o `Atualizar` de uma sub-aba do Tesouro Direto falha
- **THEN** o log ativo SHALL registrar a sub-aba e a operação de atualização
- **THEN** a statusbar SHALL continuar exibindo a falha ao usuário

#### Scenario: Falha ao ler o cache do Tesouro Direto

- **WHEN** a leitura do cache de uma sub-aba do Tesouro Direto falha
- **THEN** o log ativo SHALL registrar a sub-aba e a operação de leitura de cache
- **THEN** a statusbar SHALL continuar exibindo a falha ao usuário

#### Scenario: Falha ao atualizar Câmbio e Reservas

- **WHEN** o `Atualizar` da sub-aba Dólar e Ouro ou Reservas Internacionais falha
- **THEN** o log ativo SHALL registrar a sub-aba e a operação de atualização
- **THEN** a statusbar SHALL continuar exibindo a falha ao usuário

#### Scenario: Falha parcial de fonte

- **WHEN** uma fonte do Tesouro, de mercado ou de reservas falha e as demais respondem
- **THEN** o log ativo SHALL registrar a fonte que falhou
- **THEN** os dados disponíveis SHALL continuar sendo exibidos
- **THEN** a statusbar SHALL continuar identificando a fonte com falha

#### Scenario: Falha de comunicação sem traceback

- **WHEN** a falha registrada é de comunicação
- **THEN** o log SHALL conter uma única linha com o tipo e a mensagem da exceção
- **THEN** o registro NÃO SHALL conter traceback

#### Scenario: Defeito inesperado com traceback

- **WHEN** a falha registrada não é de comunicação
- **THEN** o log SHALL conter o traceback completo da exceção

#### Scenario: Registro único por exceção

- **WHEN** a mesma exceção atravessa controller e GUI
- **THEN** ela SHALL ser registrada uma única vez no arquivo ativo
