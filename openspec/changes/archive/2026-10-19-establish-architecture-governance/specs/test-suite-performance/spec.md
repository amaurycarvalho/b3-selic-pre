## ADDED Requirements

### Requirement: Orçamento de testes de UI não headless

A suíte SHALL manter um orçamento máximo de testes que exigem display/Tk. Todo teste que instancia Tkinter ou a aplicação GUI SHALL ser marcado com `@pytest.mark.ui` e contabilizado pelo orçamento. O orçamento SHALL NOT aumentar sem aprovação explícita e SHALL ser reduzido sempre que testes forem migrados para headless.

#### Scenario: Novo teste de UI sem ampliar orçamento

- **WHEN** um novo teste depende de Tkinter ou da aplicação GUI e o orçamento já está no limite
- **THEN** o teste de guarda do orçamento falha
- **THEN** a change deve preferir um teste headless ou obter aprovação explícita para ampliar o orçamento

#### Scenario: Teste de UI sem marcação

- **WHEN** um arquivo de teste importa Tkinter ou a camada GUI e contém teste não marcado com `@pytest.mark.ui`
- **THEN** o teste de guarda de marcação falha

#### Scenario: Migração reduz o orçamento

- **WHEN** um teste de UI é migrado para headless
- **THEN** o orçamento é reduzido para refletir a nova contagem
