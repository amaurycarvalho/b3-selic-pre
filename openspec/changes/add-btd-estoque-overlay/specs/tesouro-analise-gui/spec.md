# Spec Delta

## ADDED Requirements

### Requirement: Sobreposição do estoque BTD na sub-aba Estoque

A sub-aba `Estoque` SHALL usar a sobreposição do BTD quando ela acrescentar meses ausentes no CKAN, tanto na leitura de cache quanto na atualização, sem alterar as demais sub-abas. A data-base e o status SHALL refletir o mês mais recente entre CKAN e BTD.

#### Scenario: Primeira exibição com sobreposição em cache

- **WHEN** a sub-aba `Estoque` fica visível e existe cache BTD além do cache CKAN
- **THEN** a sub-aba SHALL ler ambos os caches sem acessar a rede
- **THEN** os gráficos SHALL incluir os meses do BTD ausentes no CKAN
- **THEN** o status SHALL indicar a data-base mais recente

#### Scenario: Atualização com BTD mais recente

- **WHEN** o usuário clica em `Atualizar` na sub-aba `Estoque`
- **THEN** o sistema SHALL atualizar o CKAN e a sobreposição BTD
- **THEN** os gráficos SHALL ser atualizados com os meses mais recentes disponíveis
- **THEN** a statusbar SHALL indicar quando a sobreposição BTD contribuiu com um mês mais recente

#### Scenario: BTD sem novidade

- **WHEN** a atualização do BTD não acrescenta meses ausentes no CKAN
- **THEN** os gráficos e a data-base SHALL permanecer os do CKAN
- **THEN** o status NÃO SHALL sugerir que o BTD forneceu dados novos

#### Scenario: Falha do BTD na atualização

- **WHEN** a atualização do BTD falha
- **THEN** a atualização do CKAN SHALL permanecer bem-sucedida
- **THEN** a statusbar SHALL informar a falha não bloqueante da complementação
- **THEN** a sub-aba SHALL continuar utilizável com os dados do CKAN e o cache BTD anterior

#### Scenario: Demais sub-abas inalteradas

- **WHEN** a sobreposição BTD é usada em `Estoque`
- **THEN** `Apetite do mercado` NÃO SHALL ser alterada
- **THEN** `Visão geral` SHALL usar a série de estoque resultante sem exigir nova requisição ao BTD
