# tesouro-analise Specification

## Purpose

Calcular percentuais normalizados de composição do estoque e de apetite do mercado do Tesouro Direto, com séries temporais e cache analítico, para apoiar a leitura de exposição a SELIC, IPCA, Prefixado e IGP-M.

## Requirements

### Requirement: Taxonomia de indexadores

O sistema SHALL classificar cada `tipo_titulo` em `SELIC`, `IPCA`, `PREFIXADO`, `IGP-M` ou `OUTROS`.

`Tesouro Reserva` SHALL ser `SELIC_RESERVA` e SHALL ser somado em `SELIC` no headline. `Tesouro IPCA+`, `Tesouro IPCA+ com Juros Semestrais`, `Tesouro RendA+` e `Tesouro Educa+` SHALL ser `IPCA`. Títulos desconhecidos SHALL ir para `OUTROS` com aviso, sem descarte silencioso.

#### Scenario: Selic e Reserva

- **WHEN** o título é `Tesouro Selic` ou `Tesouro Reserva`
- **THEN** a família SHALL ser `SELIC`
- **THEN** `Tesouro Reserva` SHALL ter subfamília `SELIC_RESERVA`
- **THEN** o headline SHALL somar Reserva em SELIC

#### Scenario: Famílias de inflação

- **WHEN** o título é `Tesouro IPCA+`, `Tesouro IPCA+ com Juros Semestrais`, `Tesouro RendA+` ou `Tesouro Educa+`
- **THEN** a família SHALL ser `IPCA`

#### Scenario: Prefixado e IGP-M

- **WHEN** o título é `Tesouro Prefixado` ou `Tesouro Prefixado com Juros Semestrais`
- **THEN** a família SHALL ser `PREFIXADO`
- **WHEN** o título é `Tesouro IGPM+ com Juros Semestrais`
- **THEN** a família SHALL ser `IGP-M`

#### Scenario: Título desconhecido

- **WHEN** um `tipo_titulo` não está no registry
- **THEN** a família SHALL ser `OUTROS`
- **THEN** o sistema SHALL registrar um aviso
- **THEN** o título NÃO SHALL ser descartado

### Requirement: Composição percentual do estoque

O sistema SHALL calcular, para um mês consolidado, o percentual de cada família e de cada título sobre o total de `valor_estoque`.

O percentual SHALL ser calculado por valor, não por quantidade. O mês SHALL ser o último disponível. O sistema NÃO SHALL somar `valor_estoque` entre meses.

#### Scenario: Percentual por família

- **WHEN** o estoque de um mês é analisado
- **THEN** cada família SHALL ter `valor_estoque` dividido pelo total do mês
- **THEN** a soma dos percentuais SHALL ser 100% (dentro do arredondamento)

#### Scenario: Percentual por título

- **WHEN** o detalhe por título é solicitado
- **THEN** cada `tipo_titulo` SHALL ter seu percentual sobre o total do mês

#### Scenario: Base é valor

- **WHEN** o percentual é calculado
- **THEN** ele SHALL usar `valor_estoque`
- **THEN** ele NÃO SHALL usar `quantidade` como base principal

#### Scenario: Sem soma entre meses

- **WHEN** mais de um mês está no intervalo
- **THEN** cada mês SHALL ser calculado isoladamente
- **THEN** os valores NÃO SHALL ser somados entre meses

#### Scenario: Total zero

- **WHEN** o total do mês é zero
- **THEN** o sistema SHALL levantar `TesouroDataError`
- **THEN** nenhum percentual SHALL ser produzido

### Requirement: Apetite percentual do mercado

O sistema SHALL calcular o percentual de vendas por família e por título sobre o total de vendas da janela.

As janelas SHALL ser 14 dias, 3 meses, 12 meses e 3 anos, relativas à maior data de liquidação disponível. A base SHALL ser `Valor` das vendas. O percentual SHALL ser rotulado com a janela usada.

#### Scenario: Janela de 14 dias

- **WHEN** a janela é 14 dias
- **THEN** o sistema SHALL somar as vendas dos últimos 14 dias até a maior data disponível
- **THEN** o percentual SHALL ser calculado sobre esse total

#### Scenario: Janelas maiores

- **WHEN** a janela é 3 meses, 12 meses ou 3 anos
- **THEN** o sistema SHALL usar o intervalo correspondente até a maior data disponível

#### Scenario: Percentual por família e por título

- **WHEN** o apetite é calculado
- **THEN** o resultado SHALL conter o percentual por família e por título
- **THEN** a soma dos percentuais SHALL ser 100% (dentro do arredondamento)

#### Scenario: Janela vazia

- **WHEN** não há vendas na janela
- **THEN** o resultado SHALL ser vazio
- **THEN** o sistema NÃO SHALL levantar erro de transporte

### Requirement: Fluxo líquido

O sistema SHALL calcular o fluxo líquido por família e por título como o valor de vendas menos o valor de recompras antecipadas na mesma janela.

Vencimentos e cupons NÃO SHALL compor o fluxo líquido. O fluxo líquido PODE ser negativo.

#### Scenario: Fluxo positivo

- **WHEN** as vendas superam as recompras
- **THEN** o fluxo líquido SHALL ser positivo

#### Scenario: Fluxo negativo

- **WHEN** as recompras superam as vendas
- **THEN** o fluxo líquido SHALL ser negativo

#### Scenario: Vencimentos e cupons fora

- **WHEN** o fluxo líquido é calculado
- **THEN** vencimentos e cupons NÃO SHALL ser subtraídos
- **THEN** apenas recompras antecipadas SHALL entrar no cálculo

### Requirement: Séries temporais normalizadas

O sistema SHALL produzir séries com período, dimensão, chave, métrica, valor e total.

As dimensões SHALL ser família, produto e produto+vencimento. As métricas SHALL incluir percentual de estoque, percentual de demanda e fluxo líquido. Os buckets SHALL ser diário, semanal e mensal. O sistema NÃO SHALL produzir períodos futuros.

#### Scenario: Bucket diário

- **WHEN** a janela é de 14 dias e a fonte é diária
- **THEN** a série SHALL usar buckets diários

#### Scenario: Bucket semanal

- **WHEN** a janela é de 3 meses e a fonte é diária
- **THEN** a série SHALL usar buckets semanais

#### Scenario: Bucket mensal

- **WHEN** a janela é de 12 meses ou 3 anos
- **THEN** a série SHALL usar buckets mensais
- **WHEN** a fonte é o estoque
- **THEN** a série SHALL ser sempre mensal

#### Scenario: Ciclo de vida do título

- **WHEN** um título aparece ou desaparece no período
- **THEN** a série SHALL representar ausência como zero ou lacuna explícita
- **THEN** o sistema NÃO SHALL inventar valores

#### Scenario: Sem projeção

- **WHEN** uma série é gerada
- **THEN** ela SHALL conter apenas períodos com dados observados
- **THEN** o sistema NÃO SHALL gerar períodos futuros

### Requirement: Cache analítico de 3 anos

O sistema SHALL manter o cache analítico em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/analytics/`, com retenção de 3 anos relativa ao `latest_data_date`.

A gravação SHALL ser atômica. O cache SHALL ser invalidado quando o `sha256` ou o `last_data_date` da fonte mudar. O housekeeping SHALL rodar após refresh bem-sucedido. Leitura somente leitura NÃO SHALL remover, renomear ou alterar arquivos.

#### Scenario: Escrita atômica

- **WHEN** uma partição analítica é gravada
- **THEN** um leitor concorrente SHALL ver a versão anterior ou a nova
- **THEN** o leitor NÃO SHALL ver conteúdo parcial

#### Scenario: Invalidação por fonte

- **WHEN** o hash ou a maior data da fonte muda
- **THEN** as partições afetadas SHALL ser recalculadas
- **THEN** as demais SHALL permanecer reutilizáveis

#### Scenario: Housekeeping de 3 anos

- **WHEN** o refresh conclui com sucesso
- **THEN** partições anteriores a `latest_data_date - 3 anos` SHALL ser removidas
- **THEN** o corte NÃO SHALL usar o relógio quando a fonte estiver atrasada

#### Scenario: Leitura somente leitura

- **WHEN** o cache analítico é lido em modo somente leitura
- **THEN** entradas ausentes, vencidas ou corrompidas SHALL ser tratadas como miss
- **THEN** nenhum arquivo SHALL ser removido, renomeado ou alterado

### Requirement: Política de atualização do cache bruto

O cache bruto SHALL permanecer cumulativo e completo, sem poda.

O TTL SHALL ser de 1 hora para vendas e recompras quando o cache contém o dia corrente ou o último dia útil; 6 horas para o histórico desses recursos; e 24 horas para estoque, cupom e vencimentos. Uma resposta `304` SHALL reutilizar o cache.

#### Scenario: Dado do dia corrente

- **WHEN** vendas ou recompras contêm o dia corrente
- **THEN** o cache SHALL expirar em 1 hora

#### Scenario: Dado histórico

- **WHEN** vendas ou recompras não contêm o dia corrente
- **THEN** o cache SHALL expirar em 6 horas
- **THEN** as linhas históricas NÃO SHALL ser recarregadas

#### Scenario: Recurso mensal ou eventual

- **WHEN** o recurso é estoque, cupom ou vencimentos
- **THEN** o cache SHALL expirar em 24 horas

#### Scenario: 304 reutiliza

- **WHEN** o servidor responde `304 Not Modified`
- **THEN** o CSV SHALL ser reutilizado
- **THEN** apenas o `checked_at` SHALL ser atualizado

### Requirement: Health check da fonte de estoque

O sistema SHALL validar a fonte de estoque antes de usá-la: `success`, recurso CSV, cabeçalho esperado e mês consolidado.

Se o dataset, o recurso ou o cabeçalho estiverem ausentes ou incompatíveis, o sistema SHALL levantar `TesouroDataError` e NÃO SHALL usar fonte alternativa ou scraping. Se o mês mais recente estiver mais de 3 meses atrás do mês corrente, o sistema SHALL registrar aviso.

#### Scenario: Fonte saudável

- **WHEN** o dataset, o CSV e o cabeçalho estão corretos
- **THEN** o sistema SHALL usar o CSV de estoque

#### Scenario: Fonte ausente

- **WHEN** o dataset ou o recurso CSV não existe
- **THEN** o sistema SHALL levantar `TesouroDataError`
- **THEN** nenhum fallback SHALL ser usado

#### Scenario: Schema alterado

- **WHEN** o cabeçalho não corresponde ao esperado
- **THEN** o sistema SHALL levantar `TesouroDataError`
- **THEN** nenhum dado parcial SHALL ser analisado

#### Scenario: Defasagem mensal

- **WHEN** o mês mais recente está mais de 3 meses atrás
- **THEN** o sistema SHALL registrar aviso
- **THEN** o dado SHALL ser tratado como o último disponível

### Requirement: Contrato headless de séries

O processamento, a taxonomia, os percentuais, o fluxo líquido e as séries SHALL residir em `application` e NÃO SHALL importar `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede.

O contrato de séries SHALL ser genérico o suficiente para que a futura change de câmbio adicione séries sem alterar o cálculo do Tesouro.

#### Scenario: Processamento sem display

- **WHEN** um teste exercita a análise
- **THEN** ele SHALL importar apenas módulos de `application` e `domain`
- **THEN** nenhuma janela ou figura SHALL ser criada

#### Scenario: Extensão para câmbio

- **WHEN** uma nova série macro é adicionada
- **THEN** ela SHALL implementar o mesmo contrato de série
- **THEN** o cálculo de composição do Tesouro NÃO SHALL ser alterado

### Requirement: Classificação de erros

O sistema SHALL usar `CommunicationError` para falhas de rede, HTTP, timeout ou corpo parcial e `TesouroDataError` para falha de schema, taxonomia, fonte ausente ou total inválido.

Falhas esperadas SHALL ser registradas em uma linha, sem traceback. Exceções inesperadas SHALL ser registradas com traceback.

#### Scenario: Falha de comunicação

- **WHEN** o download falha por rede ou HTTP
- **THEN** o erro SHALL ser `CommunicationError`
- **THEN** a mensagem de log SHALL ocupar uma única linha

#### Scenario: Falha de dados

- **WHEN** o schema, a taxonomia ou o total é inválido
- **THEN** o erro SHALL ser `TesouroDataError`
- **THEN** o erro NÃO SHALL ser classificado como comunicação
