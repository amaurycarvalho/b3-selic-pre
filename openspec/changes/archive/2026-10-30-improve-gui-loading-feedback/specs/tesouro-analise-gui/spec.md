# Spec Delta

## MODIFIED Requirements

### Requirement: Estados de carregamento e cache

Sem dados em cache e sem carga em andamento, os gráficos SHALL mostrar um texto centralizado de ausência de dados e a statusbar SHALL orientar a pressionar `Atualizar`.

O texto fixo `Processando as informações. Aguarde…` SHALL existir atrás dos gráficos. Ao selecionar uma sub-aba, os gráficos SHALL ficar temporariamente ocultos para que esse texto apareça. Ao acionar `Atualizar`, os gráficos também SHALL ficar ocultos enquanto a carga processa. Em ambos os casos, os gráficos SHALL ser reexibidos somente depois que a carga de dados e o desenho concluírem.

O texto fixo SHALL ser apresentado antes do trabalho pesado de construção, carga e desenho. Na troca de janela, os gráficos SHALL permanecer visíveis, sem o texto fixo, e o ponteiro de espera SHALL indicar o redesenho.

#### Scenario: Sem cache

- **WHEN** uma sub-aba sem cache fica visível e nenhuma carga está em andamento
- **THEN** os gráficos SHALL mostrar um texto centralizado de ausência de dados
- **THEN** a statusbar SHALL orientar a pressionar `Atualizar`
- **THEN** a statusbar SHALL usar a severidade de aviso

#### Scenario: Sem cache e carregando

- **WHEN** o usuário inicia uma atualização em uma sub-aba sem dados em cache
- **THEN** os gráficos SHALL ficar ocultos e o texto fixo `Processando as informações. Aguarde…` SHALL ser exibido
- **THEN** a statusbar SHALL indicar que a carga está em andamento
- **THEN** a statusbar NÃO SHALL orientar a pressionar `Atualizar`
- **THEN** a statusbar NÃO SHALL usar a severidade de aviso

#### Scenario: Com cache

- **WHEN** uma sub-aba com cache fica visível e os dados ainda estão sendo lidos
- **THEN** os gráficos SHALL ficar ocultos e o texto fixo de processamento SHALL ser exibido

#### Scenario: Seleção de sub-aba

- **WHEN** o usuário seleciona ou reexibe uma sub-aba
- **THEN** os gráficos SHALL ficar temporariamente ocultos
- **THEN** o texto fixo `Processando as informações. Aguarde…` SHALL aparecer no lugar deles
- **THEN** após a carga de dados e o desenho, os gráficos SHALL voltar a ser visíveis

#### Scenario: Atualizar com dados existentes

- **WHEN** o usuário aciona `Atualizar` com dados já exibidos
- **THEN** os gráficos SHALL ficar ocultos e o texto fixo de processamento SHALL ser exibido
- **THEN** a statusbar e o progresso indeterminado SHALL indicar a atualização
- **THEN** os gráficos atualizados SHALL ser reexibidos somente após a carga de dados e o desenho concluírem

#### Scenario: Aviso apresentado antes do processamento

- **WHEN** uma sub-aba fica visível pela primeira vez
- **THEN** o texto fixo de processamento SHALL ser desenhado antes da construção dos gráficos e da leitura dos dados
- **THEN** a janela SHALL permanecer responsiva para pintar esse texto antes do trabalho pesado

#### Scenario: Gráficos reexibidos ao concluir

- **WHEN** a carga de dados e o desenho terminam com sucesso
- **THEN** os gráficos SHALL ser reexibidos
- **THEN** o texto fixo SHALL voltar a ficar atrás dos gráficos

#### Scenario: Gráficos restaurados após falha

- **WHEN** a carga ou o desenho falha
- **THEN** os gráficos SHALL ser restaurados
- **THEN** o texto fixo SHALL deixar de ser visível
- **THEN** a falha SHALL ser identificada na statusbar

#### Scenario: Troca de janela

- **WHEN** o usuário altera a janela de análise de uma sub-aba
- **THEN** os gráficos SHALL permanecer visíveis
- **THEN** o texto fixo de processamento NÃO SHALL ser exibido
- **THEN** o ponteiro de espera SHALL ser usado enquanto os gráficos são redesenhados

## ADDED Requirements

### Requirement: Ponteiro de espera ao exibir e atualizar

Enquanto uma sub-aba está carregando ou desenhando seu conteúdo, a janela SHALL exibir o ponteiro de espera `watch`. O ponteiro SHALL voltar ao padrão quando o processamento terminar, inclusive em caso de falha.

#### Scenario: Ponteiro ao exibir a sub-aba

- **WHEN** uma sub-aba fica visível e inicia a leitura de cache e o desenho dos gráficos
- **THEN** a janela SHALL exibir o ponteiro `watch`
- **THEN** o ponteiro SHALL permanecer até o primeiro desenho terminar

#### Scenario: Ponteiro ao atualizar

- **WHEN** o usuário aciona `Atualizar` em uma sub-aba
- **THEN** a janela SHALL exibir o ponteiro `watch`
- **THEN** o ponteiro SHALL permanecer durante a busca, o processamento e o desenho dos gráficos

#### Scenario: Ponteiro restaurado após falha

- **WHEN** a carga ou o desenho falha
- **THEN** a janela SHALL restaurar o ponteiro padrão
- **THEN** o erro SHALL ser exibido sem manter o ponteiro de espera
