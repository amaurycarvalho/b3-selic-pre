# Spec Delta

## ADDED Requirements

### Requirement: Ponteiro de espera ao atualizar

Enquanto o `Atualizar` da sub-aba Dólar e Ouro estiver em andamento, a janela SHALL exibir o ponteiro de espera `watch`. O ponteiro SHALL voltar ao padrão quando a atualização terminar, inclusive em caso de falha.

O ponteiro de espera NÃO SHALL substituir o estado da statusbar nem a indicação de fonte com falha.

#### Scenario: Ponteiro durante a atualização

- **WHEN** o usuário aciona `Atualizar` na sub-aba Dólar e Ouro
- **THEN** a janela SHALL exibir o ponteiro `watch`
- **THEN** o ponteiro SHALL permanecer durante a busca das fontes, o pré-cálculo e o desenho dos gráficos

#### Scenario: Ponteiro restaurado após sucesso

- **WHEN** a atualização termina com sucesso
- **THEN** a janela SHALL restaurar o ponteiro padrão

#### Scenario: Ponteiro restaurado após falha

- **WHEN** a atualização termina com falha total ou parcial
- **THEN** a janela SHALL restaurar o ponteiro padrão
- **THEN** a statusbar SHALL continuar identificando a fonte com falha
