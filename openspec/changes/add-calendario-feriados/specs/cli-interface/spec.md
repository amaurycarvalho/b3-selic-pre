# Spec Delta

## MODIFIED Requirements

### Requirement: Parâmetro comum de data

Os subcomandos `consultar`, `atualizar` e `exportar` SHALL aceitar `--data AAAA-MM-DD`, com a data local corrente como valor padrão.

A data SHALL ser validada no formato `AAAA-MM-DD`, NÃO SHALL estar no futuro e SHALL respeitar a janela máxima de histórico de 30 dias. Se a data cair em fim de semana ou feriado, a CLI SHALL usar a data útil anterior e SHALL emitir um aviso em `stderr` informando a data solicitada, a data resolvida e o motivo.

#### Scenario: Data omitida usa hoje
- **WHEN** o usuário executa `atualizar` sem `--data`
- **THEN** a CLI SHALL usar a data local corrente
- **THEN** se a data corrente não for útil, SHALL usar a data útil anterior e avisar em `stderr`

#### Scenario: Data inválida é rejeitada
- **WHEN** o usuário informa uma data fora do formato `AAAA-MM-DD`
- **THEN** a CLI SHALL encerrar com código `2` e não SHALL consultar a B3

#### Scenario: Data futura é rejeitada
- **WHEN** o usuário informa uma data posterior à data corrente
- **THEN** a CLI SHALL encerrar com código `2` e não SHALL consultar a B3

#### Scenario: Data antiga é rejeitada
- **WHEN** o usuário informa uma data anterior à janela de 30 dias
- **THEN** a CLI SHALL encerrar com código `2` e não SHALL consultar a B3

#### Scenario: Fim de semana é ajustado
- **WHEN** a data informada cai em sábado ou domingo
- **THEN** a CLI SHALL usar a sexta-feira anterior como data de referência
- **THEN** SHALL emitir um aviso em `stderr` com a data resolvida e o motivo `fim_de_semana`

#### Scenario: Feriado é ajustado com aviso
- **WHEN** a data informada cai em feriado
- **THEN** a CLI SHALL usar o dia útil anterior como data de referência
- **THEN** SHALL emitir um aviso em `stderr` com a data resolvida e o nome do feriado

## ADDED Requirements

### Requirement: Subcomando feriados

A CLI SHALL oferecer o subcomando `feriados` para listar os feriados de um ano, consultar uma data e exportar o calendário em CSV ou JSON. A listagem e a exportação SHALL ler apenas o cache; `--atualizar` SHALL permitir atualizar o ano antes de responder.

#### Scenario: Listagem de um ano
- **WHEN** o usuário executa `b3-selic-pre feriados --ano 2026`
- **THEN** a CLI SHALL listar data, dia da semana e nome de cada feriado do ano

#### Scenario: Consulta de uma data
- **WHEN** o usuário executa `b3-selic-pre feriados --data 2026-04-03`
- **THEN** a CLI SHALL informar que a data não é útil, o motivo e o nome do feriado

#### Scenario: Exportação CSV
- **WHEN** o usuário executa `b3-selic-pre feriados --ano 2026 --formato csv --saida feriados.csv`
- **THEN** a CLI SHALL gravar o arquivo com separador `;`, datas ISO e colunas de data, dia da semana, nome e origem

#### Scenario: Exportação JSON
- **WHEN** o usuário executa `b3-selic-pre feriados --ano 2026 --formato json`
- **THEN** a CLI SHALL imprimir um payload JSON com ano, origem, instante de extração e feriados

#### Scenario: Ano sem cache
- **WHEN** o ano solicitado não está no cache e `--atualizar` não foi informado
- **THEN** a CLI SHALL encerrar com código `1` e orientar o uso de `--atualizar`
