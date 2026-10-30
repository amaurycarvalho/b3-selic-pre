# Spec Delta

## Purpose

Organizar a janela principal em abas por classe de ativo, com carregamento lazy e um registro de abas que permita adicionar Câmbio no futuro sem reestruturar o shell.

## ADDED Requirements

### Requirement: Abas de nível superior

A janela principal SHALL exibir um `ttk.Notebook` de nível superior com as abas `SELIC Pré` e `Tesouro Direto`, nesta ordem.

`SELIC Pré` SHALL ser a aba padrão. A antiga janela separada de Tesouro Direto NÃO SHALL existir.

#### Scenario: Abas são exibidas

- **WHEN** a janela principal é aberta
- **THEN** as abas `SELIC Pré` e `Tesouro Direto` SHALL estar visíveis
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

A change de Câmbio SHALL poder registrar sua aba sem alterar o shell. Uma aba NÃO SHALL aparecer antes de ser registrada.

#### Scenario: Aba registrada aparece

- **WHEN** uma aba é registrada no shell
- **THEN** ela SHALL aparecer na ordem definida

#### Scenario: Identificador duplicado

- **WHEN** duas abas usam o mesmo identificador
- **THEN** o registro SHALL rejeitar a duplicata

#### Scenario: Câmbio ainda ausente

- **WHEN** a change de Câmbio não foi aplicada
- **THEN** a aba `Câmbio` NÃO SHALL ser exibida

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
