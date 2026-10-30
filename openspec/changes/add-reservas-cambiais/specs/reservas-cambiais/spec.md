# Spec Delta

## Purpose

Oferecer a evolução do estoque de reservas internacionais brasileiras em dólares, com cache local rápido e um sinal determinístico de aumento ou deterioração.

## ADDED Requirements

### Requirement: Série histórica de reservas

O sistema SHALL disponibilizar a série diária das reservas internacionais brasileiras em dólares, obtida da série oficial BCB SGS 13621 (conceito de liquidez), com janela padrão de 12 meses e opção de 3 anos.

Cada ponto SHALL conter data, valor em US$ milhões, unidade, origem, método e horário de extração.

#### Scenario: Série disponível

- **WHEN** o cache contém a série de reservas
- **THEN** a resposta SHALL cobrir a janela solicitada
- **THEN** cada ponto SHALL conter data, valor em US$ milhões e unidade

#### Scenario: Janela de três anos

- **WHEN** o usuário seleciona a janela de 3 anos
- **THEN** a série SHALL cobrir até 36 meses anteriores à maior data disponível

#### Scenario: Proveniência do ponto

- **WHEN** um ponto é emitido
- **THEN** ele SHALL conter origem `BCB SGS 13621`, método, unidade e horário de extração

#### Scenario: Sem dados em cache

- **WHEN** não há série em cache
- **THEN** o sistema SHALL informar ausência de dados e orientar a atualização
- **THEN** nenhuma chamada de rede SHALL ser iniciada automaticamente

### Requirement: Cache bruto e TTL por recência

O sistema SHALL persistir um snapshot normalizado da série bruta por fonte, com metadados de esquema, fonte, unidade, hash canônico e horário de extração.

O TTL SHALL ser de 15 a 30 minutos para o último dia útil, de 1 a 6 horas para o mês corrente e imutável para datas históricas com mais de um mês.

#### Scenario: Cache recente expira

- **WHEN** o último dia útil está em cache além do TTL curto
- **THEN** o sistema SHALL revalidar ou buscar a fonte antes de usar o valor

#### Scenario: Histórico imutável

- **WHEN** a data em cache tem mais de um mês
- **THEN** o sistema SHALL tratá-la como válida independentemente da idade

#### Scenario: Leitura somente de cache

- **WHEN** a operação é somente leitura
- **THEN** o sistema NÃO SHALL criar, alterar ou remover arquivos de cache

### Requirement: Busca incremental com revisões

O sistema SHALL buscar apenas o período ausente a partir da última data em cache, com uma sobreposição configurável de dias úteis para capturar revisões de valores recentes.

A atualização forçada SHALL recarregar a janela retida mesmo que o cache esteja válido.

#### Scenario: Busca a partir da última data

- **WHEN** o cache termina em uma data e a fonte aceita intervalo
- **THEN** o sistema SHALL solicitar apenas as datas posteriores, com a sobreposição configurada

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

### Requirement: Pré-cálculo invalidado por hash

O sistema SHALL executar o pré-cálculo após o `Atualizar` somente quando o hash canônico dos pares `(data, valor)` ou os parâmetros de cálculo mudarem.

A gravação SHALL ser atômica e protegida por lock, e a falha SHALL preservar o artefato anterior.

#### Scenario: Matriz inalterada

- **WHEN** o hash canônico é igual ao gravado
- **THEN** o pré-cálculo NÃO SHALL ser executado novamente

#### Scenario: Matriz alterada

- **WHEN** um valor, uma data ou um parâmetro muda
- **THEN** o pré-cálculo SHALL ser executado
- **THEN** o novo artefato SHALL ser gravado com o novo hash

#### Scenario: Execução concorrente

- **WHEN** duas atualizações tentam pré-calcular ao mesmo tempo
- **THEN** o lock SHALL serializar a execução
- **THEN** apenas um artefato consistente SHALL ficar visível

#### Scenario: Falha no pré-cálculo

- **WHEN** o pré-cálculo falha
- **THEN** o artefato anterior SHALL permanecer válido
- **THEN** a falha SHALL ser registrada sem interromper a atualização principal

### Requirement: Housekeeping de três anos

O sistema SHALL remover do cache de reservas os dados anteriores a três anos, contados a partir da maior data disponível, sem interromper a limpeza por arquivo corrompido.

O hash do pré-cálculo SHALL considerar apenas a janela retida, para que a remoção de dados expirados não invalide o artefato.

#### Scenario: Dado antigo removido

- **WHEN** um dado tem mais de três anos em relação à maior data disponível
- **THEN** ele SHALL ser removido do cache

#### Scenario: Dado dentro da retenção

- **WHEN** um dado tem três anos ou menos
- **THEN** ele SHALL ser preservado

#### Scenario: Referência é a maior data

- **WHEN** o housekeeping é executado
- **THEN** o corte SHALL usar a maior data disponível, não o relógio local

#### Scenario: Limpeza não invalida o pré-cálculo

- **WHEN** apenas dados fora da janela retida são removidos
- **THEN** o hash canônico SHALL permanecer igual
- **THEN** o pré-cálculo NÃO SHALL ser executado novamente

#### Scenario: Arquivo corrompido

- **WHEN** um arquivo não segue o padrão de data ou está corrompido
- **THEN** ele SHALL ser ignorado sem interromper a limpeza

### Requirement: Indicadores de deterioração

O sistema SHALL calcular nível atual, variações de 1, 3 e 12 meses, tendência de 90 dias, drawdown de 12 meses e posição na faixa de 12 meses.

O sistema SHALL classificar o regime como `aumento`, `estavel` ou `deterioracao` por regra determinística com limiares configuráveis.

#### Scenario: Regime de aumento

- **WHEN** a variação de 3 meses é positiva acima do limiar e o nível está acima da média de 90 dias
- **THEN** o regime SHALL ser `aumento`

#### Scenario: Regime de deterioração

- **WHEN** a variação de 3 meses é negativa abaixo do limiar e o drawdown de 12 meses cruza o limiar
- **THEN** o regime SHALL ser `deterioracao`

#### Scenario: Regime estável

- **WHEN** nenhum limiar de aumento ou deterioração é atingido
- **THEN** o regime SHALL ser `estavel`

#### Scenario: Histórico insuficiente

- **WHEN** não há histórico suficiente para uma métrica
- **THEN** apenas essa métrica SHALL ser omitida
- **THEN** as demais SHALL continuar disponíveis

#### Scenario: Determinismo

- **WHEN** os indicadores são recalculados com os mesmos dados e parâmetros
- **THEN** o resultado SHALL ser idêntico

### Requirement: Visualização da evolução

A sub-aba `Reservas Internacionais` SHALL exibir a série em gráfico de linha, com janela de 12 meses ou 3 anos, médias móveis, selo de regime e aviso de defasagem.

O gráfico NÃO SHALL acessar a rede na construção e SHALL orientar a atualização quando não houver dados.

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

- **WHEN** o último dado está fora do TTL esperado
- **THEN** o gráfico SHALL exibir um aviso de defasagem

#### Scenario: Estado vazio

- **WHEN** não há dados
- **THEN** o gráfico SHALL exibir uma mensagem orientando a atualização

### Requirement: Atualização e estado da sub-aba

A sub-aba `Reservas Internacionais` SHALL carregar apenas o cache na primeira exibição e NÃO SHALL acessar a rede ao ser construída.

O `Atualizar` próprio SHALL buscar a série, gravar o cache bruto e disparar o pré-cálculo, preservando o estado ao alternar de sub-aba.

#### Scenario: Primeira exibição

- **WHEN** a sub-aba fica visível pela primeira vez
- **THEN** ela SHALL ler apenas o cache local
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Atualização

- **WHEN** o usuário clica em `Atualizar`
- **THEN** o sistema SHALL buscar a série de reservas
- **THEN** o pré-cálculo SHALL ser disparado após a atualização

#### Scenario: Estado preservado

- **WHEN** o usuário alterna para outra sub-aba e retorna
- **THEN** a janela e o estado anterior SHALL ser preservados

### Requirement: Exportação e payloads

O sistema SHALL expor a série e os indicadores em CSV e JSON, com proveniência e aviso de que o regime é um sinal direcional, não uma recomendação.

O CSV de série SHALL usar delimitador `;` e datas ISO; o JSON SHALL conter janela, série, indicadores, origem e `gerado_em`.

#### Scenario: CSV de série

- **WHEN** a exportação CSV é solicitada
- **THEN** a saída SHALL conter delimitador `;`, datas ISO e valor em US$ milhões

#### Scenario: JSON estruturado

- **WHEN** a exportação JSON é solicitada
- **THEN** a saída SHALL conter janela, série, indicadores, origem e `gerado_em`

#### Scenario: Sem dados

- **WHEN** não há dados para a janela
- **THEN** a exportação SHALL falhar com mensagem que oriente a atualização

#### Scenario: Aviso de sinal

- **WHEN** o regime é exportado
- **THEN** o payload SHALL informar que se trata de sinal direcional, não de recomendação
