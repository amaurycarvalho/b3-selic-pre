# Spec Delta

## Purpose

Exibir, na aba Tesouro Direto, a composição percentual do estoque e o apetite percentual do mercado, com gráficos de percentual atual e evolução, carregamento lazy e atualização independente.

## ADDED Requirements

### Requirement: Sub-abas de análise

A aba `Tesouro Direto` SHALL conter as sub-abas `Visão geral`, `Estoque` e `Apetite do mercado`.

As tabelas brutas de vendas e resgates NÃO SHALL aparecer na GUI; elas permanecem apenas na CLI.

#### Scenario: Sub-abas visíveis

- **WHEN** o usuário abre a aba `Tesouro Direto`
- **THEN** as sub-abas `Visão geral`, `Estoque` e `Apetite do mercado` SHALL estar disponíveis

#### Scenario: Sub-aba padrão

- **WHEN** a aba `Tesouro Direto` é aberta pela primeira vez
- **THEN** `Visão geral` SHALL estar selecionada

#### Scenario: Sem tabelas brutas

- **WHEN** o usuário procura tabelas de vendas ou resgates na GUI
- **THEN** elas NÃO SHALL existir
- **THEN** os dados brutos SHALL continuar disponíveis na CLI

### Requirement: Dois gráficos por sub-aba

Cada sub-aba SHALL exibir um gráfico de **percentual atual** e um gráfico de **evolução**.

O gráfico de evolução SHALL usar a janela selecionada. O gráfico atual SHALL usar o último dado ou a agregação da janela, conforme a sub-aba.

#### Scenario: Dois gráficos

- **WHEN** uma sub-aba é exibida
- **THEN** ela SHALL conter exatamente um gráfico de percentual atual e um de evolução

#### Scenario: Janela compartilhada

- **WHEN** o usuário muda a janela
- **THEN** o gráfico de evolução e o gráfico atual SHALL refletir a mesma janela

### Requirement: Visão geral

A `Visão geral` SHALL comparar o percentual atual de estoque e de apetite por família e exibir a evolução do gap entre eles.

O gráfico atual SHALL usar o último mês para estoque e a janela selecionada para apetite. A evolução SHALL mostrar o gap ao longo da janela.

#### Scenario: Comparação atual

- **WHEN** a `Visão geral` é exibida
- **THEN** o gráfico atual SHALL comparar estoque e apetite por família

#### Scenario: Evolução do gap

- **WHEN** a `Visão geral` é exibida
- **THEN** o gráfico de evolução SHALL mostrar o gap entre apetite e estoque

### Requirement: Sub-aba Estoque

A sub-aba `Estoque` SHALL exibir o percentual do último mês consolidado por família e por título, e a evolução mensal da composição.

A base SHALL ser `valor_estoque`. A sub-aba NÃO SHALL somar meses nem exibir série diária.

#### Scenario: Percentual atual

- **WHEN** a sub-aba `Estoque` é exibida
- **THEN** o gráfico atual SHALL mostrar o percentual do último mês por família
- **THEN** o detalhe por título SHALL estar disponível

#### Scenario: Evolução mensal

- **WHEN** a janela é 12 meses ou 3 anos
- **THEN** o gráfico de evolução SHALL usar buckets mensais

#### Scenario: Sem soma entre meses

- **WHEN** mais de um mês está na janela
- **THEN** cada mês SHALL ser exibido isoladamente
- **THEN** os valores NÃO SHALL ser somados entre meses

### Requirement: Sub-aba Apetite do mercado

A sub-aba `Apetite do mercado` SHALL exibir o percentual de vendas da janela selecionada por família e por título, e a evolução da composição da demanda.

A base SHALL ser o valor de vendas. A janela padrão SHALL ser 14 dias. O percentual atual SHALL ser a agregação da janela, com rótulo explícito.

#### Scenario: Percentual atual agregado

- **WHEN** a sub-aba `Apetite do mercado` é exibida
- **THEN** o gráfico atual SHALL mostrar a agregação da janela selecionada
- **THEN** o rótulo SHALL indicar a janela

#### Scenario: Evolução da demanda

- **WHEN** a janela é 14 dias
- **THEN** a evolução SHALL usar buckets diários
- **WHEN** a janela é 3 meses
- **THEN** a evolução SHALL usar buckets semanais
- **WHEN** a janela é 12 meses ou 3 anos
- **THEN** a evolução SHALL usar buckets mensais

#### Scenario: Fluxo líquido

- **WHEN** o detalhe da sub-aba é exibido
- **THEN** o fluxo líquido (vendas − recompras) SHALL estar disponível
- **THEN** vencimentos e cupons NÃO SHALL compor o fluxo

### Requirement: Seletor de janela

Cada sub-aba SHALL oferecer as janelas 14d, 3m, 12m e 3a.

A janela SHALL ser ancorada na maior data disponível. O sistema NÃO SHALL gerar períodos futuros.

#### Scenario: Janelas disponíveis

- **WHEN** o seletor é aberto
- **THEN** as opções 14d, 3m, 12m e 3a SHALL estar disponíveis

#### Scenario: Sem projeção

- **WHEN** uma janela é aplicada
- **THEN** o gráfico SHALL conter apenas dados observados
- **THEN** nenhum período futuro SHALL ser desenhado

### Requirement: Carregamento lazy e cache

Na primeira exibição de uma sub-aba, o sistema SHALL ler apenas o cache analítico.

Se não houver cache válido, a sub-aba SHALL orientar “clique em Atualizar” e NÃO SHALL baixar automaticamente. Cada sub-aba SHALL ter “Atualizar” e “Ignorar cache”.

#### Scenario: Cache na primeira exibição

- **WHEN** a sub-aba fica visível pela primeira vez e há cache válido
- **THEN** os gráficos SHALL ser desenhados a partir do cache
- **THEN** nenhuma requisição SHALL ser feita

#### Scenario: Sem cache

- **WHEN** a sub-aba fica visível e não há cache válido
- **THEN** ela SHALL orientar o clique em “Atualizar”
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Ignorar cache

- **WHEN** o usuário marca “Ignorar cache” e clica em “Atualizar”
- **THEN** o sistema SHALL fazer uma verificação condicional
- **THEN** uma resposta `304` SHALL reutilizar o cache

### Requirement: Atualização independente e status

Cada sub-aba SHALL ter atualização, progresso e status próprios. Falha em uma sub-aba NÃO SHALL impedir as demais.

O status SHALL indicar a fonte (`Cache` ou `Tesouro Transparente`), o instante da extração e a data mais recente do dataset.

#### Scenario: Falha isolada

- **WHEN** a atualização de `Estoque` falha
- **THEN** `Apetite do mercado` e `Visão geral` SHALL permanecer utilizáveis

#### Scenario: Status de cache

- **WHEN** os dados vêm do cache
- **THEN** o status SHALL exibir `Fonte: Cache` e o instante da extração

#### Scenario: Data mais recente

- **WHEN** os dados são exibidos
- **THEN** o status SHALL indicar o último mês do estoque ou a maior data de vendas, conforme a sub-aba

### Requirement: Responsividade e fechamento

Download, parsing e cálculo SHALL executar fora da thread da UI. A UI SHALL ser atualizada via `root.after`.

Durante a carga, a sub-aba SHALL exibir progresso indeterminado e desabilitar sua atualização. Fechar a janela durante a carga NÃO SHALL lançar exceção.

#### Scenario: Progresso indeterminado

- **WHEN** uma sub-aba está carregando
- **THEN** ela SHALL exibir progresso indeterminado
- **THEN** sua ação de atualização SHALL ficar desabilitada

#### Scenario: Fechar durante a carga

- **WHEN** o usuário fecha a janela durante uma carga
- **THEN** nenhuma exceção SHALL ser lançada

### Requirement: View-model headless e orçamento de UI

O estado de cada sub-aba SHALL ser calculado por um view-model headless, sem importar Tkinter.

Testes que importam Tkinter ou a GUI SHALL continuar marcados com `@pytest.mark.ui`. O orçamento atual de 5 testes de UI NÃO SHALL aumentar.

#### Scenario: Estado sem display

- **WHEN** um teste valida gráficos, filtros, janela e status
- **THEN** ele SHALL executar sem Tkinter
- **THEN** ele SHALL importar o view-model headless

#### Scenario: Orçamento respeitado

- **WHEN** a change é validada
- **THEN** o total de testes de UI SHALL permanecer em 5 ou menos
