# Spec Delta

## MODIFIED Requirements

### Requirement: Série histórica de 12 meses

O sistema SHALL disponibilizar séries diárias dos últimos 12 meses para dólar em BRL/USD e ouro em R$/g, alinhadas por data e com proveniência em cada série.

Cada item SHALL conter data, valor, unidade, origem, método e horário de extração. Datas sem cotação em uma fonte SHALL ser omitidas ou preenchidas apenas com o último valor válido, com a defasagem indicada. A ausência de ponto em fim de semana ou feriado SHALL ser classificada como lacuna esperada; a ausência em dia útil SHALL ser classificada como lacuna real.

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

#### Scenario: Lacuna em feriado é esperada

- **WHEN** a série não tem ponto em um feriado ou fim de semana
- **THEN** a ausência SHALL ser classificada como lacuna esperada
- **THEN** NÃO SHALL ser reportada como falha de fonte

#### Scenario: Lacuna em dia útil é real

- **WHEN** a série não tem ponto em um dia útil coberto pelo calendário
- **THEN** a ausência SHALL ser classificada como lacuna real
- **THEN** o status SHALL indicar o dia útil sem dado

#### Scenario: Sem dados em cache

- **WHEN** não há série em cache para a janela
- **THEN** o sistema SHALL informar ausência de dados e orientar a atualização
- **THEN** nenhuma chamada de rede SHALL ser iniciada automaticamente
