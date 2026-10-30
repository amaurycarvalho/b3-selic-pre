# Spec Delta

## ADDED Requirements

### Requirement: Ponteiro de espera ao atualizar

Enquanto o `Atualizar` da sub-aba Reservas Internacionais estiver em andamento, a janela SHALL exibir o ponteiro de espera `watch`. O ponteiro SHALL voltar ao padrão quando a atualização terminar, inclusive em caso de falha.

O ponteiro de espera NÃO SHALL substituir o estado da statusbar, o snapshot anterior nem o aviso de defasagem.

#### Scenario: Ponteiro durante a atualização

- **WHEN** o usuário aciona `Atualizar` na sub-aba Reservas Internacionais
- **THEN** a janela SHALL exibir o ponteiro `watch`
- **THEN** o ponteiro SHALL permanecer durante a busca da série, a persistência do cache, o pré-cálculo e o desenho do gráfico

#### Scenario: Ponteiro restaurado após sucesso

- **WHEN** a atualização termina com sucesso
- **THEN** a janela SHALL restaurar o ponteiro padrão

#### Scenario: Ponteiro restaurado após falha

- **WHEN** a atualização termina com falha
- **THEN** a janela SHALL restaurar o ponteiro padrão
- **THEN** o snapshot anterior SHALL permanecer exibido e a falha SHALL ser identificada na statusbar
