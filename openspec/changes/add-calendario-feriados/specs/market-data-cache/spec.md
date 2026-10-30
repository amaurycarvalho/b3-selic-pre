# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
