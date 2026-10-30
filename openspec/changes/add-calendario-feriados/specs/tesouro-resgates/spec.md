# Spec Delta

## MODIFIED Requirements

### Requirement: Download e cache por recurso

O sistema SHALL baixar e cachear cada recurso de resgates independentemente, com timeout padrão de 60 segundos por recurso.

O download SHALL usar `ETag`/`If-None-Match` e `Last-Modified`/`If-Modified-Since`, SHALL tratar `304` como cache válido e SHALL repetir falhas transitórias com backoff/jitter.

#### Scenario: Download bem-sucedido

- **WHEN** um recurso responde HTTP 200 com CSV válido
- **THEN** o sistema SHALL baixar em chunks
- **THEN** o conteúdo SHALL ser validado antes de substituir o cache daquele recurso

#### Scenario: 304 reutiliza o recurso

- **WHEN** o servidor responde `304 Not Modified` para um recurso
- **THEN** o CSV daquele recurso SHALL ser reutilizado
- **THEN** apenas `checked_at` do metadata daquele recurso SHALL ser atualizado

#### Scenario: Falha isolada

- **WHEN** o download de um recurso falha
- **THEN** a versão anterior daquele recurso SHALL ser preservada
- **THEN** os demais recursos SHALL permanecer disponíveis

#### Scenario: Cache por recurso

- **WHEN** os resgates são carregados
- **THEN** cada recurso SHALL ter seu próprio CSV e seu próprio metadata
- **THEN** o TTL SHALL ser aplicado individualmente
- **THEN** recompras SHALL usar 1 hora quando contiver o dia corrente ou o último dia útil calendário-aware e 6 horas quando o dado for histórico
- **THEN** cupom e vencimentos SHALL usar 24 horas

#### Scenario: Feriado não conta como dia útil

- **WHEN** a data corrente é feriado e recompras contêm o dia útil anterior
- **THEN** recompras SHALL usar o TTL de 1 hora
- **THEN** o feriado NÃO SHALL forçar o TTL de 6 horas

#### Scenario: Corpo parcial ou não-CSV

- **WHEN** o corpo baixado é parcial ou o `Content-Type` não começa por `text/csv`
- **THEN** o sistema SHALL tratar como falha transitória
- **THEN** após os retries, SHALL levantar `CommunicationError`
