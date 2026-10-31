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

### Requirement: Feedback de carregamento do gráfico

A sub-aba `Reservas Internacionais` SHALL exibir `Processando as informações. Aguarde…` atrás do painel e ocultar o painel ao exibir/re-exibir a sub-aba ou ao acionar `Atualizar`. O painel SHALL voltar somente após a carga e o desenho concluírem, inclusive em falha. A troca de janela SHALL manter o painel visível e usar apenas o ponteiro de espera.

#### Scenario: Seleção ou reexibição

- **WHEN** o usuário seleciona ou reexibe a sub-aba `Reservas Internacionais`
- **THEN** o painel SHALL ficar oculto antes da leitura do cache e do desenho
- **THEN** o texto fixo `Processando as informações. Aguarde…` SHALL ficar visível
- **THEN** o painel SHALL voltar após a carga e o desenho concluírem

#### Scenario: Atualizar

- **WHEN** o usuário aciona `Atualizar` na sub-aba `Reservas Internacionais`
- **THEN** o painel SHALL ficar oculto durante a busca, o processamento e o desenho
- **THEN** o painel SHALL voltar somente após o desenho e um repaint adicional

#### Scenario: Falha na carga ou no desenho

- **WHEN** a carga ou o desenho falha
- **THEN** o painel SHALL ser restaurado
- **THEN** a falha SHALL ser identificada na statusbar

#### Scenario: Troca de janela

- **WHEN** o usuário troca a janela de 12 meses ou 3 anos
- **THEN** o painel SHALL permanecer visível
- **THEN** apenas o ponteiro de espera SHALL indicar o redesenho
