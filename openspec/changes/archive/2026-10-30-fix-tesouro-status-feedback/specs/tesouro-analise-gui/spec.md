# Spec Delta

## MODIFIED Requirements

### Requirement: Estados de carregamento e cache

Quando não houver dados em cache e nenhuma carga estiver em andamento, os gráficos SHALL exibir um texto centralizado informando que não há dados e a statusbar SHALL orientar a pressionar `Atualizar`.

Enquanto uma carga estiver em andamento, independentemente de haver cache, os gráficos SHALL exibir um texto centralizado informando que os dados estão sendo carregados e a statusbar SHALL exibir o estado de carga em vez da orientação de cache vazio.

#### Scenario: Sem cache

- **WHEN** uma sub-aba sem cache fica visível e nenhuma carga está em andamento
- **THEN** os gráficos SHALL mostrar um texto centralizado de ausência de dados
- **THEN** a statusbar SHALL orientar a pressionar `Atualizar`
- **THEN** a statusbar SHALL usar a severidade de aviso

#### Scenario: Sem cache e carregando

- **WHEN** o usuário inicia uma atualização em uma sub-aba sem dados em cache
- **THEN** os gráficos SHALL mostrar um texto centralizado de carregamento
- **THEN** a statusbar SHALL indicar que a carga está em andamento
- **THEN** a statusbar NÃO SHALL orientar a pressionar `Atualizar`
- **THEN** a statusbar NÃO SHALL usar a severidade de aviso

#### Scenario: Com cache

- **WHEN** uma sub-aba com cache fica visível e os dados ainda estão sendo lidos
- **THEN** os gráficos SHALL mostrar um texto centralizado de carregamento

## ADDED Requirements

### Requirement: Nova tentativa após falha

O início de uma nova carga SHALL remover da statusbar e dos gráficos a mensagem de erro da tentativa anterior. A mensagem de erro SHALL voltar a ser exibida apenas se a nova carga falhar novamente.

#### Scenario: Retentativa após erro

- **WHEN** uma atualização falhou e o usuário inicia outra atualização
- **THEN** a statusbar SHALL exibir o estado da nova carga
- **THEN** a statusbar NÃO SHALL exibir o erro da tentativa anterior
- **THEN** os gráficos NÃO SHALL exibir o erro da tentativa anterior

#### Scenario: Nova falha

- **WHEN** a nova tentativa também falha
- **THEN** a statusbar SHALL exibir o erro da nova tentativa

### Requirement: Reavaliação do cache ao reexibir a sub-aba

Ao reexibir uma sub-aba que ainda não possui dados, o sistema SHALL reavaliar a disponibilidade de cache em disco. Se o cache tiver sido preenchido desde a primeira exibição, a sub-aba SHALL lê-lo sem acesso à rede e atualizar os gráficos e a statusbar.

#### Scenario: Cache preenchido por outra sub-aba

- **WHEN** uma sub-aba é reexibida sem dados porque o cache estava vazio na primeira exibição
- **THEN** o sistema SHALL reavaliar a disponibilidade de cache
- **THEN** se o cache estiver disponível, a sub-aba SHALL lê-lo sem acesso à rede
- **THEN** a statusbar SHALL deixar de orientar a pressionar `Atualizar`
- **THEN** os gráficos SHALL ser desenhados a partir do cache

#### Scenario: Cache ainda ausente

- **WHEN** a sub-aba é reexibida e o cache continua ausente
- **THEN** a statusbar SHALL continuar orientando a pressionar `Atualizar`
- **THEN** nenhum acesso à rede SHALL ser iniciado

### Requirement: Etapa e origem da carga

Durante uma atualização, a statusbar SHALL distinguir a leitura do cache da atualização junto ao Tesouro Transparente e SHALL indicar a etapa corrente quando ela for conhecida (`vendas`, `resgates` ou `estoque`). A barra de progresso SHALL permanecer indeterminada.

#### Scenario: Leitura inicial do cache

- **WHEN** a carga lê apenas o cache na primeira exibição
- **THEN** a statusbar SHALL informar que os dados estão sendo lidos do cache
- **THEN** nenhuma etapa de download SHALL ser exibida
- **THEN** nenhum acesso à rede SHALL ser iniciado

#### Scenario: Atualização pela rede com etapas

- **WHEN** o usuário clica em `Atualizar` e há acesso ao Tesouro Transparente
- **THEN** a statusbar SHALL informar que os dados estão sendo atualizados
- **THEN** a statusbar SHALL indicar a etapa corrente à medida que vendas, resgates ou estoque são processados
- **THEN** a barra de progresso SHALL permanecer indeterminada

#### Scenario: Falha de leitura do cache

- **WHEN** a leitura do cache falha por motivo diferente de ausência de arquivo
- **THEN** a statusbar SHALL informar a falha de leitura do cache
- **THEN** a statusbar NÃO SHALL afirmar que não há dados em cache
