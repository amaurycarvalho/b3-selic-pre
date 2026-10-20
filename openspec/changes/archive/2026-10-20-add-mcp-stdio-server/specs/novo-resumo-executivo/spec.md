## ADDED Requirements

### Requirement: Análise sobre as representações curta e longa

O resumo executivo SHALL poder ser calculado sobre a representação `curta`, usando os registros brutos, ou sobre a representação `longa`, usando a série de taxas médias por ano.

Na representação longa, a taxa curta SHALL ser a média do primeiro ano, a taxa longa SHALL ser a média do último ano e a inclinação SHALL ser a diferença entre elas em pontos-base. A estabilidade das expectativas e a última mudança de inclinação SHALL usar as séries anuais convertidas de cada data do histórico.

A análise da representação curta SHALL permanecer inalterada.

#### Scenario: Análise curta inalterada

- **WHEN** a análise é solicitada para a representação curta
- **THEN** o resultado SHALL ser calculado a partir dos registros brutos
- **THEN** o comportamento existente SHALL ser preservado

#### Scenario: Análise longa usa médias anuais

- **WHEN** a análise é solicitada para a representação longa
- **THEN** a taxa curta SHALL ser a média do primeiro ano
- **THEN** a taxa longa SHALL ser a média do último ano
- **THEN** a inclinação SHALL ser calculada a partir dessas médias

#### Scenario: Histórico longo é consistente

- **WHEN** há histórico disponível para a análise longa
- **THEN** cada data do histórico SHALL ser convertida para médias anuais
- **THEN** a estabilidade e a mudança de inclinação SHALL usar essas séries

### Requirement: Identificação da representação no resultado

O resultado da análise SHALL identificar a representação usada, `curta` ou `longa`, para que consumidores não confundam os textos.

#### Scenario: Resultado identifica a curva

- **WHEN** a análise longa é devolvida
- **THEN** o resultado SHALL identificar `curta` ou `longa` conforme a solicitação
- **THEN** o texto SHALL corresponder à representação identificada
