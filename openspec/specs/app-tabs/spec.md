# app-tabs Specification

## Purpose

Organizar a janela principal em abas por classe de ativo, com carregamento lazy e um registro de abas que permita adicionar Câmbio no futuro sem reestruturar o shell.

## Requirements

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

### Requirement: Conteúdo atual preservado

A aba `SELIC Pré` SHALL manter o conteúdo atual da aplicação: busca por data, gráfico da curva, painel de análise, cópia de dados/gráfico, atalhos e barra de status.

A mudança de pai dos widgets NÃO SHALL alterar o comportamento observável.

#### Scenario: Busca continua funcionando

- **WHEN** o usuário informa uma data e clica em Buscar dentro de `SELIC Pré`
- **THEN** o gráfico e a análise SHALL ser atualizados como antes

#### Scenario: Estado preservado

- **WHEN** o usuário alterna para `Tesouro Direto` e volta para `SELIC Pré`
- **THEN** a data, o gráfico e o estado da análise SHALL permanecer

#### Scenario: Título da janela

- **WHEN** a janela principal é aberta
- **THEN** o título SHALL permanecer o atual
- **THEN** a change de Câmbio poderá alterá-lo depois

### Requirement: Renderização lazy por visibilidade

Cada aba de nível superior e cada sub-aba SHALL ser construída apenas na primeira vez que ficar visível.

A aba padrão SHALL ser construída no startup. Abas ocultas NÃO SHALL ser construídas no startup. A construção SHALL ser idempotente e NÃO SHALL acessar a rede.

#### Scenario: Startup constrói apenas a aba padrão

- **WHEN** a aplicação inicia
- **THEN** `SELIC Pré` SHALL ser construída
- **THEN** `Tesouro Direto` e suas sub-abas NÃO SHALL ser construídas

#### Scenario: Primeira exibição constrói

- **WHEN** o usuário seleciona `Tesouro Direto` pela primeira vez
- **THEN** o conteúdo SHALL ser construído

#### Scenario: Segunda exibição reutiliza

- **WHEN** o usuário retorna a uma aba já construída
- **THEN** ela NÃO SHALL ser construída novamente

#### Scenario: Construção sem rede

- **WHEN** uma aba é construída pela primeira vez
- **THEN** ela SHALL ler apenas o cache local
- **THEN** nenhuma requisição de rede SHALL ser iniciada

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

### Requirement: Legenda da curva SELIC Pré

As visualizações 2D da aba `SELIC Pré` SHALL exibir a legenda no canto superior
direito, inclusive na curva curta, na curva longa e nas evoluções.

#### Scenario: Legenda sempre visível

- **WHEN** uma curva ou evolução 2D é renderizada na aba `SELIC Pré`
- **THEN** a legenda SHALL estar visível no canto superior direito

#### Scenario: Curva curta rotulada

- **WHEN** a curva curta é exibida
- **THEN** a legenda SHALL conter o rótulo `Taxa`

### Requirement: Atalhos restritos à aba ativa

Os atalhos globais existentes SHALL atuar apenas quando `SELIC Pré` estiver ativa.

Atalhos de busca, cópia, evolução e análise NÃO SHALL disparar ações de `SELIC Pré` quando outra aba estiver ativa.

#### Scenario: Atalho na aba correta

- **WHEN** `SELIC Pré` está ativa e o usuário pressiona F5
- **THEN** a busca de taxas SHALL ser iniciada

#### Scenario: Atalho em outra aba

- **WHEN** `Tesouro Direto` está ativa e o usuário pressiona F5
- **THEN** nenhuma busca de taxas SELIC SHALL ser iniciada

### Requirement: Escudo de inicialização

O escudo de inicialização SHALL cobrir o notebook e bloquear a interação até o término da inicialização.

Após o escudo, a troca de abas SHALL funcionar normalmente.

#### Scenario: Escudo cobre o shell

- **WHEN** a aplicação está inicializando
- **THEN** o escudo SHALL cobrir o notebook
- **THEN** a troca de abas NÃO SHALL responder

#### Scenario: Escudo termina

- **WHEN** a inicialização termina
- **THEN** o escudo SHALL ser removido
- **THEN** a troca de abas SHALL funcionar

### Requirement: Ciclo de vida e fechamento

A troca de abas SHALL preservar o estado de cada controller.

Fechar a aplicação durante uma carga assíncrona NÃO SHALL lançar exceção. Controllers destruídos NÃO SHALL tentar atualizar widgets inexistentes.

#### Scenario: Fechar durante carga

- **WHEN** o usuário fecha a janela enquanto uma sub-aba carrega
- **THEN** nenhuma exceção SHALL ser lançada
- **THEN** a aplicação SHALL encerrar normalmente

#### Scenario: Controller destruído

- **WHEN** uma aba é destruída
- **THEN** callbacks pendentes SHALL ser ignorados
- **THEN** nenhum widget inválido SHALL ser acessado

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
