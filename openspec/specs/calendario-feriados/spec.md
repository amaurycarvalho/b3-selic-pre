# calendario-feriados Specification

## Purpose

Manter um calendário interno de dias úteis alimentado pela ANBIMA, com cache, fallback, resolução de datas e uma aba de consulta por ano, mês e dia, para que cargas, TTLs e exibições não usem feriados como datas de negociação.

## Requirements

### Requirement: Fonte ANBIMA por ano

O sistema SHALL obter os feriados da página anual da ANBIMA (`feriados/fer_nacionais/{ano}.asp`) e SHALL registrar a URL, o ano, o instante de extração e a origem em cada leitura. NÃO SHALL existir uma segunda fonte de rede para feriados.

#### Scenario: Ano é carregado da ANBIMA
- **WHEN** o calendário do ano corrente é atualizado e a ANBIMA responde com a tabela de feriados
- **THEN** o sistema grava os feriados normalizados com origem `ANBIMA`
- **THEN** o payload registra a URL e o instante de extração

#### Scenario: Falha da ANBIMA não troca de fonte
- **WHEN** a ANBIMA responde com erro, timeout ou página inesperada
- **THEN** o sistema NÃO SHALL consultar outra fonte de rede
- **THEN** aplica o fallback definido para cache anterior

### Requirement: Normalização e validação dos feriados

O sistema SHALL normalizar datas `d/m/aa` para ISO (`AAAA-MM-DD`), SHALL remover acentos e entidades HTML do nome e SHALL validar que o dia da semana informado corresponde à data. Uma linha inválida SHALL invalidar a carga do ano, sem produzir calendário parcial.

#### Scenario: Data é normalizada
- **WHEN** a ANBIMA informa `1/1/26`
- **THEN** o feriado é armazenado como `2026-01-01`

#### Scenario: Dia da semana divergente
- **WHEN** o dia da semana declarado não corresponde à data calculada
- **THEN** o sistema trata a carga como falha de fonte
- **THEN** NÃO SHALL gravar um calendário parcial

### Requirement: Cache por ano com TTL por recência

O sistema SHALL manter um arquivo por ano com os feriados, o TTL aplicado e os metadados de origem. Anos passados SHALL ser imutáveis; o ano corrente e anos futuros SHALL usar TTL curto; ano futuro ainda não publicado SHALL usar cache negativo com TTL.

#### Scenario: Cache fresco evita nova carga
- **WHEN** o arquivo do ano existe, é válido e está dentro do TTL
- **THEN** o sistema reutiliza o cache sem acessar a ANBIMA

#### Scenario: Cache do ano corrente expira
- **WHEN** o arquivo do ano corrente está além do TTL curto
- **THEN** a próxima carga de dados SHALL revalidar o ano na ANBIMA

#### Scenario: Ano futuro ainda não publicado
- **WHEN** a ANBIMA não publica o ano futuro solicitado
- **THEN** o sistema grava um marcador negativo com TTL
- **THEN** novas cargas NÃO SHALL consultar o mesmo ano antes do TTL

### Requirement: Fallback para cache anterior e modo degradado

Quando a ANBIMA falhar, o sistema SHALL reutilizar o cache anterior do ano, marcado como defasado. Sem cache algum para o ano, o sistema SHALL aplicar apenas a regra de fim de semana e SHALL expor o estado `calendario_indisponivel`.

#### Scenario: Falha usa cache anterior
- **WHEN** a ANBIMA falha e existe cache anterior para o ano
- **THEN** o sistema usa o cache anterior
- **THEN** o estado do calendário é marcado como defasado

#### Scenario: Sem cache, fim de semana apenas
- **WHEN** a ANBIMA falha e não existe cache para o ano
- **THEN** o sistema trata sábado e domingo como não úteis
- **THEN** o estado do calendário é `calendario_indisponivel`
- **THEN** a carga de dados NÃO SHALL ser bloqueada

### Requirement: Housekeeping de três anos

O sistema SHALL remover arquivos de anos fora do intervalo `[ano_corrente - 3, ano_corrente + 1]` após uma atualização bem-sucedida. O housekeeping NUNCA SHALL remover o ano usado pela operação corrente e SHALL ignorar arquivos corrompidos.

#### Scenario: Anos antigos são removidos
- **WHEN** o ano corrente é 2026 e existe arquivo de 2021
- **THEN** o housekeeping remove o arquivo de 2021
- **THEN** mantém 2023, 2024, 2025, 2026 e 2027

#### Scenario: Corrupção não interrompe a limpeza
- **WHEN** um arquivo de ano não pode ser lido
- **THEN** o housekeeping o ignora e continua os demais

### Requirement: Resolução de dia útil

O sistema SHALL expor uma resolução que devolve a data informada quando ela é dia útil, ou o dia útil anterior quando é fim de semana ou feriado. A resolução SHALL informar `data_solicitada`, `data_resolvida`, `ajustada`, `motivo` e, quando aplicável, o nome do feriado.

#### Scenario: Fim de semana retrocede
- **WHEN** a data solicitada é sábado ou domingo
- **THEN** a resolução devolve a sexta-feira anterior
- **THEN** `motivo` é `fim_de_semana`

#### Scenario: Feriado retrocede
- **WHEN** a data solicitada é feriado em dia de semana
- **THEN** a resolução devolve o dia útil anterior
- **THEN** `motivo` é `feriado` e o nome do feriado é informado

#### Scenario: Bloco de feriados atravessa dias consecutivos
- **WHEN** a data solicitada e os dias anteriores formam um bloco de feriados
- **THEN** a resolução retrocede até o primeiro dia útil anterior ao bloco

#### Scenario: Dia útil é preservado
- **WHEN** a data solicitada é dia útil
- **THEN** a resolução devolve a própria data com `ajustada` falso

### Requirement: Resolução da janela de evolução

Para cada alvo de `7`, `14`, `21` e `28` dias corridos antes da data-base, o sistema SHALL aplicar a resolução de dia útil. A data-base SHALL ser a data já resolvida. Alvos que resultem na mesma data SHALL ser deduplicados.

#### Scenario: Alvo em feriado é ajustado
- **WHEN** um alvo da janela cai em feriado
- **THEN** o alvo é substituído pelo dia útil anterior
- **THEN** os demais alvos são preservados

#### Scenario: Alvos duplicados são colapsados
- **WHEN** dois alvos resolvem para a mesma data
- **THEN** a janela contém uma única entrada para essa data

### Requirement: Atualização junto das cargas

As cargas de dados existentes SHALL garantir o calendário do ano da data de referência antes de resolver a data. A atualização SHALL ser best-effort, com lock e TTL, e uma falha do calendário NÃO SHALL impedir a carga principal.

#### Scenario: Carga atualiza o calendário antes de resolver
- **WHEN** uma carga de dados é iniciada
- **THEN** o sistema garante o calendário do ano da data de referência
- **THEN** só depois resolve a data e consulta a fonte de dados

#### Scenario: Falha do calendário não bloqueia
- **WHEN** a atualização do calendário falha
- **THEN** a carga principal continua com o cache anterior ou com a regra de fim de semana
- **THEN** a falha é registrada em log

### Requirement: Concorrência e escrita atômica

A gravação do cache do calendário SHALL ser atômica e protegida por lock dedicado. Leituras somente de cache NÃO SHALL gravar, renomear ou remover arquivos.

#### Scenario: Cargas concorrentes usam o mesmo cache
- **WHEN** duas cargas tentam atualizar o mesmo ano ao mesmo tempo
- **THEN** o lock evita gravação concorrente
- **THEN** a segunda carga reutiliza o resultado da primeira

#### Scenario: Leitura não altera o cache
- **WHEN** a CLI ou o MCP lê o calendário em modo somente cache
- **THEN** nenhum arquivo do calendário é criado, alterado ou removido

### Requirement: Consulta e exportação do calendário

O sistema SHALL expor os feriados de um ano e a classificação de uma data como dia útil ou não, com nome, motivo e origem. A exportação SHALL suportar CSV e JSON sem gravar arquivos no servidor MCP.

#### Scenario: Listagem do ano
- **WHEN** o usuário lista os feriados de 2026
- **THEN** cada item contém data, dia da semana, nome e origem

#### Scenario: Consulta de uma data
- **WHEN** o usuário consulta uma data
- **THEN** a resposta informa se é dia útil e, quando não for, o motivo e o nome do feriado

#### Scenario: Exportação CSV
- **WHEN** o usuário exporta o ano em CSV
- **THEN** o artefato usa `;` como separador, datas ISO e colunas de data, dia da semana, nome e origem

### Requirement: Aba Feriados com árvore ano/mês/dia

A aba `Feriados` SHALL exibir um `ttk.Treeview` à esquerda e um textbox somente leitura à direita. A árvore SHALL ter ramos de ano, ramos de mês e folhas de dia; cada folha SHALL mostrar `DD` seguido do dia da semana abreviado entre parênteses (`dom`, `seg`, `ter`, `qua`, `qui`, `sex`, `sáb`).

#### Scenario: Árvore é montada a partir do cache
- **WHEN** a aba é exibida pela primeira vez e há anos no cache
- **THEN** a árvore SHALL mostrar os anos em ordem decrescente
- **THEN** cada ano SHALL ter apenas os meses com feriados, em ordem crescente
- **THEN** cada mês SHALL ter as folhas de dia em ordem crescente

#### Scenario: Folha mostra o dia da semana
- **WHEN** uma folha de dia é exibida
- **THEN** o rótulo SHALL ser `DD (abreviatura)`, como `03 (sex)`

#### Scenario: Construção sem rede
- **WHEN** a aba é construída pela primeira vez
- **THEN** ela SHALL ler apenas o cache do calendário
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Sem cache
- **WHEN** não há anos no cache
- **THEN** a árvore SHALL ficar vazia e o textbox SHALL orientar a usar o botão de atualização

### Requirement: Seleção na árvore atualiza o textbox

Ao selecionar um ano, o textbox SHALL listar todos os feriados do ano agrupados por mês. Ao selecionar um mês, SHALL listar os feriados do mês dia a dia. Ao selecionar um dia, SHALL mostrar apenas o feriado daquele dia. O textbox SHALL ser somente leitura e SHALL exibir o dia da semana ao lado do dia.

#### Scenario: Ano selecionado
- **WHEN** o usuário seleciona um ano
- **THEN** o textbox SHALL mostrar os feriados agrupados por mês
- **THEN** cada linha SHALL conter dia, dia da semana abreviado e nome do feriado

#### Scenario: Mês selecionado
- **WHEN** o usuário seleciona um mês
- **THEN** o textbox SHALL mostrar os feriados daquele mês, dia a dia
- **THEN** cada linha SHALL conter dia, dia da semana abreviado e nome do feriado

#### Scenario: Dia selecionado
- **WHEN** o usuário seleciona uma folha de dia
- **THEN** o textbox SHALL mostrar o feriado daquele dia com data, dia da semana abreviado e nome

#### Scenario: Textbox somente leitura
- **WHEN** o usuário tenta editar o textbox
- **THEN** a edição NÃO SHALL ser permitida

### Requirement: Atualização forçada na aba Feriados

A aba SHALL ter um botão de atualização com o mesmo ícone `view-refresh` das sub-abas do Tesouro Direto. Durante a carga, o ícone SHALL mudar para `content-loading` e o botão SHALL ficar desabilitado. O botão SHALL forçar a revalidação dos anos exibidos, ignorando o TTL, e SHALL preservar o cache anterior em caso de falha.

#### Scenario: Atualização bem-sucedida
- **WHEN** o usuário clica no botão de atualização
- **THEN** os anos exibidos SHALL ser revalidados na ANBIMA
- **THEN** a árvore SHALL ser reconstruída com os dados atualizados
- **THEN** a seleção anterior SHALL ser preservada quando ainda existir

#### Scenario: Árvore vazia atualiza o ano corrente
- **WHEN** o usuário clica no botão de atualização sem anos no cache
- **THEN** o ano corrente SHALL ser revalidado na ANBIMA
- **THEN** a árvore SHALL ser montada com os feriados obtidos

#### Scenario: Falha preserva o conteúdo
- **WHEN** a atualização falha
- **THEN** a árvore e o textbox SHALL manter o conteúdo anterior
- **THEN** a barra de status SHALL indicar a falha ou a defasagem

#### Scenario: Indicador de carga
- **WHEN** a atualização está em andamento
- **THEN** o botão SHALL usar o ícone `content-loading`
- **THEN** o botão SHALL ficar desabilitado até o fim da operação

#### Scenario: Seleção não acessa a rede
- **WHEN** o usuário navega entre anos, meses e dias
- **THEN** nenhuma requisição de rede SHALL ser iniciada
