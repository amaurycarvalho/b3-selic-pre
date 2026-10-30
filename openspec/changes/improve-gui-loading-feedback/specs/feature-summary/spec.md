# Spec Delta

## Purpose

Publicar um resumo único e conciso das funcionalidades da aplicação, usado tanto no início do README quanto na aba Sobre, para que o usuário descubra rapidamente o que o sistema oferece.

## ADDED Requirements

### Requirement: Resumo de funcionalidades no README

O `README.md` SHALL conter uma seção `Funcionalidades` na parte inicial do documento, antes das seções de instalação e de uso.

A seção SHALL apresentar, em poucos itens, as principais capacidades da aplicação: interface gráfica por abas, consulta da curva SELIC Pré, Tesouro Direto, Câmbio e Ouro, Reservas Internacionais, Feriados, linha de comando, servidor MCP somente leitura, cache local e exportação.

#### Scenario: Resumo antes das seções de uso

- **WHEN** o usuário abre o `README.md`
- **THEN** a seção `Funcionalidades` SHALL aparecer antes de `Como Instalar` e de `Como Usar`
- **THEN** ela SHALL resumir as capacidades principais em uma lista curta

#### Scenario: Resumo cobre as áreas funcionais

- **WHEN** o usuário lê a seção `Funcionalidades`
- **THEN** ela SHALL mencionar a interface gráfica por abas
- **THEN** ela SHALL mencionar a consulta da curva SELIC Pré
- **THEN** ela SHALL mencionar o Tesouro Direto, o Câmbio e Ouro e as Reservas Internacionais
- **THEN** ela SHALL mencionar a linha de comando, o servidor MCP e o uso de cache local

### Requirement: Resumo replicado na aba Sobre

A aba Sobre SHALL exibir uma seção `Funcionalidades` com o mesmo texto do resumo publicado no `README.md`, dentro do painel de texto somente leitura.

O texto SHALL ser mantido em uma única fonte de dados compartilhada pela aba Sobre e verificado contra o `README.md` por teste automatizado.

#### Scenario: Seção na aba Sobre

- **WHEN** o usuário acessa a aba Sobre
- **THEN** o painel de texto somente leitura SHALL conter uma seção `Funcionalidades`
- **THEN** a seção SHALL usar o mesmo título e o mesmo conteúdo do `README.md`

#### Scenario: Conteúdo idêntico

- **WHEN** o resumo do `README.md` e o resumo da aba Sobre são comparados com espaços normalizados
- **THEN** os dois textos SHALL ser idênticos

#### Scenario: Alteração do resumo

- **WHEN** uma funcionalidade é adicionada, removida ou reescrita no resumo
- **THEN** a mudança SHALL ser refletida no `README.md` e na aba Sobre
- **THEN** o teste de paridade SHALL falhar enquanto os dois textos divergirem
