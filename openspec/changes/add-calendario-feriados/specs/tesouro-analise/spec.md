# Spec Delta

## MODIFIED Requirements

### Requirement: Política de atualização do cache bruto

O cache bruto SHALL permanecer cumulativo e completo, sem poda.

O TTL SHALL ser de 1 hora para vendas e recompras quando o cache contém o dia corrente ou o último dia útil calendário-aware (considerando fins de semana e feriados); 6 horas para o histórico desses recursos; e 24 horas para estoque, cupom e vencimentos. Uma resposta `304` SHALL reutilizar o cache.

#### Scenario: Dado do dia corrente

- **WHEN** vendas ou recompras contêm o dia corrente
- **THEN** o cache SHALL expirar em 1 hora

#### Scenario: Último dia útil em feriado

- **WHEN** a data corrente é feriado e vendas ou recompras contêm o dia útil anterior
- **THEN** o cache SHALL ser considerado corrente e expirar em 1 hora
- **THEN** o feriado NÃO SHALL reiniciar o TTL de 6 horas

#### Scenario: Dado histórico

- **WHEN** vendas ou recompras não contêm o dia corrente nem o último dia útil
- **THEN** o cache SHALL expirar em 6 horas
- **THEN** as linhas históricas NÃO SHALL ser recarregadas

#### Scenario: Recurso mensal ou eventual

- **WHEN** o recurso é estoque, cupom ou vencimentos
- **THEN** o cache SHALL expirar em 24 horas

#### Scenario: 304 reutiliza

- **WHEN** o servidor responde `304 Not Modified`
- **THEN** o CSV SHALL ser reutilizado
- **THEN** apenas o `checked_at` SHALL ser atualizado
