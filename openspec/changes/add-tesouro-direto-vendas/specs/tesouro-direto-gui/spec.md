## Purpose

Descrever a janela separada de consulta às vendas do Tesouro Direto na GUI, com tabela, filtros, limite de linhas e estados de carregamento, sem alterar o gráfico principal da aplicação.

## ADDED Requirements

### Requirement: Botão de acesso na barra superior

A GUI SHALL exibir um botão "Tesouro Direto" na barra superior, visualmente separado dos controles de busca e cópia, com ícone e tooltip.

O botão SHALL abrir uma janela separada e NÃO SHALL alterar o modo de visualização do gráfico principal. O botão SHALL fazer parte dos widgets bloqueados pelo escudo de inicialização e só SHALL ficar interativo após o término do escudo.

#### Scenario: Botão abre a janela

- **WHEN** o usuário clica em "Tesouro Direto"
- **THEN** uma janela separada SHALL ser aberta
- **THEN** o gráfico principal SHALL permanecer inalterado

#### Scenario: Botão tem tooltip

- **WHEN** o usuário posiciona o ponteiro sobre o botão
- **THEN** o tooltip SHALL descrever a ação

#### Scenario: Escudo de inicialização é respeitado

- **WHEN** a janela principal ainda está no período de inicialização
- **THEN** o botão NÃO SHALL ficar interativo antes do término do escudo

#### Scenario: Janela única

- **WHEN** a janela do Tesouro Direto já está aberta e o usuário clica no botão novamente
- **THEN** a janela existente SHALL ser trazida para frente
- **THEN** uma segunda janela NÃO SHALL ser criada

### Requirement: Janela separada com tabela

A janela "Tesouro Direto" SHALL exibir uma tabela rolável (`ttk.Treeview`) com as colunas `Tipo`, `Vencimento`, `Liquidação`, `PU`, `Quantidade` e `Valor`, e barras de rolagem.

A janela SHALL ter título próprio e SHALL poder ser fechada sem encerrar a aplicação principal.

#### Scenario: Tabela exibe registros

- **WHEN** há registros disponíveis
- **THEN** a tabela SHALL exibir uma linha por registro
- **THEN** as colunas SHALL corresponder ao schema confirmado

#### Scenario: Tabela é rolável

- **WHEN** há mais registros do que o espaço visível
- **THEN** a tabela SHALL permitir rolagem vertical e horizontal

#### Scenario: Fechar a janela não encerra a aplicação

- **WHEN** o usuário fecha a janela do Tesouro Direto
- **THEN** a janela principal SHALL permanecer aberta e utilizável

#### Scenario: Formatação visual

- **WHEN** os registros são exibidos
- **THEN** as datas SHALL usar `DD/MM/YYYY`
- **THEN** os números SHALL usar vírgula decimal

### Requirement: Filtros de título e período

A janela SHALL oferecer filtro por título e filtros de data inicial e final.

O filtro de título SHALL ser parcial e sem distinção de caixa/acentos. O período SHALL ser inclusivo sobre `data_liquidacao`. Datas inválidas ou `inicio > fim` SHALL ser rejeitados com mensagem na própria janela, sem iniciar download.

O período padrão SHALL ser de 12 meses relativos à maior `data_liquidacao` disponível.

#### Scenario: Filtro por título

- **WHEN** o usuário informa parte do nome de um título
- **THEN** a tabela SHALL exibir apenas os registros correspondentes

#### Scenario: Filtro por período

- **WHEN** o usuário informa data inicial e final válidas
- **THEN** a tabela SHALL exibir apenas os registros de liquidação do intervalo inclusivo

#### Scenario: Data inválida

- **WHEN** o usuário informa uma data fora do formato `AAAA-MM-DD`
- **THEN** a janela SHALL exibir uma mensagem de validação
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Período invertido

- **WHEN** o usuário informa data inicial maior que a final
- **THEN** a janela SHALL exibir uma mensagem de validação
- **THEN** nenhum download SHALL ser iniciado

#### Scenario: Período padrão

- **WHEN** a janela é aberta sem filtros
- **THEN** o período SHALL cobrir 12 meses até a maior `data_liquidacao` disponível

### Requirement: Limite de linhas exibidas

A janela SHALL limitar a tabela a 5.000 linhas exibidas e SHALL informar no status quantos registros foram encontrados e quantos estão visíveis.

#### Scenario: Limite é aplicado

- **WHEN** o filtro encontra mais de 5.000 registros
- **THEN** a tabela SHALL exibir no máximo 5.000 linhas
- **THEN** o status SHALL indicar "mostrando X de Y; refine os filtros"

#### Scenario: Filtro reduz o volume

- **WHEN** o filtro encontra 5.000 registros ou menos
- **THEN** todos SHALL ser exibidos

### Requirement: Carregamento inicial e cache

Ao ser aberta, a janela SHALL carregar o cache válido, se existir. Se não houver cache válido, a janela SHALL orientar o usuário a clicar em "Atualizar" e NÃO SHALL iniciar download automaticamente.

A janela SHALL oferecer uma ação "Atualizar" que reutiliza o cache válido e uma opção "Ignorar cache" que força uma verificação condicional na rede.

#### Scenario: Abertura com cache

- **WHEN** a janela é aberta e existe cache válido
- **THEN** os dados SHALL ser carregados do cache
- **THEN** nenhuma requisição SHALL ser feita ao Tesouro Transparente

#### Scenario: Abertura sem cache

- **WHEN** a janela é aberta e não existe cache válido
- **THEN** a janela SHALL exibir a orientação para clicar em "Atualizar"
- **THEN** nenhum download SHALL ser iniciado automaticamente

#### Scenario: Atualização usa cache

- **WHEN** o cache é válido e o usuário clica em "Atualizar"
- **THEN** os dados SHALL ser carregados do cache
- **THEN** nenhuma requisição SHALL ser feita ao Tesouro Transparente

#### Scenario: Ignorar cache força verificação

- **WHEN** a opção "Ignorar cache" está marcada e o usuário clica em "Atualizar"
- **THEN** o sistema SHALL fazer uma requisição condicional ao Tesouro Transparente
- **THEN** uma resposta `304` SHALL reutilizar o cache

### Requirement: Progresso e responsividade

Durante o download e o parsing, a janela SHALL exibir progresso indeterminado e desabilitar a ação de atualização. A janela principal SHALL permanecer responsiva.

O download e o parsing SHALL executar fora da thread da UI, e as atualizações SHALL ser feitas via `root.after`.

#### Scenario: Progresso durante o download

- **WHEN** o download está em andamento
- **THEN** a janela SHALL exibir progresso indeterminado
- **THEN** a ação de atualização SHALL permanecer desabilitada até a conclusão

#### Scenario: Janela principal continua responsiva

- **WHEN** o Tesouro Direto está carregando
- **THEN** a janela principal SHALL continuar respondendo a eventos

#### Scenario: Fechar durante o download

- **WHEN** o usuário fecha a janela do Tesouro Direto enquanto o download está em andamento
- **THEN** nenhuma exceção SHALL ser lançada
- **THEN** a aplicação principal SHALL permanecer utilizável

### Requirement: Estados de erro e status

A janela SHALL exibir mensagens de erro de comunicação e de dados em uma área de status própria.

Após uma falha, a janela SHALL permanecer utilizável. Quando os dados vierem do cache, o status SHALL indicar a fonte e o instante da extração. O status SHALL também indicar a maior `data_liquidacao` disponível.

#### Scenario: Erro de comunicação

- **WHEN** o download falha por rede ou HTTP
- **THEN** a janela SHALL exibir a mensagem de comunicação
- **THEN** a janela SHALL permanecer utilizável

#### Scenario: Erro de dados

- **WHEN** o CSV tem colunas ausentes ou valores inválidos
- **THEN** a janela SHALL exibir a mensagem de dados
- **THEN** nenhuma linha inválida SHALL ser exibida

#### Scenario: Indicador de cache

- **WHEN** os dados são servidos do cache
- **THEN** o status SHALL exibir "Fonte: Cache" e o instante da extração

#### Scenario: Indicador de download

- **WHEN** os dados são baixados do Tesouro Transparente
- **THEN** o status SHALL exibir "Fonte: Tesouro Transparente"

#### Scenario: Data máxima

- **WHEN** os dados são exibidos
- **THEN** o status SHALL indicar a maior `data_liquidacao` disponível

### Requirement: View-model headless e orçamento de UI

O estado da janela (linhas exibidas, filtros aplicados, limite de linhas, habilitação de controles e mensagens de status) SHALL ser calculado por um view-model headless, sem importar Tkinter.

Testes que importam Tkinter ou a GUI SHALL ser marcados com `@pytest.mark.ui` e SHALL respeitar o orçamento atual de 5 testes de UI. O orçamento NÃO SHALL aumentar.

#### Scenario: Estado calculado sem display

- **WHEN** um teste valida filtros, linhas, limite e habilitação de controles
- **THEN** ele SHALL executar sem Tkinter
- **THEN** ele SHALL importar o view-model headless

#### Scenario: Testes de UI são marcados

- **WHEN** um teste depende de Tkinter ou da janela
- **THEN** ele SHALL ser marcado com `@pytest.mark.ui`

#### Scenario: Orçamento respeitado

- **WHEN** um novo teste de UI é adicionado
- **THEN** o total SHALL permanecer dentro do orçamento
- **THEN** a alternativa headless SHALL ser preferida
