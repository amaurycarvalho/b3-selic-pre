## Why

O framework atual de classificacao utiliza um limiar binario de ativacao: cada regra ou e satisfeita integralmente ou e descartada. Na pratica, evidencias estruturais possuem diferentes importancias diagnosticas e frequentemente se apresentam em combinacoes parciais que nao atingem o limiar exato de nenhuma regra — mesmo quando uma delas domina claramente as evidencias. Quando isso ocorre, o sistema produz INDEFINIDA com score zero e nenhuma informacao estrutural, pois os fatos de estrutura sao todos bloqueados por `gated_by`. Alem disso, a ausencia de uma categoria intermediaria de volatilidade e de uma regra que capture recuperacoes longas e sustentadas — uma assinatura comum em curvas DI — limita a capacidade diagnostica do motor.

## What Changes

- **Adicionar R199 — Classe Primaria por Dominancia**: apos a avaliacao normal das regras, o Classifier coleta os escores de ativacao que cada regra produziu durante sua propria avaliacao (`activation_score` = features satisfeitas ponderadas / total possivel). Se nenhuma classe primaria ativou diretamente, R199 seleciona a de maior `activation_score` >= 0.70 e a promove com confianca correspondente. Nao ha reavaliacao de regras — R199 apenas consome o estado ja computado.
- **Rastrear estado de avaliacao por regra**: cada regra, ao ser avaliada, produz `matched_features`, `missing_features` e `activation_score`. Esse estado e armazenado e consumido por R199, permitindo auditoria completa de quais evidencias foram consideradas e por que uma classe foi (ou nao) promovida.
- **Separar fatos estruturais em independentes e dependentes**: fatos como TORCAO, EMPINAMENTO, ACHATAMENTO e DEGRAUS sao propriedades intrinsecas da curva e passam a ser avaliados independentemente da classe primaria (sem `gated_by`). Fatos como RECUPERACAO_SUSTENTADA mantem o gate, pois dependem semanticamente do contexto de vale.
- **Adicionar VOLATILIDADE_MODERADA**: fecha a lacuna diagnostica entre baixa e alta volatilidade. Escore 0 (informativo).
- **Adicionar RECUPERACAO_LONGA**: detecta tendencia ascendente persistente com criterios matematicos deterministicos: existencia de segmento contiguo com >= 70% de deltas positivos abrangendo pelo menos 15% da curva, slope de regressao positivo nesse intervalo, e amplitude >= 40% da amplitude total. Independe da classe primaria.

## Capabilities

### New Capabilities

- `auto-analysis`: Pipeline de inferencia hierarquica de 5 niveis para analise automatica de curvas de taxas referenciais. Inclui extracao de metricas, computacao de features, classificacao por regras com grupos de exclusividade e fallback por dominancia, rastreamento de estado de avaliacao, scoring ponderado, e templates internacionalizaveis.

### Modified Capabilities

<!-- Nenhuma capacidade existente em openspec/specs/ e modificada. -->

## Impact

- **Arquivos modificados**:
  - `src/b3_selic_pre/application/analyze/_registry.py` — nova regra RECUPERACAO_LONGA; remocao de `gated_by` dos fatos independentes; nova regra VOLATILIDADE_MODERADA
  - `src/b3_selic_pre/application/analyze/_classifier.py` — struct `RuleEvaluation` para estado de avaliacao; logica R199 consumindo `activation_score`; coleta de `matched_features`/`missing_features`
  - `src/b3_selic_pre/application/analyze/_features.py` — novas features `VOLATILITY_MODERATE` e `LONG_RECOVERY`
  - `src/b3_selic_pre/application/analyze/_scoring.py` — entradas `VOLATILIDADE_MODERADA` e `RECUPERACAO_LONGA`
  - `src/b3_selic_pre/application/analyze/_templates.py` — templates `fallback_primary`, `volmod_qual`, `longrec_struct`
  - `src/b3_selic_pre/application/analyze/_config.py` — novo threshold `recuperacao_longa_min_pct`; parâmetros `recuperacao_longa_min_ratio` e `recuperacao_longa_min_amplitude`
  - `tests/test_analyze.py` — testes para R199, estado de avaliacao, fatos independentes, volatilidade moderada, recuperacao longa
