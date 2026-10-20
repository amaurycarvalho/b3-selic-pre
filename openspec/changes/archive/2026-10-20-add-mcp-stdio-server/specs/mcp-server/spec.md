## Purpose

Expor os dados da aplicação a clientes MCP por um servidor `stdio` somente leitura, com protocolo moderno, preparação opcional na inicialização e ciclo de vida controlado pelo cliente.

## ADDED Requirements

### Requirement: Subcomando MCP e transporte stdio

O sistema SHALL oferecer o subcomando `b3-selic-pre mcp`, que inicia um servidor MCP via `stdio`. O cliente lança o processo e troca mensagens JSON-RPC delimitadas por newline em `stdin` e `stdout`. O servidor SHALL encerrar ao receber EOF em `stdin`.

O servidor NÃO SHALL escrever em `stdout` nada que não seja uma mensagem JSON-RPC válida. Logs e diagnósticos SHALL ser escritos em `stderr`.

#### Scenario: Servidor inicia e responde

- **WHEN** o cliente executa `b3-selic-pre mcp` e envia uma requisição JSON-RPC em `stdin`
- **THEN** o servidor SHALL responder em `stdout` com uma única linha JSON-RPC
- **THEN** nenhuma outra saída SHALL ser escrita em `stdout`

#### Scenario: EOF encerra o servidor

- **WHEN** o cliente fecha `stdin`
- **THEN** o servidor SHALL encerrar prontamente com código de saída `0`

#### Scenario: Diagnóstico vai para stderr

- **WHEN** o servidor precisa registrar progresso, aviso ou erro interno
- **THEN** a mensagem SHALL ser escrita em `stderr`
- **THEN** `stdout` SHALL permanecer exclusivo para mensagens JSON-RPC

### Requirement: Preparação opcional na inicialização

O subcomando `mcp` SHALL aceitar os parâmetros opcionais `--atualizar` e `--data <AAAA-MM-DD>`.

Quando `--atualizar` for informado, o sistema SHALL executar, antes de iniciar o servidor, a mesma etapa de carga do subcomando `atualizar`, usando a data de referência padrão (hoje). Quando `--data` for informado, o sistema SHALL executar a mesma etapa de carga com a data informada. Quando ambos forem informados, o sistema SHALL executar uma única carga usando a data informada.

A preparação SHALL reutilizar os mesmos serviços de carga do subcomando `atualizar`, SHALL ocorrer sob o lock de ação compartilhado com `atualizar`, SHALL registrar progresso em `stderr`, NÃO SHALL escrever em `stdout` e SHALL liberar o lock antes de o servidor começar a atender. Uma falha na preparação SHALL abortar a inicialização com código de saída diferente de zero, sem iniciar o servidor.

Sem `--atualizar` e sem `--data`, o servidor SHALL iniciar diretamente e atender usando apenas o cache local padrão.

#### Scenario: Atualização padrão antes do servidor

- **WHEN** o usuário executa `b3-selic-pre mcp --atualizar`
- **THEN** o sistema SHALL carregar os dados da data de referência padrão antes de atender
- **THEN** o lock de ação SHALL ser liberado antes do início do atendimento

#### Scenario: Data explícita antes do servidor

- **WHEN** o usuário executa `b3-selic-pre mcp --data 2026-06-10`
- **THEN** o sistema SHALL carregar os dados de 2026-06-10 antes de atender

#### Scenario: Ambos os parâmetros fazem uma única carga

- **WHEN** o usuário executa `b3-selic-pre mcp --atualizar --data 2026-06-10`
- **THEN** o sistema SHALL executar uma única carga usando 2026-06-10
- **THEN** o sistema NÃO SHALL executar uma segunda carga para a data padrão

#### Scenario: Falha na preparação não inicia o servidor

- **WHEN** a carga de preparação falha
- **THEN** o sistema SHALL registrar o erro em `stderr`
- **THEN** o sistema SHALL encerrar com código diferente de zero
- **THEN** o servidor NÃO SHALL iniciar o atendimento

#### Scenario: Sem preparação lê o cache

- **WHEN** o usuário executa `b3-selic-pre mcp` sem `--atualizar` e sem `--data`
- **THEN** o sistema NÃO SHALL acessar a B3 ou a CVM
- **THEN** o servidor SHALL iniciar lendo o cache local padrão

#### Scenario: Preparação não é uma tool

- **WHEN** um cliente lista as tools disponíveis
- **THEN** a preparação NÃO SHALL aparecer como tool
- **THEN** nenhuma chamada JSON-RPC SHALL executar atualização de dados

### Requirement: Protocolo moderno 2026-07-28

O servidor SHALL implementar a revisão MCP `2026-07-28`, na qual cada requisição declara sua versão de protocolo e suas capacidades em `_meta`, sem handshake `initialize`.

O servidor SHALL validar os campos obrigatórios `io.modelcontextprotocol/protocolVersion` e `io.modelcontextprotocol/clientCapabilities` em cada requisição. Uma requisição sem esses campos SHALL ser rejeitada com erro JSON-RPC `-32602`.

O servidor SHALL implementar a RPC obrigatória `server/discover`, devolvendo as versões de protocolo suportadas, as capacidades e a identidade do servidor.

Quando a versão solicitada não for suportada, o servidor SHALL responder com `UnsupportedProtocolVersionError` (`-32022`), listando as versões suportadas e a versão solicitada. Ao receber um `initialize` legado, o servidor SHALL responder com erro que nomeie as versões suportadas.

Todo resultado SHALL incluir `resultType` com o valor `complete`.

#### Scenario: Descoberta retorna versão e identidade

- **WHEN** o cliente envia `server/discover` com `_meta` válido
- **THEN** a resposta SHALL conter `supportedVersions`, `capabilities` e `io.modelcontextprotocol/serverInfo`
- **THEN** `supportedVersions` SHALL conter `2026-07-28`

#### Scenario: Versão não suportada

- **WHEN** o cliente envia uma requisição com versão de protocolo não suportada
- **THEN** o servidor SHALL responder com código `-32022`
- **THEN** os dados do erro SHALL listar as versões suportadas e a versão solicitada

#### Scenario: Metadados obrigatórios ausentes

- **WHEN** uma requisição não contém `_meta` ou não contém a versão/capacidades obrigatórias
- **THEN** o servidor SHALL responder com código `-32602`

#### Scenario: Initialize legado é rejeitado

- **WHEN** o cliente envia `initialize`
- **THEN** o servidor SHALL responder com erro
- **THEN** a mensagem SHALL nomear as versões de protocolo suportadas
- **THEN** o servidor NÃO SHALL iniciar um handshake legado

#### Scenario: Resultado completo

- **WHEN** uma requisição é atendida com sucesso
- **THEN** o resultado SHALL conter `resultType` igual a `complete`

### Requirement: Listagem e chamada de tools

O servidor SHALL responder a `tools/list` com o catálogo de tools disponíveis, em ordem determinística. Quando houver continuação, a resposta SHALL incluir `nextCursor`.

O servidor SHALL responder a `tools/call` executando a tool solicitada e devolvendo o resultado em JSON estruturado. Uma tool desconhecida SHALL ser rejeitada com `-32602`.

#### Scenario: Listagem de tools

- **WHEN** o cliente envia `tools/list`
- **THEN** o servidor SHALL devolver as tools disponíveis com nome, descrição e schema de entrada
- **THEN** a ordem SHALL ser a mesma em chamadas sucessivas enquanto o catálogo não mudar

#### Scenario: Chamada de tool conhecida

- **WHEN** o cliente envia `tools/call` com uma tool e argumentos válidos
- **THEN** o servidor SHALL devolver o resultado estruturado da tool
- **THEN** o resultado SHALL conter `resultType` igual a `complete`

#### Scenario: Tool desconhecida

- **WHEN** o cliente envia `tools/call` com um nome de tool inexistente
- **THEN** o servidor SHALL responder com código `-32602`

### Requirement: Falhas recuperáveis e falhas internas

Erros de domínio recuperáveis SHALL ser devolvidos como conteúdo estruturado com os campos `motivo`, `detalhe` e `dica`, sem `isError`. Falhas internas não tratadas SHALL ser devolvidas com `isError` verdadeiro, sem derrubar o servidor.

Após uma falha interna, o servidor SHALL permanecer apto a atender novas chamadas.

#### Scenario: Erro de domínio é resultado estruturado

- **WHEN** uma tool não encontra dados para a data solicitada
- **THEN** o resultado SHALL conter `motivo`, `detalhe` e `dica`
- **THEN** o resultado NÃO SHALL conter `isError`

#### Scenario: Falha interna não derruba o servidor

- **WHEN** uma tool lança uma exceção não tratada
- **THEN** o resultado SHALL conter `isError` verdadeiro
- **THEN** uma chamada seguinte SHALL ser atendida normalmente

### Requirement: Cancelamento de requisições

O servidor SHALL suportar a notificação `notifications/cancelled`, referenciando o identificador de uma requisição em andamento. Ao receber o cancelamento, o servidor SHOULD interromper o trabalho e NÃO SHALL enviar resposta para a requisição cancelada. Cancelamentos de requisições desconhecidas ou já concluídas SHALL ser ignorados.

#### Scenario: Requisição cancelada não recebe resposta

- **WHEN** o cliente envia `notifications/cancelled` para uma requisição em andamento
- **THEN** o servidor SHALL interromper o processamento quando possível
- **THEN** o servidor NÃO SHALL enviar resposta para aquela requisição

#### Scenario: Cancelamento desconhecido é ignorado

- **WHEN** o cliente cancela um identificador que não está em andamento
- **THEN** o servidor SHALL ignorar a notificação
- **THEN** o servidor SHALL continuar atendendo outras requisições

### Requirement: Somente leitura durante o atendimento

Durante o atendimento, o servidor MCP SHALL apenas ler o cache local e as configurações locais da aplicação. O servidor NÃO SHALL consultar a B3 ou a CVM, baixar dados, extrair dados ou escrever estado.

A preparação opcional executada antes do atendimento NÃO SHALL ser acessível pelo protocolo. As tools NÃO SHALL gravar arquivos nem alterar o cache.

#### Scenario: Nenhum acesso à rede durante o atendimento

- **WHEN** uma tool é chamada
- **THEN** o servidor NÃO SHALL fazer requisições à B3 ou à CVM
- **THEN** o servidor SHALL usar apenas dados locais já presentes no cache

#### Scenario: Nenhuma escrita de estado

- **WHEN** uma tool é chamada
- **THEN** o servidor NÃO SHALL criar, alterar ou remover arquivos de cache, settings ou log

#### Scenario: Cache vazio não dispara download

- **WHEN** uma tool é chamada e não há dados em cache
- **THEN** o servidor SHALL devolver erro de domínio recuperável
- **THEN** o servidor NÃO SHALL baixar dados
