## ADDED Requirements

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
