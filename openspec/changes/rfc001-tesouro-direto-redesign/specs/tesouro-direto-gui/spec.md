## Purpose

Descrever a janela separada de consulta ao Tesouro Direto na GUI, com tabela, filtros e estados de carregamento, sem alterar o gráfico principal da aplicação.

## ADDED Requirements

### Requirement: Botão de acesso na barra superior

A GUI SHALL exibir um botão "Tesouro Direto" na barra superior, visualmente separado dos controles de busca e cópia, com ícone e tooltip.

O botão SHALL abrir uma janela separada e NÃO SHALL alterar o modo de visualização do gráfico principal.

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

### Requirement: Janela separada com tabela

A janela "Tesouro Direto" SHALL exibir uma tabela rolável (`ttk.Treeview`) com as colunas do schema confirmado e barras de rolagem.

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

### Requirement: Filtros de título e período

A janela SHALL oferecer filtro por título e filtros de data inicial e final.

O filtro de título SHALL ser parcial e sem distinção de caixa/acentos. O período SHALL ser inclusivo. Datas inválidas SHALL ser rejeitadas com mensagem na própria janela.

#### Scenario: Filtro por título

- **WHEN** o usuário informa parte do nome de um título
- **THEN** a tabela SHALL exibir apenas os registros correspondentes

#### Scenario: Filtro por período

- **WHEN** o usuário informa data inicial e final válidas
- **THEN** a tabela SHALL exibir apenas os registros do intervalo inclusivo

#### Scenario: Data inválida

- **WHEN** o usuário informa uma data fora do formato `AAAA-MM-DD`
- **THEN** a janela SHALL exibir uma mensagem de validação
- **THEN** nenhum download SHALL ser iniciado

### Requirement: Atualização e cache

A janela SHALL oferecer uma ação "Atualizar" que reutiliza o cache válido e uma opção "Ignorar cache" que força o download.

Durante a atualização, a janela SHALL exibir progresso e desabilitar a ação de atualização. A janela principal SHALL permanecer responsiva.

#### Scenario: Atualização usa cache

- **WHEN** o cache é válido e o usuário clica em "Atualizar"
- **THEN** os dados SHALL ser carregados do cache
- **THEN** nenhuma requisição SHALL ser feita ao Tesouro Transparente

#### Scenario: Ignorar cache força download

- **WHEN** a opção "Ignorar cache" está marcada e o usuário clica em "Atualizar"
- **THEN** o sistema SHALL baixar o CSV novamente

#### Scenario: Progresso durante o download

- **WHEN** o download está em andamento
- **THEN** a janela SHALL exibir progresso
- **THEN** a ação de atualização SHALL permanecer desabilitada até a conclusão

#### Scenario: Janela principal continua responsiva

- **WHEN** o Tesouro Direto está carregando
- **THEN** a janela principal SHALL continuar respondendo a eventos

### Requirement: Estados de erro e status

A janela SHALL exibir mensagens de erro de comunicação e de dados em uma área de status própria.

Após uma falha, a janela SHALL permanecer utilizável. Quando os dados vierem do cache, o status SHALL indicar a fonte e o instante do download.

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
- **THEN** o status SHALL exibir "Fonte: Cache" e o instante do download

#### Scenario: Indicador de download

- **WHEN** os dados são baixados do Tesouro Transparente
- **THEN** o status SHALL exibir "Fonte: Tesouro Transparente"

### Requirement: View-model headless e orçamento de UI

O estado da janela (linhas exibidas, filtros aplicados, habilitação de controles e mensagens de status) SHALL ser calculado por um view-model headless, sem importar Tkinter.

Testes que importam Tkinter ou a GUI SHALL ser marcados com `@pytest.mark.ui` e SHALL respeitar o orçamento atual de testes de UI. O orçamento NÃO SHALL aumentar sem aprovação explícita.

#### Scenario: Estado calculado sem display

- **WHEN** um teste valida filtros, linhas e habilitação de controles
- **THEN** ele SHALL executar sem Tkinter
- **THEN** ele SHALL importar o view-model headless

#### Scenario: Testes de UI são marcados

- **WHEN** um teste depende de Tkinter ou da janela
- **THEN** ele SHALL ser marcado com `@pytest.mark.ui`

#### Scenario: Orçamento respeitado

- **WHEN** um novo teste de UI é adicionado
- **THEN** o total SHALL permanecer dentro do orçamento
- **THEN** a alternativa headless SHALL ser preferida
