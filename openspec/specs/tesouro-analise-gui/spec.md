# tesouro-analise-gui Specification

## Purpose

Exibir, na aba Tesouro Direto, a composição percentual do estoque e o apetite percentual do mercado, com gráficos de percentual atual e evolução, carregamento lazy e atualização independente.

## Requirements

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

### Requirement: Controles e status da sub-aba

Cada sub-aba SHALL ter:

- botão `Atualizar` somente com ícone, trocando para o ícone de carregamento durante a atualização;
- tooltips no seletor de janela, no botão `Atualizar` e no checkbox `Ignorar cache`;
- statusbar própria, sempre visível na base, com fonte, extração, data-base e barra de progresso indeterminado;
- separadores visuais entre a seleção de dados, a área de gráficos e a statusbar;
- linha de detalhe (por exemplo, fluxo líquido) ao lado do checkbox `Ignorar cache`, sem ocupar espaço acima da statusbar;
- leitura inicial do cache fora da thread da UI, sem acesso automático à rede.

#### Scenario: Controles identificáveis

- **WHEN** uma sub-aba é exibida
- **THEN** o botão `Atualizar` SHALL exibir apenas o ícone
- **THEN** o seletor, o botão e o checkbox SHALL ter tooltips

#### Scenario: Progresso na statusbar

- **WHEN** a sub-aba está carregando
- **THEN** a barra de progresso indeterminado SHALL aparecer na statusbar
- **THEN** os controles de atualização SHALL ficar desabilitados

#### Scenario: Separadores

- **WHEN** a sub-aba é exibida
- **THEN** separadores SHALL dividir a seleção de dados, os gráficos e a statusbar

### Requirement: Texto orientativo redimensionável

Cada sub-aba SHALL exibir um texto somente leitura ao lado dos gráficos,
contendo as seções `Objetivo`, `Responde a pergunta`, `Indicadores envolvidos`
e `Como interpretar`. Os títulos das seções SHALL estar em negrito e terminar
com `:`.

Uma splitbar móvel SHALL separar o texto orientativo da área de gráficos.

#### Scenario: Seções obrigatórias

- **WHEN** o texto orientativo é exibido
- **THEN** ele SHALL conter `Objetivo`, `Responde a pergunta`, `Indicadores envolvidos` e `Como interpretar`

#### Scenario: Splitbar móvel

- **WHEN** o usuário arrasta a splitbar
- **THEN** a divisão entre texto e gráficos SHALL mudar de tamanho

### Requirement: Toolbars verticais por gráfico e hover

Cada gráfico SHALL ter uma toolbar independente, com as mesmas funções da
toolbar do gráfico SELIC Pré, incluindo cópia da imagem. A toolbar SHALL ser
exibida na vertical, do lado esquerdo do respectivo gráfico, sem separadores
entre os botões.

Quando o cursor estiver sobre um ponto de dados, o sistema SHALL exibir um
rótulo com o conteúdo daquele ponto.

#### Scenario: Toolbar por gráfico

- **WHEN** uma sub-aba é exibida
- **THEN** cada gráfico SHALL ter sua própria toolbar
- **THEN** a toolbar SHALL aparecer na vertical à esquerda do gráfico

#### Scenario: Independência

- **WHEN** o usuário navega no primeiro gráfico
- **THEN** a toolbar do segundo gráfico SHALL permanecer independente

#### Scenario: Rótulo no hover

- **WHEN** o cursor passa sobre um ponto de dados
- **THEN** um rótulo SHALL mostrar os valores daquele ponto
- **THEN** o rótulo SHALL desaparecer ao sair do ponto

### Requirement: Títulos e grade vertical

A `Visão geral` SHALL usar os títulos `Estoque vs Apetite do mercado (janela até
data)` e `Gap Apetite menos Estoque (janela até data)`.

As evoluções de `Estoque` e `Apetite do mercado` SHALL exibir grades verticais
nos pontos de dados.

#### Scenario: Títulos padronizados

- **WHEN** a `Visão geral` é exibida
- **THEN** os títulos SHALL seguir a redação definida

#### Scenario: Grade vertical

- **WHEN** a evolução de `Estoque` ou `Apetite do mercado` é exibida
- **THEN** o gráfico SHALL ter linhas de grade verticais nos pontos de dados

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

### Requirement: Estados de carregamento e cache

Quando não houver dados em cache, os gráficos SHALL exibir um texto centralizado
informando que não há dados e a statusbar SHALL orientar a pressionar
`Atualizar`.

Quando houver dados em cache, durante a leitura os gráficos SHALL exibir um
texto centralizado informando que os dados estão sendo carregados.

#### Scenario: Sem cache

- **WHEN** uma sub-aba sem cache fica visível
- **THEN** os gráficos SHALL mostrar um texto centralizado de ausência de dados
- **THEN** a statusbar SHALL orientar a pressionar `Atualizar`

#### Scenario: Com cache

- **WHEN** uma sub-aba com cache fica visível e os dados ainda estão sendo lidos
- **THEN** os gráficos SHALL mostrar um texto centralizado de carregamento

### Requirement: Leitura inicial sem bloquear a UI

A primeira exibição de uma sub-aba SHALL ler apenas o cache, em thread separada
da UI, e atualizar os widgets via `root.after`.

A leitura SHALL ser restrita aos dados da sub-aba: `Visão geral` lê estoque e
vendas; `Estoque` lê apenas estoque; `Apetite do mercado` lê vendas e resgates.

#### Scenario: Sub-aba visível é a única construída

- **WHEN** o usuário seleciona `Tesouro Direto`
- **THEN** apenas a sub-aba visível SHALL ser construída
- **THEN** as demais SHALL permanecer sem conteúdo até a primeira visibilidade

#### Scenario: Cache não bloqueia

- **WHEN** a sub-aba visível é construída
- **THEN** a leitura do cache SHALL ocorrer fora da thread da UI
- **THEN** nenhuma requisição de rede SHALL ser iniciada

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
