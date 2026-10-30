# Spec Delta

## MODIFIED Requirements

### Requirement: Cache bruto por fonte e data

O sistema SHALL armazenar o payload bruto de cada fonte de mercado por data ou como snapshot normalizado por fonte, com metadados de esquema, fonte, unidade, hash canônico e horário de extração.

O TTL SHALL variar por recência: 15 a 30 minutos para os últimos 14 dias, 1 a 6 horas para o mês corrente e imutável para datas históricas com mais de um mês.

#### Scenario: Cache recente expira

- **WHEN** um dado dos últimos 14 dias está em cache além do TTL curto
- **THEN** o sistema SHALL revalidar ou buscar novamente a fonte

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
