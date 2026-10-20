## Purpose

Oferecer, na interface gráfica, um ponto único de informações institucionais da aplicação, apresentação do projeto, acesso a recursos úteis e aviso de atualização disponível.

## ADDED Requirements

### Requirement: Botão "Sobre" na barra superior

A interface gráfica SHALL exibir um botão "Sobre" na barra superior, usando o ícone `help-about.png`, posicionado à direita do botão de copiar dados e visualmente separado dos botões de busca e de cópia.

#### Scenario: Botão visível ao abrir a janela

- **WHEN** a janela principal é renderizada
- **THEN** o botão "Sobre" SHALL estar visível à direita do botão de copiar dados
- **AND** SHALL usar o ícone `help-about.png`

#### Scenario: Destaque visual em relação aos demais botões

- **WHEN** a barra superior é renderizada
- **THEN** SHALL existir um espaçamento maior entre o botão de copiar dados e o botão de busca
- **AND** SHALL existir um espaçamento adicional entre o botão de copiar dados e o botão "Sobre"

#### Scenario: Tooltip do botão "Sobre"

- **WHEN** o cursor permanece sobre o botão "Sobre"
- **THEN** uma dica de texto SHALL ser exibida após o atraso padrão de tooltip

### Requirement: Janela modal de informações

O botão "Sobre" SHALL abrir uma janela de diálogo modal que reúne as informações institucionais e os atalhos da aplicação.

#### Scenario: Diálogo aberto como modal

- **WHEN** o usuário aciona o botão "Sobre"
- **THEN** uma nova janela de diálogo SHALL ser exibida
- **AND** a janela principal NÃO SHALL aceitar interação enquanto o diálogo estiver aberto

#### Scenario: Identidade da aplicação

- **WHEN** o diálogo é exibido
- **THEN** ele SHALL mostrar o ícone da aplicação
- **AND** SHALL mostrar o nome e a versão no formato `Taxas Referenciais SELIC (B3) vX.Y.Z`
- **AND** a versão SHALL ser obtida de `__version__`

#### Scenario: Data de lançamento e licença

- **WHEN** o diálogo é exibido
- **THEN** ele SHALL mostrar a data de lançamento no formato ISO `YYYY-MM-DD`
- **AND** a data SHALL ser obtida de `__release_date__`
- **AND** ele SHALL mostrar a licença "Software livre e de código aberto (GNU GPLv3)"

#### Scenario: Texto de apresentação

- **WHEN** o diálogo é exibido
- **THEN** ele SHALL mostrar um texto curto de apresentação da aplicação, derivado da descrição do projeto no `README.md`

### Requirement: Botão "Fechar" no diálogo

O diálogo SHALL oferecer um botão "Fechar" que encerra a janela de informações e libera a interação com a janela principal.

#### Scenario: Fechar pelo botão do diálogo

- **WHEN** o diálogo está aberto
- **AND** o usuário aciona o botão "Fechar"
- **THEN** o diálogo SHALL ser encerrado
- **AND** a janela principal SHALL voltar a aceitar interação

#### Scenario: Reabrir o diálogo após fechar

- **WHEN** o usuário fecha o diálogo pelo botão "Fechar"
- **AND** aciona novamente o botão "Sobre"
- **THEN** uma nova janela de diálogo SHALL ser exibida

### Requirement: Atalho para o repositório

O diálogo SHALL oferecer um botão que abre o repositório do projeto no navegador padrão do sistema.

#### Scenario: Abrir repositório

- **WHEN** o usuário aciona o botão do repositório
- **THEN** o sistema SHALL abrir `https://github.com/amaurycarvalho/b3-selic-pre` no navegador padrão

### Requirement: Atalho para o diretório de logs

O diálogo SHALL oferecer um botão que abre o diretório de logs da aplicação no aplicativo padrão do sistema. Quando o diretório não existir, o diálogo SHALL informar a indisponibilidade em seu próprio conteúdo, sem criar o diretório e sem encerrar o diálogo.

#### Scenario: Abrir diretório de logs existente

- **WHEN** o diretório de logs existe
- **AND** o usuário aciona o botão de logs
- **THEN** o sistema SHALL abrir o diretório no aplicativo padrão do sistema

#### Scenario: Diretório de logs ausente

- **WHEN** o diretório de logs não existe
- **AND** o usuário aciona o botão de logs
- **THEN** o diálogo SHALL informar que o diretório de logs está indisponível
- **AND** NÃO SHALL criar o diretório
- **AND** NÃO SHALL falhar silenciosamente

### Requirement: Aviso de nova versão

Quando a verificação de versão indicar uma versão mais recente que a atual, o diálogo SHALL exibir, ao final do conteúdo, o aviso "Nova versão vX.Y.Z disponível" e um botão que abre a página da release no navegador padrão. Quando não houver versão mais nova ou a verificação falhar, nenhum aviso SHALL ser exibido.

#### Scenario: Versão mais recente encontrada

- **WHEN** a verificação indica uma versão mais recente
- **THEN** o diálogo SHALL exibir "Nova versão vX.Y.Z disponível" ao final do conteúdo
- **AND** SHALL exibir um botão para abrir a página da release

#### Scenario: Abrir página da release

- **WHEN** o aviso de nova versão está visível
- **AND** o usuário aciona o botão da release
- **THEN** o sistema SHALL abrir a página da release correspondente no navegador padrão

#### Scenario: Sem versão mais nova

- **WHEN** a versão disponível é igual ou anterior à versão atual
- **THEN** nenhum aviso de nova versão SHALL ser exibido

#### Scenario: Falha na verificação

- **WHEN** a verificação de versão falha, excede o tempo limite ou retorna dados inválidos
- **THEN** nenhum aviso de nova versão SHALL ser exibido
- **AND** nenhuma mensagem de erro SHALL ser exibida no diálogo

#### Scenario: Verificação não bloqueia o diálogo

- **WHEN** o diálogo é aberto
- **THEN** a verificação de versão SHALL ocorrer em segundo plano
- **AND** o conteúdo principal do diálogo SHALL permanecer visível e responsivo enquanto a verificação está em andamento

### Requirement: Data de lançamento mantida pela release

O pacote SHALL expor `__release_date__` no formato ISO `YYYY-MM-DD`, e o processo de atualização de versão SHALL atualizar essa data para a data corrente sempre que alterar `__version__`.

#### Scenario: Data de lançamento disponível

- **WHEN** o pacote é importado
- **THEN** `__release_date__` SHALL estar disponível no formato `YYYY-MM-DD`

#### Scenario: Atualização de versão atualiza a data

- **WHEN** o processo de release altera a versão da aplicação
- **THEN** `__release_date__` SHALL ser alterado para a data corrente
