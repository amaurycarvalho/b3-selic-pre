# Spec Delta

## MODIFIED Requirements

### Requirement: Cache bruto e TTL por recência

O sistema SHALL persistir um snapshot normalizado da série bruta por fonte, com metadados de esquema, fonte, unidade, hash canônico e horário de extração.

O TTL SHALL ser de 15 a 30 minutos para o último dia útil, de 1 a 6 horas para o mês corrente e imutável para datas históricas com mais de um mês. O "último dia útil" SHALL considerar fins de semana e feriados.

#### Scenario: Cache recente expira

- **WHEN** o último dia útil está em cache além do TTL curto
- **THEN** o sistema SHALL revalidar ou buscar a fonte antes de usar o valor

#### Scenario: Feriado não reinicia o TTL

- **WHEN** a data corrente é feriado e o último dado em cache é do dia útil anterior
- **THEN** o snapshot SHALL ser considerado corrente
- **THEN** o feriado NÃO SHALL forçar uma revalidação

#### Scenario: Histórico imutável

- **WHEN** a data em cache tem mais de um mês
- **THEN** o sistema SHALL tratá-la como válida independentemente da idade

#### Scenario: Leitura somente de cache

- **WHEN** a operação é somente leitura
- **THEN** o sistema NÃO SHALL criar, alterar ou remover arquivos de cache

### Requirement: Busca incremental com revisões

O sistema SHALL buscar apenas o período ausente a partir da última data em cache, com uma sobreposição configurável de dias úteis para capturar revisões de valores recentes. A contagem da sobreposição SHALL usar o calendário de dias úteis.

A atualização forçada SHALL recarregar a janela retida mesmo que o cache esteja válido.

#### Scenario: Busca a partir da última data

- **WHEN** o cache termina em uma data e a fonte aceita intervalo
- **THEN** o sistema SHALL solicitar apenas as datas posteriores, com a sobreposição configurada

#### Scenario: Sobreposição atravessa feriado

- **WHEN** a sobreposição de 5 dias úteis encontra um feriado
- **THEN** o sistema SHALL recuar até completar 5 dias úteis
- **THEN** NÃO SHALL contar o feriado como dia útil

#### Scenario: Revisão de valor recente

- **WHEN** a fonte revisa o valor de um dia dentro da sobreposição
- **THEN** o snapshot SHALL refletir o valor revisado

#### Scenario: Atualização forçada

- **WHEN** o usuário solicita ignorar o cache
- **THEN** o sistema SHALL consultar a fonte para a janela retida

#### Scenario: Falha de rede

- **WHEN** a fonte falha durante a atualização
- **THEN** o snapshot anterior SHALL permanecer válido
- **THEN** a falha SHALL ser identificada no status

### Requirement: Visualização da evolução

A sub-aba `Reservas Internacionais` SHALL exibir a série em gráfico de linha, com janela de 12 meses ou 3 anos, médias móveis, selo de regime e aviso de defasagem.

O gráfico NÃO SHALL acessar a rede na construção e SHALL orientar a atualização quando não houver dados. O aviso de defasagem SHALL comparar a maior data disponível com o último dia útil esperado.

#### Scenario: Janela de 12 meses

- **WHEN** a sub-aba é exibida com a janela padrão
- **THEN** o gráfico SHALL cobrir os 12 meses anteriores à maior data disponível

#### Scenario: Janela de 3 anos

- **WHEN** o usuário seleciona a janela de 3 anos
- **THEN** o gráfico SHALL cobrir até 36 meses anteriores à maior data disponível

#### Scenario: Selo de regime

- **WHEN** os indicadores estão disponíveis
- **THEN** o gráfico SHALL exibir o regime e os limiares usados

#### Scenario: Dado defasado

- **WHEN** a maior data disponível é anterior ao último dia útil esperado
- **THEN** o gráfico SHALL exibir um aviso de defasagem

#### Scenario: Feriado não gera aviso

- **WHEN** a maior data disponível é o dia útil anterior a um feriado
- **THEN** o gráfico NÃO SHALL exibir aviso de defasagem

#### Scenario: Estado vazio

- **WHEN** não há dados
- **THEN** o gráfico SHALL exibir uma mensagem orientando a atualização
