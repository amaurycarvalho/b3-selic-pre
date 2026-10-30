# Spec Delta

## ADDED Requirements

### Requirement: Sub-aba Reservas Internacionais

A aba `Câmbio e Ouro` SHALL registrar a sub-aba `Reservas Internacionais` em seu sub-notebook lazy, após `Dólar e Ouro`.

A sub-aba SHALL ser construída apenas quando visível e NÃO SHALL acessar a rede na construção.

#### Scenario: Sub-aba registrada na ordem

- **WHEN** a aba `Câmbio e Ouro` é construída
- **THEN** o sub-notebook SHALL conter `Dólar e Ouro` e `Reservas Internacionais`, nesta ordem

#### Scenario: Sub-aba lazy

- **WHEN** o usuário seleciona `Reservas Internacionais` pela primeira vez
- **THEN** a sub-aba SHALL ser construída
- **THEN** seleções seguintes NÃO SHALL reconstruí-la

#### Scenario: Sub-aba oculta no startup

- **WHEN** a aplicação inicia
- **THEN** a sub-aba `Reservas Internacionais` NÃO SHALL ser construída

#### Scenario: Construção sem rede

- **WHEN** a sub-aba é construída pela primeira vez
- **THEN** ela SHALL ler apenas o cache local
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Estado preservado

- **WHEN** o usuário alterna para outra sub-aba e retorna
- **THEN** o estado anterior da sub-aba SHALL ser preservado
