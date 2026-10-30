# Spec Delta

## MODIFIED Requirements

### Requirement: Abas de nível superior

A janela principal SHALL exibir um `ttk.Notebook` de nível superior com as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Reservas` e `Sobre`, nesta ordem.

`SELIC Pré` SHALL ser a aba padrão. A antiga janela separada de Tesouro Direto NÃO SHALL existir.

#### Scenario: Abas são exibidas

- **WHEN** a janela principal é aberta
- **THEN** as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Reservas` e `Sobre` SHALL estar visíveis
- **THEN** `SELIC Pré` SHALL estar selecionada

#### Scenario: Sem janela separada

- **WHEN** o usuário acessa o Tesouro Direto
- **THEN** o conteúdo SHALL aparecer na aba da janela principal
- **THEN** nenhum `Toplevel` de Tesouro Direto SHALL ser criado

### Requirement: Registro de abas

O shell SHALL manter um registro determinístico de abas, com identificador único e rótulo.

A aba `Câmbio e Reservas` SHALL ser registrada sem reestruturar o shell. Uma aba NÃO SHALL aparecer antes de ser registrada.

O sub-notebook de `Câmbio e Reservas` SHALL manter um registro determinístico de sub-abas, com identificador único e rótulo, rejeitando identificadores duplicados.

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

- **WHEN** a change de Câmbio e Reservas é aplicada
- **THEN** a aba `Câmbio e Reservas` SHALL estar registrada entre `Tesouro Direto` e `Sobre`

### Requirement: Aba Sobre

A janela principal SHALL exibir uma aba `Sobre` à direita de `Câmbio e Reservas`.

A aba SHALL replicar o conteúdo e as funcionalidades do diálogo `Sobre` da aba
`SELIC Pré`: identidade, versão, data de lançamento, licença, descrição, link do
repositório, diretório de logs e aviso de nova versão. O botão `Sobre` da aba
`SELIC Pré` SHALL continuar disponível e abrindo o diálogo modal.

A aba SHALL exibir o conteúdo em um frame e um textbox somente leitura abaixo
dos botões com seções em negrito e `:` ao final. O texto SHALL resumir a
aplicação, a sintaxe dos comandos e parâmetros da CLI e o servidor MCP, incluindo
o que é MCP, as tools disponibilizadas e a sintaxe para iniciar/atualizar o
servidor.

#### Scenario: Aba Sobre visível

- **WHEN** a janela principal é aberta
- **THEN** as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Reservas` e `Sobre` SHALL estar disponíveis
- **THEN** `Sobre` SHALL estar à direita de `Câmbio e Reservas`

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

## ADDED Requirements

### Requirement: Aba Câmbio e Reservas

A aba `Câmbio e Reservas` SHALL ser construída apenas na primeira vez que ficar visível e SHALL ler apenas o cache local nessa construção.

A aba SHALL organizar o conteúdo em sub-abas lazy. A sub-aba `Dólar e Ouro` SHALL ser registrada nesta entrega. A futura sub-aba `Reservas Internacionais` SHALL entrar no mesmo sub-notebook sem reestruturar o shell.

#### Scenario: Primeira exibição

- **WHEN** o usuário seleciona `Câmbio e Reservas` pela primeira vez
- **THEN** o conteúdo da sub-aba visível SHALL ser construído
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Aba oculta no startup

- **WHEN** a aplicação inicia
- **THEN** a aba `Câmbio e Reservas` NÃO SHALL ser construída

### Requirement: Sub-aba Dólar e Ouro

A sub-aba `Dólar e Ouro` SHALL ser construída apenas quando visível e SHALL ter `Atualizar` próprio, que busca apenas as fontes dessa sub-aba e dispara o pré-cálculo correspondente.

O estado da sub-aba SHALL ser preservado ao alternar entre sub-abas, outras abas e ao retornar. A sub-aba concentra os dois painéis de preço e o `Atualizar` do mercado.

#### Scenario: Sub-aba oculta no startup

- **WHEN** a aplicação inicia
- **THEN** a sub-aba `Dólar e Ouro` NÃO SHALL ser construída

#### Scenario: Segunda exibição

- **WHEN** o usuário retorna à sub-aba já construída
- **THEN** ela NÃO SHALL ser construída novamente
- **THEN** o estado anterior SHALL ser preservado

#### Scenario: Atualização própria

- **WHEN** o usuário clica em `Atualizar` na sub-aba `Dólar e Ouro`
- **THEN** as fontes de mercado daquela sub-aba SHALL ser consultadas
- **THEN** o pré-cálculo correspondente SHALL ser disparado após a atualização

### Requirement: Controles da sub-aba Dólar e Ouro

A sub-aba SHALL seguir o padrão de usabilidade do Tesouro Direto: tooltips nos controles, toolbar do gráfico, statusbar, texto orientativo e botão `Atualizar` com ícone ao lado direito do combobox. Falhas de atualização SHALL ser visíveis na statusbar.

#### Scenario: Controles consistentes com o Tesouro Direto

- **WHEN** a sub-aba é exibida
- **THEN** os controles SHALL ter tooltips
- **THEN** o gráfico SHALL ter toolbar
- **THEN** a sub-aba SHALL ter statusbar e texto orientativo
- **THEN** o botão `Atualizar` SHALL exibir ícone e ficar à direita do combobox

#### Scenario: Falha de atualização visível

- **WHEN** o `Atualizar` falha
- **THEN** a statusbar SHALL exibir a falha
- **THEN** o último artefato válido SHALL permanecer visível
