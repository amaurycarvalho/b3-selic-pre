# Spec Delta

## MODIFIED Requirements

### Requirement: Cache cumulativo atômico

O sistema SHALL manter um único CSV cumulativo `vendastesourodireto.csv` e um `metadata.json` no diretório XDG.

O cache SHALL usar TTL condicional (1 hora para o dia corrente/último dia útil, considerando fins de semana e feriados; 6 horas para histórico), gravação atômica em bytes e validação antes da substituição. Cache corrompido SHALL ser miss. O cache bruto NÃO SHALL ter housekeeping; a retenção de 3 anos pertence ao cache analítico.

#### Scenario: Dado corrente expira em 1 hora

- **WHEN** o CSV em cache contém o dia corrente ou o último dia útil calendário-aware e `checked_at` tem menos de 1 hora
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede
- **WHEN** `checked_at` tem 1 hora ou mais
- **THEN** o sistema SHALL tentar um download condicional

#### Scenario: Feriado não conta como dia útil

- **WHEN** a data corrente é feriado e o CSV contém o dia útil anterior
- **THEN** o cache SHALL ser considerado corrente e usar TTL de 1 hora
- **THEN** o sistema NÃO SHALL considerar o cache vencido por causa do feriado

#### Scenario: Dado histórico expira em 6 horas

- **WHEN** o dado mais recente do CSV é histórico e `checked_at` tem menos de 6 horas
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede
- **WHEN** `checked_at` tem 6 horas ou mais
- **THEN** o sistema SHALL tentar um download condicional

#### Scenario: Cache corrompido

- **WHEN** o CSV ou os metadados em cache estão vazios, inválidos ou têm `schema_version` antigo
- **THEN** o sistema SHALL tratar a entrada como miss
- **THEN** o sistema SHALL baixar novamente e substituir o cache

#### Scenario: Escrita atômica

- **WHEN** um download válido conclui
- **THEN** o novo CSV SHALL ser gravado em arquivo temporário e substituído atomicamente
- **THEN** um leitor concorrente NÃO SHALL ver conteúdo parcial

#### Scenario: Falha preserva a versão anterior

- **WHEN** o download falha depois de existir um cache válido
- **THEN** a versão anterior SHALL permanecer disponível

#### Scenario: Leitura somente leitura

- **WHEN** o cache é lido em modo somente leitura
- **THEN** entradas ausentes, vencidas ou corrompidas SHALL ser tratadas como miss
- **THEN** nenhum arquivo SHALL ser removido, renomeado ou alterado

#### Scenario: Metadados completos

- **WHEN** um download ou uma resposta `304` conclui
- **THEN** o metadata SHALL conter `schema_version`, `dataset_name`, `dataset_id`, `resource_id`, `resource_url`, `etag`, `last_modified`, `downloaded_at`, `checked_at`, `size_bytes`, `sha256`, `row_count`, `first_data_date` e `last_data_date`
