# Spec Delta

## ADDED Requirements

### Requirement: Datas não úteis não são solicitadas

O sistema SHALL resolver a data de referência e cada alvo da janela de evolução para um dia útil antes de escolher a fonte. Ele NÃO SHALL emitir `GetList` nem `GetDownloadFile` para fim de semana ou feriado. Sem calendário para o ano, aplica somente a regra de fim de semana e informa o estado degradado.

#### Scenario: Feriado na data de referência
- **WHEN** a data informada é feriado e existe calendário para o ano
- **THEN** a data é resolvida para o dia útil anterior antes da escolha da fonte
- **THEN** nenhuma requisição é feita para a data do feriado

#### Scenario: Fim de semana continua não útil
- **WHEN** a data informada cai em sábado ou domingo
- **THEN** a data é resolvida para a sexta-feira anterior antes da escolha da fonte

#### Scenario: Feriado na janela de evolução
- **WHEN** um alvo de 7, 14, 21 ou 28 dias cai em feriado
- **THEN** o alvo é resolvido para o dia útil anterior
- **THEN** nenhuma requisição é feita para a data do feriado

#### Scenario: Calendário indisponível
- **WHEN** não há calendário para o ano e a fonte de feriados falhou
- **THEN** o sistema aplica somente a regra de fim de semana
- **THEN** o estado `calendario_indisponivel` é exposto e a carga continua
