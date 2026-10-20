## Purpose

Descrever as abas de Resgates e Estoque na janela "Tesouro Direto" da GUI, com filtros, tabelas, limites, atualização e status próprios, sem alterar a janela principal.

## ADDED Requirements

### Requirement: Abas na janela Tesouro Direto

A janela "Tesouro Direto" SHALL exibir `ttk.Notebook` com as abas `Vendas`, `Resgates` e `Estoque`.

A aba `Vendas` SHALL manter o comportamento da capability `tesouro-direto-gui`. As abas `Resgates` e `Estoque` SHALL ter filtros, tabela, atualização e status próprios.

#### Scenario: Abas são exibidas

- **WHEN** o usuário abre a janela Tesouro Direto
- **THEN** as abas `Vendas`, `Resgates` e `Estoque` SHALL estar disponíveis

#### Scenario: Aba de vendas permanece

- **WHEN** o usuário alterna para `Resgates` ou `Estoque`
- **THEN** a aba `Vendas` SHALL continuar disponível e com seu estado preservado

#### Scenario: Falha isolada

- **WHEN** o carregamento de uma aba falha
- **THEN** as demais abas SHALL permanecer utilizáveis

### Requirement: Aba de resgates

A aba `Resgates` SHALL exibir tabela com as colunas `Tipo`, `Título`, `Vencimento`, `Data do Resgate`, `PU`, `Quantidade` e `Valor`.

A aba SHALL oferecer filtro por tipo (`Todos`, `Recompra`, `Cupom`, `Vencimento`), título e período inclusivo; período padrão de 12 meses relativos à maior `data_resgate`; limite de 5.000 linhas exibidas.

#### Scenario: Tabela de resgates

- **WHEN** há resgates disponíveis
- **THEN** a tabela SHALL exibir uma linha por resgate
- **THEN** as datas SHALL usar `DD/MM/YYYY`
- **THEN** os números SHALL usar vírgula decimal

#### Scenario: Filtro por tipo

- **WHEN** o usuário seleciona `Recompra`
- **THEN** a tabela SHALL exibir apenas recompras

#### Scenario: Período padrão

- **WHEN** a aba é aberta sem filtros
- **THEN** o período SHALL cobrir 12 meses até a maior `data_resgate` disponível

#### Scenario: Limite de linhas

- **WHEN** o filtro encontra mais de 5.000 resgates
- **THEN** a tabela SHALL exibir no máximo 5.000 linhas
- **THEN** o status SHALL indicar "mostrando X de Y; refine os filtros"

#### Scenario: Recompra sem PU

- **WHEN** um resgate do tipo recompra é exibido
- **THEN** a coluna `PU` SHALL ficar vazia

### Requirement: Aba de estoque

A aba `Estoque` SHALL exibir tabela com as colunas `Título`, `Vencimento`, `Mês`, `PU`, `Quantidade` e `Valor do Estoque`.

A aba SHALL oferecer filtro por título e intervalo inclusivo de meses; período padrão de 12 meses; seleção de um mês para agregação.

#### Scenario: Tabela de estoque

- **WHEN** há registros de estoque disponíveis
- **THEN** a tabela SHALL exibir uma linha por título/mês
- **THEN** o mês SHALL usar `MM/AAAA`
- **THEN** os números SHALL usar vírgula decimal

#### Scenario: Filtro por título

- **WHEN** o usuário filtra por parte do título
- **THEN** a tabela SHALL exibir apenas os registros correspondentes

#### Scenario: Período padrão

- **WHEN** a aba é aberta sem filtros
- **THEN** a tabela SHALL cobrir os últimos 12 meses disponíveis

#### Scenario: Agregação por mês

- **WHEN** o usuário solicita agregação
- **THEN** a aba SHALL exigir um único mês
- **THEN** o resultado SHALL somar `quantidade` e `valor_estoque` apenas dentro daquele mês

#### Scenario: Não somar entre meses

- **WHEN** o intervalo contém mais de um mês
- **THEN** a aba NÃO SHALL somar `valor_estoque` entre meses

### Requirement: Atualização e cache por aba

Cada aba SHALL carregar o cache válido do seu dataset ao ser aberta. Se não houver cache válido, a aba SHALL orientar o usuário a clicar em "Atualizar" e NÃO SHALL baixar automaticamente.

Cada aba SHALL ter uma ação "Atualizar" que reutiliza o cache válido e uma opção "Ignorar cache" que força uma verificação condicional na rede.

#### Scenario: Abertura com cache

- **WHEN** a aba é aberta e existe cache válido para seus recursos
- **THEN** os dados SHALL ser carregados do cache
- **THEN** nenhuma requisição SHALL ser feita

#### Scenario: Abertura sem cache

- **WHEN** a aba é aberta e não existe cache válido
- **THEN** a aba SHALL orientar o clique em "Atualizar"
- **THEN** nenhum download SHALL ser iniciado automaticamente

#### Scenario: Ignorar cache

- **WHEN** a opção "Ignorar cache" está marcada e o usuário clica em "Atualizar"
- **THEN** o sistema SHALL fazer uma requisição condicional
- **THEN** uma resposta `304` SHALL reutilizar o cache

#### Scenario: Falha em um recurso de resgates

- **WHEN** um dos recursos de resgates falha
- **THEN** a aba SHALL exibir a mensagem daquele recurso
- **THEN** os recursos carregados com sucesso SHALL permanecer visíveis

### Requirement: Progresso, responsividade e fechamento

Durante o download e o parsing, cada aba SHALL exibir progresso indeterminado e desabilitar sua ação de atualização. A janela principal SHALL permanecer responsiva.

O download e o parsing SHALL executar fora da thread da UI e as atualizações SHALL ser feitas via `root.after`.

#### Scenario: Progresso indeterminado

- **WHEN** o download está em andamento
- **THEN** a aba SHALL exibir progresso indeterminado
- **THEN** a ação de atualização da aba SHALL permanecer desabilitada

#### Scenario: Janela principal responsiva

- **WHEN** uma aba está carregando
- **THEN** a janela principal SHALL continuar respondendo a eventos

#### Scenario: Fechar durante o download

- **WHEN** o usuário fecha a janela do Tesouro Direto durante uma carga
- **THEN** nenhuma exceção SHALL ser lançada
- **THEN** a aplicação principal SHALL permanecer utilizável

### Requirement: Status por aba

Cada aba SHALL exibir em seu status a origem dos dados (`Cache` ou `Tesouro Transparente`), o instante da extração e a data mais recente do dataset.

#### Scenario: Status de cache

- **WHEN** os dados vêm do cache
- **THEN** o status SHALL exibir "Fonte: Cache" e o instante da extração

#### Scenario: Status de download

- **WHEN** os dados vêm do Tesouro Transparente
- **THEN** o status SHALL exibir "Fonte: Tesouro Transparente"

#### Scenario: Data mais recente

- **WHEN** os dados são exibidos
- **THEN** o status SHALL indicar a maior `data_resgate` ou o maior `mes`, conforme a aba

### Requirement: View-model headless e orçamento de UI

O estado de cada aba (linhas, filtros, limite, habilitação de controles e status) SHALL ser calculado por um view-model headless, sem importar Tkinter.

Testes que importam Tkinter ou a GUI SHALL ser marcados com `@pytest.mark.ui` e SHALL respeitar o orçamento atual de 5 testes de UI. O orçamento NÃO SHALL aumentar.

#### Scenario: Estado calculado sem display

- **WHEN** um teste valida filtros, linhas, limite e controles das abas
- **THEN** ele SHALL executar sem Tkinter
- **THEN** ele SHALL importar o view-model headless

#### Scenario: Testes de UI são marcados

- **WHEN** um teste depende de Tkinter ou da janela
- **THEN** ele SHALL ser marcado com `@pytest.mark.ui`

#### Scenario: Orçamento respeitado

- **WHEN** um novo teste de UI é adicionado
- **THEN** o total SHALL permanecer dentro do orçamento
- **THEN** a alternativa headless SHALL ser preferida
