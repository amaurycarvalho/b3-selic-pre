# cambio-ouro Specification

## Purpose
Oferecer histórico e cenário de 12 meses para dólar e ouro, com proveniência por ponto e sinais que ajudem a detectar mudanças na política cambial.

## Requirements

### Requirement: Série histórica de 12 meses

O sistema SHALL disponibilizar séries diárias dos últimos 12 meses para dólar em BRL/USD e ouro em R$/g, alinhadas por data e com proveniência em cada série.

Cada item SHALL conter data, valor, unidade, origem, método e horário de extração. Datas sem cotação em uma fonte SHALL ser omitidas ou preenchidas apenas com o último valor válido, com a defasagem indicada.

#### Scenario: Histórico disponível

- **WHEN** o cache contém dados dos últimos 12 meses
- **THEN** a série SHALL cobrir a janela de 12 meses
- **THEN** cada item SHALL conter data, valor e unidade

#### Scenario: Alinhamento por data

- **WHEN** dólar e ouro têm datas de cotação diferentes
- **THEN** cada ponto SHALL preservar sua própria data
- **THEN** nenhuma interpolação silenciosa SHALL ocorrer

#### Scenario: Proveniência do ponto

- **WHEN** um ponto é emitido
- **THEN** ele SHALL conter origem, método, unidade e horário de extração

#### Scenario: Sem dados em cache

- **WHEN** não há série em cache para a janela
- **THEN** o sistema SHALL informar ausência de dados e orientar a atualização
- **THEN** nenhuma chamada de rede SHALL ser iniciada automaticamente

### Requirement: Resolução temporal em camadas

A série histórica SHALL usar resolução diária nos últimos 14 dias, semanal entre 15 dias e 3 meses e mensal acima de 3 meses, contados a partir da maior data disponível.

Cada bucket SHALL preservar o mínimo, o máximo e o último valor do período. A mudança de resolução NÃO SHALL alterar o eixo temporal do gráfico.

#### Scenario: Zona diária

- **WHEN** a data está nos últimos 14 dias
- **THEN** a série SHALL ter um ponto por dia útil

#### Scenario: Zona semanal

- **WHEN** a data está entre 15 dias e 3 meses atrás
- **THEN** a série SHALL ter um ponto por semana

#### Scenario: Zona mensal

- **WHEN** a data está além de 3 meses
- **THEN** a série SHALL ter um ponto por mês

#### Scenario: Extremos preservados

- **WHEN** um bucket semanal ou mensal é formado
- **THEN** o mínimo e o máximo do período SHALL ser preservados
- **THEN** o último valor do período SHALL ser identificado

#### Scenario: Sem amostragem temporal Fibonacci

- **WHEN** a resolução da série é calculada
- **THEN** o sistema NÃO SHALL usar intervalos de Fibonacci para amostrar datas
- **THEN** Fibonacci SHALL ser usado apenas como overlay de níveis de preço

### Requirement: Derivação do ouro em R$/g

O ouro SHALL ser obtido em R$/g pela fórmula `XAU/USD x USD/BRL / 31,1034768`, usando XAU/USD de fonte de mercado e USD/BRL da série oficial do BCB.

O método SHALL ser registrado como `derivado`. A awesomeapi NÃO SHALL ser usada. Quando a fonte de XAU/USD falhar, o sistema SHALL reutilizar o último valor válido em cache, marcado como `cache_defasado`.

#### Scenario: Derivação do ouro

- **WHEN** há XAU/USD e USD/BRL disponíveis
- **THEN** o valor do ouro SHALL ser calculado em R$/g
- **THEN** a origem SHALL registrar a derivação e as fontes usadas

#### Scenario: Conversão de unidade

- **WHEN** XAU/USD está em dólares por onça troy
- **THEN** o sistema SHALL dividir por 31,1034768 para obter R$/g

#### Scenario: Fallback para cache

- **WHEN** a fonte de XAU/USD falha
- **THEN** o sistema SHALL usar o último valor válido em cache
- **THEN** o ponto SHALL ser marcado como `cache_defasado`

#### Scenario: Sem fallback de rede

- **WHEN** a fonte primária de ouro falha e não há valor em cache
- **THEN** o sistema NÃO SHALL consultar outro agregador de terceiros
- **THEN** o sistema SHALL informar indisponibilidade do ouro

#### Scenario: B3 sem ouro oficial

- **WHEN** a B3 não oferece preço oficial de ouro para a data
- **THEN** o sistema SHALL usar a derivação
- **THEN** a origem NÃO SHALL afirmar que o dado é oficial da B3

### Requirement: Cenário de 12 meses do dólar

O cenário central do dólar SHALL ser ancorado na mediana anual do Focus para 12 meses, interpolada entre os anos de referência.

O curto prazo PODE ser ajustado pelo prêmio implícito dos futuros DOL com liquidez. O sistema SHALL exibir bandas de 80% e 95% e rotular o resultado como cenário de mercado.

#### Scenario: Ancoragem no Focus

- **WHEN** há expectativa Focus para 12 meses
- **THEN** o cenário central SHALL usar a mediana Focus interpolada

#### Scenario: Sinal de curto prazo

- **WHEN** há futuros DOL líquidos
- **THEN** o sistema SHALL calcular o prêmio implícito de curto prazo
- **THEN** o sinal PODE ajustar a parte inicial do cenário

#### Scenario: Bandas de incerteza

- **WHEN** o cenário do dólar é exibido
- **THEN** ele SHALL conter bandas de 80% e 95%
- **THEN** as bandas SHALL ser identificadas como incerteza, não como garantia

#### Scenario: Focus ausente

- **WHEN** não há expectativa Focus disponível
- **THEN** o sistema NÃO SHALL inventar um cenário de mercado
- **THEN** o sistema SHALL usar projeção estatística e rotulá-la como tal

### Requirement: Cenário estatístico de 12 meses do ouro

O cenário do ouro SHALL usar random walk com drift encolhido e volatilidade EWMA sobre retornos logarítmicos, com bandas de 80% e 95%.

O sistema SHALL rotular o resultado como projeção estatística, não como expectativa de mercado.

#### Scenario: Projeção do ouro

- **WHEN** há histórico suficiente de ouro
- **THEN** o sistema SHALL gerar um ponto por mês para os próximos 12 meses

#### Scenario: Bandas crescentes

- **WHEN** o horizonte aumenta
- **THEN** a largura das bandas SHALL aumentar ou permanecer igual

#### Scenario: Histórico insuficiente

- **WHEN** o histórico é menor que o mínimo necessário
- **THEN** o sistema NÃO SHALL gerar o cenário
- **THEN** o sistema SHALL informar a insuficiência de dados

#### Scenario: Determinismo

- **WHEN** a projeção é recalculada com os mesmos dados e parâmetros
- **THEN** o resultado SHALL ser idêntico

### Requirement: Sinais de política cambial

O sistema SHALL calcular e exibir o prêmio a termo Focus 12 meses versus spot, o prêmio implícito DOL curto versus spot, o gap Focus versus spot, a volatilidade realizada de 30 e 90 dias e um indicador de regime.

O indicador de regime SHALL ser determinístico e ligado quando a razão de volatilidade e o sinal do drift atenderem ao limiar documentado.

#### Scenario: Prêmio a termo

- **WHEN** há cenário Focus e spot
- **THEN** o sistema SHALL calcular o prêmio a termo anualizado

#### Scenario: Prêmio implícito DOL

- **WHEN** há futuro DOL líquido e spot
- **THEN** o sistema SHALL calcular o prêmio implícito de curto prazo

#### Scenario: Gap Focus

- **WHEN** há Focus e spot
- **THEN** o sistema SHALL calcular a diferença entre a expectativa e o spot

#### Scenario: Volatilidade realizada

- **WHEN** há histórico suficiente
- **THEN** o sistema SHALL calcular a volatilidade realizada de 30 e 90 dias

#### Scenario: Indicador de regime

- **WHEN** a razão de volatilidade e o drift cruzam o limiar configurado
- **THEN** o indicador de regime SHALL ser ligado
- **THEN** o limiar usado SHALL ser identificável na saída

#### Scenario: Entrada ausente

- **WHEN** um dos insumos do sinal não está disponível
- **THEN** o sinal correspondente SHALL ser omitido
- **THEN** os demais sinais SHALL continuar disponíveis

### Requirement: Visualização em dois painéis

A sub-aba `Dólar e Ouro` SHALL exibir dólar e ouro em dois subgráficos empilhados com eixo x compartilhado, divisor vertical na data atual, região futura sombreada e cenário tracejado.

A sub-aba SHALL oferecer alternância entre valores absolutos e base 100. O overlay de retração de Fibonacci PODE ser exibido sobre o range de 12 meses.

#### Scenario: Painéis empilhados

- **WHEN** a sub-aba é exibida com dados
- **THEN** o dólar SHALL ocupar o painel superior
- **THEN** o ouro SHALL ocupar o painel inferior
- **THEN** os dois painéis SHALL compartilhar o eixo x

#### Scenario: Base 100

- **WHEN** o usuário alterna para base 100
- **THEN** as duas séries SHALL ser reindexadas para 100 na data inicial da janela

#### Scenario: Região futura

- **WHEN** o cenário de 12 meses é exibido
- **THEN** a região posterior à data atual SHALL ser sombreada
- **THEN** o cenário SHALL ser desenhado com linha tracejada

#### Scenario: Overlay Fibonacci

- **WHEN** o usuário ativa o overlay de Fibonacci
- **THEN** os níveis de retração SHALL ser desenhados sobre o range de 12 meses
- **THEN** o overlay NÃO SHALL substituir a série histórica

#### Scenario: Estado vazio

- **WHEN** não há dados
- **THEN** o gráfico SHALL exibir uma mensagem orientando a atualização

#### Scenario: Dado defasado

- **WHEN** algum ponto usa `cache_defasado`
- **THEN** o gráfico SHALL exibir um aviso de defasagem

### Requirement: Legenda e hover dos painéis

A legenda SHALL ficar centralizada abaixo dos painéis. O gráfico SHALL oferecer hover com data, ativo, valor, unidade e faixa mín-máx do histórico; nos pontos de cenário, o hover SHALL incluir o valor central e as bandas de 80% e 95%.

#### Scenario: Legenda abaixo dos painéis

- **WHEN** o gráfico é exibido com dados
- **THEN** a legenda SHALL ficar centralizada abaixo dos painéis
- **THEN** a legenda NÃO SHALL sobrepor a área dos gráficos

#### Scenario: Hover nos dados históricos

- **WHEN** o ponteiro fica próximo de um ponto histórico
- **THEN** o tooltip SHALL exibir data, ativo, valor, unidade e faixa mín-máx

#### Scenario: Hover no cenário

- **WHEN** o ponteiro fica próximo de um ponto do cenário
- **THEN** o tooltip SHALL exibir o valor central e as bandas de 80% e 95%

### Requirement: Atualização e estado da sub-aba

A sub-aba `Dólar e Ouro` SHALL carregar apenas o cache na primeira exibição e NÃO SHALL acessar a rede ao ser construída.

O botão `Atualizar` SHALL buscar as fontes da sub-aba, gravar o cache bruto e disparar o pré-cálculo. A barra de status SHALL exibir origem, horário de extração e indicação de dados defasados.

#### Scenario: Primeira exibição

- **WHEN** a sub-aba fica visível pela primeira vez
- **THEN** ela SHALL ler apenas o cache local
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Atualização

- **WHEN** o usuário clica em `Atualizar` na sub-aba
- **THEN** o sistema SHALL buscar as fontes de mercado da sub-aba
- **THEN** o pré-cálculo SHALL ser disparado após a atualização

#### Scenario: Falha parcial

- **WHEN** uma fonte falha e outra responde
- **THEN** a sub-aba SHALL exibir os dados disponíveis
- **THEN** a fonte com falha SHALL ser identificada no status

#### Scenario: Dado defasado no status

- **WHEN** o dado exibido é `cache_defasado`
- **THEN** a barra de status SHALL indicar a defasagem

### Requirement: Cenário não é recomendação

Toda projeção exibida ou exportada SHALL ser identificada como cenário ou projeção estatística. O sistema NÃO SHALL apresentar projeções como recomendação de investimento.

#### Scenario: Rótulo na tela

- **WHEN** uma projeção é exibida
- **THEN** o rótulo SHALL indicar que se trata de cenário ou projeção estatística

#### Scenario: Rótulo na exportação

- **WHEN** uma projeção é exportada pela CLI ou pelo MCP
- **THEN** o payload SHALL conter o tipo de projeção e o aviso de que não é recomendação
