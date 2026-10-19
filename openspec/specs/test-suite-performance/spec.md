## Purpose

Reduce the execution time of the GUI test suite by reusing application instances instead of rebuilding the Tk application on every test case.

## Requirements

### Requirement: Suíte de testes GUI reutiliza uma única instância de aplicação

A suíte de testes de GUI (`tests/test_b3_selic_pre_gui.py`) SHALL construir uma única instância de `tk.Tk` e `SelicPreApp` por classe de teste e restaurar o estado mutável entre testes, em vez de reconstruir a aplicação a cada teste.

#### Scenario: aplicação construída uma vez por classe
- **WHEN** a classe de testes de GUI executa seus casos
- **THEN** `tk.Tk` e `SelicPreApp` são construídos exatamente uma vez para a classe
- **THEN** o estado mutável é resetado no início de cada caso de teste

#### Scenario: estado resetado entre testes
- **WHEN** um caso de teste da GUI começa
- **THEN** `records`, `historical_data`, variáveis de visualização (`view`, `evolution`, `3d`, `sidebar`) e estados de widgets retornam aos valores iniciais
- **THEN** a barra de status e a data retornam aos valores padrão

### Requirement: Testes de atalho desktop reutilizam instâncias compartilhadas

Os testes de atalho desktop SHALL reutilizar instâncias de aplicação pré-construídas (uma com atalho existente e uma sem), em vez de construir uma nova aplicação por teste.

#### Scenario: apps de atalho compartilhados
- **WHEN** os testes de atalho executam
- **THEN** no máximo duas aplicações adicionais são construídas, independentemente do número de casos de teste de atalho

### Requirement: Tempo de execução dos testes reduzido

Após a reutilização de instâncias, o tempo de execução de `make test` SHALL ser significativamente menor que o baseline (~51s), com os 10 testes mais lentos caindo abaixo de 1s cada.

#### Scenario: suíte mais rápida
- **WHEN** `make test` executa a suíte completa
- **THEN** o tempo total é reduzido para uma fração do baseline
- **THEN** nenhum caso de teste individual excede 1s nos testes de GUI

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

### Requirement: Testes de comportamento migrados de UI para headless

Testes que validam regras de negócio, exportação, estatísticas, dispatch de gráfico ou estado derivado de controles SHALL ser migrados para testes headless. Apenas testes de montagem, aparência e wiring de widgets SHALL permanecer como testes de UI. Após a migração, o orçamento de testes de UI SHALL ser reduzido para a nova contagem.

#### Scenario: Comportamento testado sem display

- **WHEN** um teste valida validação de data, seleção de exportação, estatísticas, modo de gráfico ou estado de habilitação
- **THEN** ele executa sem Tkinter e sem display
- **THEN** ele importa o serviço/view-model headless correspondente

#### Scenario: UI mantém apenas testes de apresentação

- **WHEN** um teste de UI é mantido
- **THEN** ele valida montagem, existência/configuração de widgets ou wiring com o view-model
- **THEN** regras de negócio já são cobertas por testes headless

#### Scenario: Orçamento reduzido após migração

- **WHEN** os testes migrados deixam de depender de Tkinter
- **THEN** `UI_TEST_BUDGET` é reduzido para a contagem real de testes de UI remanescentes
- **THEN** o teste de guarda do orçamento continua passando
