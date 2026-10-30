# Spec Delta

## MODIFIED Requirements

### Requirement: Abas de nível superior

A janela principal SHALL exibir um `ttk.Notebook` de nível superior com as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Ouro`, `Feriados` e `Sobre`, nesta ordem.

`SELIC Pré` SHALL ser a aba padrão. A antiga janela separada de Tesouro Direto NÃO SHALL existir.

#### Scenario: Abas são exibidas

- **WHEN** a janela principal é aberta
- **THEN** as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Ouro`, `Feriados` e `Sobre` SHALL estar visíveis
- **THEN** `SELIC Pré` SHALL estar selecionada

#### Scenario: Sem janela separada

- **WHEN** o usuário acessa o Tesouro Direto
- **THEN** o conteúdo SHALL aparecer na aba da janela principal
- **THEN** nenhum `Toplevel` de Tesouro Direto SHALL ser criado

### Requirement: Registro de abas

O shell SHALL manter um registro determinístico de abas, com identificador único e rótulo.

As abas `Câmbio e Ouro` e `Feriados` SHALL ser registradas sem reestruturar o shell. Uma aba NÃO SHALL aparecer antes de ser registrada.

O sub-notebook de `Câmbio e Ouro` SHALL manter um registro determinístico de sub-abas, com identificador único e rótulo, rejeitando identificadores duplicados.

#### Scenario: Aba registrada aparece

- **WHEN** uma aba é registrada no shell
- **THEN** ela SHALL aparecer na ordem definida

#### Scenario: Identificador duplicado

- **WHEN** duas abas usam o mesmo identificador
- **THEN** o registro SHALL rejeitar a duplicata

#### Scenario: Sub-aba registrada aparece

- **WHEN** uma sub-aba é registrada no sub-notebook
- **THEN** ela SHALL aparecer na ordem definida

#### Scenario: Sub-aba duplicada

- **WHEN** duas sub-abas usam o mesmo identificador
- **THEN** o registro SHALL rejeitar a duplicata

#### Scenario: Câmbio ainda ausente

- **WHEN** a change de Câmbio não foi aplicada
- **THEN** a aba `Câmbio` NÃO SHALL ser exibida

#### Scenario: Câmbio registrada

- **WHEN** a change de Câmbio e Ouro é aplicada
- **THEN** a aba `Câmbio e Ouro` SHALL estar registrada entre `Tesouro Direto` e `Feriados`

#### Scenario: Feriados registrada

- **WHEN** a change de Calendário de Feriados é aplicada
- **THEN** a aba `Feriados` SHALL estar registrada entre `Câmbio e Ouro` e `Sobre`

### Requirement: Renderização lazy por visibilidade

Cada aba de nível superior e cada sub-aba SHALL ser construída apenas na primeira vez que ficar visível.

A aba padrão SHALL ser construída no startup. Abas ocultas NÃO SHALL ser construídas no startup. A construção SHALL ser idempotente e NÃO SHALL acessar a rede.

#### Scenario: Startup constrói apenas a aba padrão

- **WHEN** a aplicação inicia
- **THEN** `SELIC Pré` SHALL ser construída
- **THEN** `Tesouro Direto`, `Câmbio e Ouro` e `Feriados` NÃO SHALL ser construídas

#### Scenario: Primeira exibição constrói

- **WHEN** o usuário seleciona `Tesouro Direto` pela primeira vez
- **THEN** o conteúdo SHALL ser construído

#### Scenario: Primeira exibição de Feriados constrói

- **WHEN** o usuário seleciona `Feriados` pela primeira vez
- **THEN** a aba SHALL ser construída lendo apenas o cache do calendário
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Segunda exibição reutiliza

- **WHEN** o usuário retorna a uma aba já construída
- **THEN** ela NÃO SHALL ser construída novamente

#### Scenario: Construção sem rede

- **WHEN** uma aba é construída pela primeira vez
- **THEN** ela SHALL ler apenas o cache local
- **THEN** nenhuma requisição de rede SHALL ser iniciada

### Requirement: Aba Sobre

A janela principal SHALL exibir uma aba `Sobre` à direita de `Feriados`.

A aba SHALL replicar o conteúdo e as funcionalidades do diálogo `Sobre` da aba
`SELIC Pré`: identidade, versão, data de lançamento, licença, descrição, link do
repositório, diretório de logs e aviso de nova versão. O botão `Sobre` da aba
`SELIC Pré` SHALL continuar disponível e abrindo o diálogo modal.

A aba SHALL exibir o conteúdo em um frame e um textbox somente leitura abaixo
dos botões com seções em negrito e `:` ao final. O texto SHALL resumir a
aplicação, a sintaxe dos comandos e parâmetros da CLI e o servidor MCP, incluindo
o que é MCP, as ferramentas disponibilizadas e a sintaxe para iniciar/atualizar
o servidor.

#### Scenario: Aba Sobre visível

- **WHEN** a janela principal é aberta
- **THEN** as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Ouro`, `Feriados` e `Sobre` SHALL estar disponíveis
- **THEN** `Sobre` SHALL estar à direita de `Feriados`

#### Scenario: Funcionalidades preservadas

- **WHEN** o usuário acessa a aba `Sobre`
- **THEN** o link do repositório, o diretório de logs e o aviso de nova versão SHALL funcionar como no diálogo
- **THEN** o botão `Sobre` da aba `SELIC Pré` SHALL continuar abrindo o diálogo

#### Scenario: Texto orientativo da aplicação

- **WHEN** o usuário acessa a aba `Sobre`
- **THEN** SHALL existir um textbox somente leitura abaixo dos botões
- **THEN** as seções SHALL estar em negrito e terminar com `:`
- **THEN** ele SHALL resumir a aplicação, a sintaxe/parâmetros da CLI e o servidor MCP
- **THEN** ele SHALL explicar o que é MCP, listar as tools e mostrar como iniciar/atualizar
