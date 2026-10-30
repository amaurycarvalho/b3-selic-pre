## MODIFIED Requirements

### Requirement: Carregamento lazy e cache

Na primeira exibição de uma sub-aba, o sistema SHALL ler apenas as séries pré-calculadas do cache analítico, sem parse de CSV e sem rede. Se as séries faltarem mas houver cache bruto válido, ele SHALL montá-las uma vez em background a partir do cache bruto, persistir e desenhar, sem download. Sem cache analítico nem bruto, a sub-aba SHALL orientar “clique em Atualizar”. Cada sub-aba SHALL ter “Atualizar” e “Ignorar cache”.

#### Scenario: Cache na primeira exibição

- **WHEN** a sub-aba fica visível pela primeira vez e há séries pré-calculadas válidas
- **THEN** os gráficos SHALL ser desenhados a partir dessas séries
- **THEN** nenhum CSV bruto SHALL ser lido ou parseado
- **THEN** nenhuma requisição SHALL ser feita

#### Scenario: Séries ausentes com cache bruto

- **WHEN** as séries pré-calculadas faltam mas há cache bruto válido
- **THEN** as séries SHALL ser montadas uma vez em background a partir do cache bruto
- **THEN** o resultado SHALL ser persistido no cache analítico
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Sem cache

- **WHEN** a sub-aba fica visível e não há séries pré-calculadas nem cache bruto válido
- **THEN** ela SHALL orientar o clique em “Atualizar”
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Ignorar cache

- **WHEN** o usuário marca “Ignorar cache” e clica em “Atualizar”
- **THEN** o sistema SHALL fazer uma verificação condicional
- **THEN** uma resposta `304` SHALL reutilizar o cache

## ADDED Requirements

### Requirement: Troca de janela com séries pré-calculadas

Uma troca de janela SHALL obter os dados por filtragem e agregação das séries pré-calculadas, sem ler ou parsear o CSV bruto e sem acessar a rede. Os valores SHALL continuar ancorados na maior data disponível da fonte.

#### Scenario: Troca de janela

- **WHEN** o usuário alterna entre 14d, 3m, 12m e 3a
- **THEN** a sub-aba SHALL reutilizar as séries pré-calculadas
- **THEN** nenhum CSV bruto SHALL ser lido ou parseado
- **THEN** nenhuma requisição de rede SHALL ser feita

#### Scenario: Sem projeção

- **WHEN** uma janela é aplicada
- **THEN** o gráfico SHALL conter apenas períodos observados
- **THEN** nenhum período futuro SHALL ser desenhado

### Requirement: Pré-cálculo automático após atualização

Após uma atualização bem-sucedida de uma sub-aba, o sistema SHALL iniciar, fora da thread da UI, o pré-cálculo das séries das fontes cujo conteúdo bruto mudou, reutilizando os dados já parseados pelo refresh. O pré-cálculo NÃO SHALL bloquear a exibição dos gráficos atualizados. Um `304` ou conteúdo idêntico NÃO SHALL disparar pré-cálculo.

#### Scenario: Atualizar com mudança

- **WHEN** o refresh muda o conteúdo bruto de uma fonte
- **THEN** o pré-cálculo dessa fonte SHALL iniciar automaticamente
- **THEN** os gráficos atualizados SHALL ser desenhados a partir dos dados do refresh
- **THEN** a UI NÃO SHALL ficar bloqueada durante o pré-cálculo

#### Scenario: Atualizar sem mudança

- **WHEN** o refresh recebe `304` ou o conteúdo bruto permanece idêntico
- **THEN** nenhum pré-cálculo SHALL ser iniciado

#### Scenario: Falha no pré-cálculo

- **WHEN** o pré-cálculo falha
- **THEN** o refresh SHALL permanecer bem-sucedido
- **THEN** os gráficos SHALL ser desenhados a partir dos dados atualizados
- **THEN** a série válida anterior SHALL continuar utilizável
