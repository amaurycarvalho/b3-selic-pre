## ADDED Requirements

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
