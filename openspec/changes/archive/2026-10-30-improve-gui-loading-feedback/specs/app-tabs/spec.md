# Spec Delta

## MODIFIED Requirements

### Requirement: Abas de nível superior

A janela principal SHALL exibir um `ttk.Notebook` de nível superior com as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Reserva`, `Feriados` e `Sobre`, nesta ordem.

`SELIC Pré` SHALL ser a aba padrão. A antiga janela separada de Tesouro Direto NÃO SHALL existir.

#### Scenario: Abas são exibidas

- **WHEN** a janela principal é aberta
- **THEN** as abas `SELIC Pré`, `Tesouro Direto`, `Câmbio e Reserva`, `Feriados` e `Sobre` SHALL estar visíveis
- **THEN** `SELIC Pré` SHALL estar selecionada

#### Scenario: Sem janela separada

- **WHEN** o usuário acessa o Tesouro Direto
- **THEN** o conteúdo SHALL aparecer na aba da janela principal
- **THEN** nenhum `Toplevel` de Tesouro Direto SHALL ser criado
