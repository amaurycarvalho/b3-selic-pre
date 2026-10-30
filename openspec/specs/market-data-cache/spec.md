# market-data-cache Specification

## Purpose
Persistir dados brutos e derivados de mercado com TTL por recência, pré-cálculo invalidado por hash e retenção de três anos.

## Requirements

### Requirement: Cache bruto por fonte e data

O sistema SHALL armazenar o payload bruto de cada fonte de mercado por data ou como snapshot normalizado por fonte, com metadados de esquema, fonte, unidade, hash canônico e horário de extração.

O TTL SHALL variar por recência: 15 a 30 minutos para os últimos 14 dias, 1 a 6 horas para o mês corrente e imutável para datas históricas com mais de um mês. O "último dia útil" usado na recência SHALL considerar fins de semana e feriados.

#### Scenario: Cache recente expira

- **WHEN** um dado dos últimos 14 dias está em cache além do TTL curto
- **THEN** o sistema SHALL revalidar ou buscar novamente a fonte

#### Scenario: Feriado não reinicia o TTL

- **WHEN** a data corrente é feriado e o último dado em cache é do dia útil anterior
- **THEN** o cache SHALL ser considerado corrente e usar o TTL curto
- **THEN** o feriado NÃO SHALL forçar uma revalidação

#### Scenario: Histórico é imutável

- **WHEN** a data em cache tem mais de um mês
- **THEN** o sistema SHALL tratá-la como válida independentemente da idade

#### Scenario: Metadados de origem

- **WHEN** um payload bruto é gravado
- **THEN** ele SHALL conter fonte, unidade, hash canônico, esquema e horário de extração

#### Scenario: Snapshot normalizado

- **WHEN** a fonte retorna uma série em bloco
- **THEN** o sistema PODE gravá-la como um snapshot normalizado por fonte
- **THEN** o hash SHALL ser calculado sobre os pares `(data, valor)`, não sobre os bytes do arquivo

#### Scenario: Cache ausente

- **WHEN** não há entrada para a data solicitada
- **THEN** o sistema SHALL buscar a fonte quando a operação permitir rede
- **THEN** uma leitura somente de cache SHALL informar ausência de dados

### Requirement: Busca incremental

O sistema SHALL buscar apenas o período ausente a partir da última data em cache, quando a fonte suportar intervalo.

A busca SHALL incluir uma sobreposição configurável de dias úteis para capturar revisões de valores recentes. A busca completa SHALL ocorrer apenas em atualização forçada, mudança de esquema ou lacuna de cobertura detectada.

#### Scenario: Busca a partir da última data

- **WHEN** o cache termina em uma data e a fonte aceita intervalo
- **THEN** o sistema SHALL solicitar somente as datas posteriores, com a sobreposição configurada

#### Scenario: Revisão de valor recente

- **WHEN** a fonte revisa o valor de um dia dentro da sobreposição
- **THEN** o snapshot SHALL refletir o valor revisado

#### Scenario: Lacuna de cobertura

- **WHEN** o cache não cobre o início da janela solicitada
- **THEN** o sistema SHALL buscar a lacuna
- **THEN** a lacuna SHALL ser registrada no status

#### Scenario: Atualização forçada

- **WHEN** o usuário solicita ignorar o cache
- **THEN** o sistema SHALL consultar a fonte mesmo que o cache esteja válido

### Requirement: Cache derivado por buckets

O sistema SHALL armazenar a série derivada por buckets, os indicadores e o cenário em cache separado do payload bruto.

A chave do cache derivado SHALL combinar o hash das fontes, os parâmetros de resolução, os parâmetros de projeção e a versão do esquema.

#### Scenario: Reutilização do derivado

- **WHEN** os hashes das fontes e os parâmetros não mudaram
- **THEN** o sistema SHALL reutilizar o derivado em cache

#### Scenario: Parâmetro alterado

- **WHEN** a resolução ou um parâmetro de projeção muda
- **THEN** o sistema SHALL tratar o derivado como ausente
- **THEN** um novo derivado SHALL ser calculado

#### Scenario: Versão de esquema alterada

- **WHEN** a versão do esquema do cache muda
- **THEN** os derivados antigos NÃO SHALL ser reutilizados

### Requirement: Pré-cálculo invalidado por hash

O sistema SHALL executar o pré-cálculo após a atualização somente quando o hash canônico da matriz de origem ou os parâmetros de cálculo forem diferentes do hash gravado.

Para fontes com retenção, o hash SHALL considerar apenas a janela retida. A gravação do pré-cálculo SHALL ser atômica e protegida por lock, sem deixar artefato parcial visível.

#### Scenario: Matriz inalterada

- **WHEN** o hash canônico é igual ao gravado
- **THEN** o pré-cálculo NÃO SHALL ser executado novamente

#### Scenario: Matriz alterada

- **WHEN** qualquer fonte da matriz muda
- **THEN** o pré-cálculo SHALL ser executado
- **THEN** o novo hash SHALL ser gravado com o artefato

#### Scenario: Limpeza fora da janela

- **WHEN** apenas dados fora da janela retida são removidos
- **THEN** o hash canônico SHALL permanecer igual
- **THEN** o pré-cálculo NÃO SHALL ser executado novamente

#### Scenario: Execução concorrente

- **WHEN** duas atualizações tentam pré-calcular ao mesmo tempo
- **THEN** o lock SHALL serializar a execução
- **THEN** apenas um artefato consistente SHALL ficar visível

#### Scenario: Falha no pré-cálculo

- **WHEN** o pré-cálculo falha
- **THEN** o artefato anterior SHALL permanecer válido
- **THEN** a falha SHALL ser registrada sem interromper a atualização principal

### Requirement: Housekeeping de três anos

O sistema SHALL remover do cache de mercado os dados brutos e derivados anteriores a três anos, contados a partir da maior data disponível.

O hash do pré-cálculo SHALL considerar apenas a janela retida, para que a remoção de dados expirados não invalide o artefato. Arquivos corrompidos ou fora do padrão de data NÃO SHALL interromper o housekeeping.

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

#### Scenario: Arquivo corrompido

- **WHEN** um arquivo não segue o padrão de data ou está corrompido
- **THEN** ele SHALL ser ignorado sem interromper a limpeza

### Requirement: Proveniência e defasagem

O sistema SHALL persistir a origem, o método e o horário de extração de cada série e de cada ponto que possa ser exibido.

Quando um ponto reutiliza valor antigo por falha de fonte, o sistema SHALL marcá-lo como `cache_defasado` e expor a idade do dado.

#### Scenario: Ponto derivado

- **WHEN** o ouro é calculado a partir de XAU/USD e USD/BRL
- **THEN** o método SHALL ser registrado como `derivado`
- **THEN** as fontes de entrada SHALL ser registradas

#### Scenario: Ponto defasado

- **WHEN** o último valor válido é reutilizado
- **THEN** o ponto SHALL ser marcado como `cache_defasado`
- **THEN** a idade do dado SHALL estar disponível

### Requirement: Integridade do cache

O sistema SHALL gravar entradas de cache de forma atômica e NÃO SHALL persistir resultados vazios ou parciais.

Uma leitura somente de cache NÃO SHALL remover, corrigir ou criar arquivos.

#### Scenario: Escrita atômica

- **WHEN** uma entrada é gravada
- **THEN** nenhum arquivo parcial SHALL ficar visível para leitores concorrentes

#### Scenario: Resultado vazio

- **WHEN** a fonte retorna resultado vazio ou incompleto
- **THEN** o cache NÃO SHALL ser atualizado

#### Scenario: Entrada corrompida

- **WHEN** uma entrada de cache está corrompida
- **THEN** o sistema SHALL descartá-la ao gravar novamente

#### Scenario: Leitura somente de cache

- **WHEN** a operação é somente leitura
- **THEN** o sistema NÃO SHALL modificar o diretório de cache

### Requirement: Data esperada do artefato de mercado

O sistema SHALL comparar a maior data disponível do artefato de mercado com o último dia útil esperado, calculado pelo calendário. A ausência de dado em fim de semana ou feriado NÃO SHALL ser tratada como defasagem. Sem calendário para o ano, aplica-se apenas a regra de fim de semana.

#### Scenario: Feriado não gera defasagem
- **WHEN** o último dado disponível é o dia útil anterior a um feriado
- **THEN** o artefato NÃO SHALL ser marcado como defasado

#### Scenario: Dia útil ausente gera defasagem
- **WHEN** o último dia útil esperado é posterior à maior data disponível
- **THEN** o artefato SHALL ser marcado como defasado

#### Scenario: Calendário indisponível
- **WHEN** não há calendário para o ano da data esperada
- **THEN** o sistema SHALL usar apenas a regra de fim de semana
- **THEN** SHALL expor o estado `calendario_indisponivel`
