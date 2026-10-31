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

### Requirement: Feedback de carregamento do gráfico

A sub-aba `Dólar e Ouro` SHALL exibir `Processando as informações. Aguarde…` atrás do painel e ocultar o painel ao exibir/re-exibir a sub-aba ou ao acionar `Atualizar`. O painel SHALL voltar somente após a carga e o desenho concluírem, inclusive em falha. A troca de ativo, base 100 ou Fibonacci SHALL manter o painel visível e usar apenas o ponteiro de espera.

#### Scenario: Seleção ou reexibição

- **WHEN** o usuário seleciona ou reexibe a sub-aba `Dólar e Ouro`
- **THEN** o painel SHALL ficar oculto antes da leitura do cache e do desenho
- **THEN** o texto fixo `Processando as informações. Aguarde…` SHALL ficar visível
- **THEN** o painel SHALL voltar após a carga e o desenho concluírem

#### Scenario: Atualizar

- **WHEN** o usuário aciona `Atualizar` na sub-aba `Dólar e Ouro`
- **THEN** o painel SHALL ficar oculto durante a busca, o processamento e o desenho
- **THEN** o painel SHALL voltar somente após o desenho e um repaint adicional

#### Scenario: Falha na carga ou no desenho

- **WHEN** a carga ou o desenho falha
- **THEN** o painel SHALL ser restaurado
- **THEN** a falha SHALL ser identificada na statusbar

#### Scenario: Troca de opção

- **WHEN** o usuário troca o ativo, base 100 ou Fibonacci
- **THEN** o painel SHALL permanecer visível
- **THEN** apenas o ponteiro de espera SHALL indicar o redesenho
