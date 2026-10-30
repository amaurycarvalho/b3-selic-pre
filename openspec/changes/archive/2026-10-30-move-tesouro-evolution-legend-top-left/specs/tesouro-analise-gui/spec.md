## ADDED Requirements

### Requirement: Posição da legenda dos gráficos temporais

Os gráficos temporais das sub-abas de `Tesouro Direto` (evolução de `Estoque`/`Apetite do mercado` e gap da `Visão geral`) SHALL exibir a legenda no canto superior esquerdo, no início da série. A posição da legenda dos gráficos de percentual atual NÃO SHALL ser alterada.

#### Scenario: Legenda no início da série

- **WHEN** um gráfico temporal é renderizado com dados
- **THEN** a legenda SHALL estar no canto superior esquerdo
- **THEN** a legenda SHALL permanecer visível

#### Scenario: Gráfico temporal sem dados

- **WHEN** um gráfico temporal é renderizado sem dados
- **THEN** o estado vazio SHALL ser exibido sem erro
- **THEN** nenhuma legenda SHALL ser exigida

#### Scenario: Gráficos atuais inalterados

- **WHEN** um gráfico de percentual atual é renderizado
- **THEN** a posição da legenda SHALL permanecer a anterior
