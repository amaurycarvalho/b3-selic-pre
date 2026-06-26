## Context

O motor de inferencia atual classifica curvas com geometria vale+recuperacao+plato como INDEFINIDA. A causa raiz nao e um parametro especifico, mas duas deficiencias arquiteturais: (1) ausencia de um mecanismo de fallback quando nenhuma regra atinge 100% de satisfacao — o sistema opera com limiar binario e descarta evidencias parciais, e (2) acoplamento rigido entre classe primaria e fatos estruturais via `gated_by`. Adicionalmente, o motor nao possui categoria intermediaria de volatilidade nem detecta recuperacoes longas e sustentadas — uma assinatura comum em curvas DI.

Ajustes pontuais de thresholds foram considerados e rejeitados: um aumento de 500% sem validacao estatistica sobre um conjunto amplo de curvas introduziria falsos positivos. A solucao arquitetonica — nao parametrica — e o caminho correto.

## Goals / Non-Goals

**Goals:**
- Introduzir R199 — fallback por dominancia que consome estado de avaliacao ja computado (nao reavalia regras)
- Introduzir `RuleEvaluation` como struct que registra `activation_score`, `matched_features`, `missing_features` por regra
- Separar fatos estruturais em independentes (sem gate) e dependentes (com gate)
- Adicionar fato VOLATILIDADE_MODERADA para cobertura da faixa intermediaria
- Adicionar regra RECUPERACAO_LONGA com criterios matematicos deterministicos

**Non-Goals:**
- Alterar `min_optional` de qualquer regra existente
- Alterar valores de thresholds existentes
- Criar novas classes primarias
- Implementar categorizacao por faixas para suavidade/volatilidade (mudanca futura)
- Modificar o calculo de metricas base (`_metrics.py`)

## Decisions

### D1: R199 consome estado de avaliacao, nao reavalia regras

**Problema:** Implementar R199 reavaliando features para cada regra duplica logica, introduz risco de divergencia entre a avaliacao normal e a do fallback, e dificulta auditoria.

**Decisao:** Introduzir um struct `RuleEvaluation` que cada regra preenche durante sua propria avaliacao:

```python
@dataclass
class RuleEvaluation:
    rule_id: str
    matched_features: list[str]    # features satisfeitas (required + optional)
    missing_features: list[str]     # features nao satisfeitas (required + optional)
    activation_score: float         # Σ pesos_satisfeitos / Σ pesos_possiveis
    activated: bool                 # se a regra ativou diretamente
```

Durante o loop principal do Classifier, cada regra (ativa ou nao) registra seu `RuleEvaluation`. Regras que nao passaram no gate ou cujo `required_features` falhou ainda assim produzem uma `RuleEvaluation` com `activated=False` e `activation_score` correspondente.

Apos o loop, se nenhum fato `CLASSIFICATION` foi gerado:

1. Filtrar `RuleEvaluation` com `exclusive_group == "PRIMARY_CLASS"` (excluindo INDEFINIDA)
2. Selecionar a de maior `activation_score`
3. Se `activation_score >= 0.70`, gerar fato com `confidence = activation_score`
4. Senao, INDEFINIDA permanece

```python
# Pseudocodigo no Classifier
evaluations: list[RuleEvaluation] = []

for rule in rules:
    eval = RuleEvaluation(rule_id=rule.id, ...)
    # ... avaliacao normal ...
    # Preenche matched_features, missing_features, activation_score
    evaluations.append(eval)
    
    if activated:
        facts.append(fact)
        if rule.exclusive_group:
            activated_groups.add(rule.exclusive_group)

# Pos-loop: R199 fallback
if not any(f.fact_type == FactType.CLASSIFICATION for f in facts):
    primary_evals = [e for e in evaluations 
                     if rule_has_exclusive_group(e.rule_id, "PRIMARY_CLASS")
                     and e.rule_id != "INDEFINIDA"]
    if primary_evals:
        best = max(primary_evals, key=lambda e: e.activation_score)
        if best.activation_score >= 0.70:
            facts.append(Fact(
                id=rule_generated_fact(best.rule_id),
                confidence=best.activation_score,
                derived_from_features=best.matched_features,
                template_id="fallback_primary",
                ...
            ))
```

**Vantagens:**
- Nenhuma regra e avaliada duas vezes
- `activation_score` e computado uma unica vez por regra, no mesmo local
- `matched_features` e `missing_features` sao um subproduto natural da avaliacao
- Auditoria: e possivel inspecionar por que cada regra ativou ou nao
- R199 e apenas uma funcao de decisao sobre dados ja existentes

**Alternativa considerada:** R199 iterando novamente sobre as regras e reavaliando features. Rejeitada: duplica logica e introduz risco de inconsistencia.

### D2: Pesos das features para activation_score

**Problema:** Nem todas as features tem o mesmo valor diagnostico. `VALLEY_EARLY` (minimo global antes de 40%) e muito mais informativo que `SHORT_END_UP` (media do primeiro terco acima do inicio). Um sistema de pesos reconhece essa assimetria.

**Decisao:** Pesos definidos em dicionario no Classifier, organizados por nivel de relevancia diagnostica:

```python
FEATURE_WEIGHTS: dict[str, float] = {
    # Nivel 3 — Assinaturas estruturais (maximo valor diagnostico)
    "VALLEY_EARLY": 3.0,
    "PEAK_EARLY": 3.0,
    "SIGMOIDAL_SHAPE": 3.0,
    "TREND_UP": 3.0,
    "TREND_DOWN": 3.0,
    "OSCILLATING": 3.0,
    
    # Nivel 2 — Evidencias direcionais e de planicidade
    "FINAL_GT_INITIAL": 2.0,
    "FINAL_LT_INITIAL": 2.0,
    "AFTER_MIN_UP": 2.0,
    "AFTER_MAX_DOWN": 2.0,
    "AMPLITUDE_LOW": 2.0,
    "DELTA_FINAL_LOW": 2.0,
    "SLOPE_FLAT": 2.0,
    
    # Nivel 1.5 — Confirmacao contextual
    "RECOVERY_STRONG": 1.5,
    "MONOTONIC": 1.5,
    
    # Nivel 1 — Evidencias segmentais (menor valor individual)
    "SHORT_END_UP": 1.0,
    "SHORT_END_DOWN": 1.0,
    "LONG_END_UP": 1.0,
    "LONG_END_DOWN": 1.0,
    "MID_END_UP": 1.0,
}
```

`activation_score` = Σ pesos das features em `matched_features` / Σ pesos de todas as features (required + optional) da regra.

Exemplo: VALE tem required `[VALLEY_EARLY: 3.0]` e optional `[FINAL_GT_INITIAL: 2.0, AFTER_MIN_UP: 2.0, RECOVERY_STRONG: 1.5, SHORT_END_UP: 1.0]`. Score maximo = 3.0 + 2.0 + 2.0 + 1.5 + 1.0 = 9.5. Se VALLEY_EARLY, FINAL_GT_INITIAL e AFTER_MIN_UP estao satisfeitas: score = 3.0 + 2.0 + 2.0 = 7.0. `activation_score = 7.0/9.5 ≈ 0.74`.

### D3: RECUPERACAO_LONGA — definicao matematica deterministica

**Problema:** A especificacao "tendencia ascendente persistente" e ambigua e permite implementacoes diferentes.

**Decisao:** Definir `LONG_RECOVERY` com criterios matematicos exatos:

```
LONG_RECOVERY = True quando TODAS as condicoes abaixo sao satisfeitas:

1. TAMANHO MINIMO DA CURVA: n >= 20 pontos

2. SEGMENTO MINIMO: Existe um segmento contiguo S = rates[i..j] tal que:
   a) |S| >= max(10, n * config.recuperacao_longa_min_pct)
      onde config.recuperacao_longa_min_pct = 0.15 (15% da curva)
   b) Para todo k em [i, j-1]: a proporcao de deltas positivos em S
      e >= config.recuperacao_longa_min_ratio (default: 0.70)
      delta_positivo = rates[k+1] - rates[k] > config.epsilon_slope

3. SLOPE POSITIVO NO SEGMENTO:
   polyfit(days[i..j], rates[i..j], 1)[0] > config.epsilon_slope

4. AMPLITUDE SIGNIFICATIVA:
   (max(rates[i..j]) - min(rates[i..j])) >= amplitude_total * config.recuperacao_longa_min_amplitude
   onde config.recuperacao_longa_min_amplitude = 0.40 (40% da amplitude total)

Se multiplos segmentos satisfazem, selecionar o de maior |S|.
```

Novos thresholds em `InferenceConfig`:
```python
recuperacao_longa_min_pct: float = 0.15       # fracao minima da curva
recuperacao_longa_min_ratio: float = 0.70     # proporcao minima de deltas positivos
recuperacao_longa_min_amplitude: float = 0.40 # fracao minima da amplitude total
```

**Justificativa dos defaults:**
- 15% da curva: filtro contra micro-tendencias. Numa curva de 230 pts, exige >= 35 pts.
- 70% deltas positivos: permite pequenas correcoes (30% de recuos) sem descaracterizar a tendencia.
- 40% da amplitude total: garante que a recuperacao e economicamente significativa.

**Alternativa considerada:** Vincular LONG_RECOVERY ao indice do minimo global. Rejeitada: tornaria a regra dependente do contexto de vale, contrariando o design de fato estrutural independente. A deteccao por segmento contiguo e mais geral e captura recuperacoes em qualquer posicao da curva.

### D4: Fatos estruturais independentes vs. dependentes

(Sem alteracao em relacao a versao anterior; mantido para integridade do documento.)

| Fato | Tipo | Gate | Justificativa |
|------|------|------|---------------|
| RECUPERACAO_SUSTENTADA | Dependente | `gated_by: ["VALE"]` | So faz sentido se ha um vale do qual se recuperar |
| RECUPERACAO_LONGA (novo) | Independente | Sem gate | Persistencia ascendente e propriedade intrinseca |
| ACHATAMENTO | Independente | Sem gate | Relacao curto/longo e observavel direta |
| EMPINAMENTO | Independente | Sem gate | Idem |
| TORCAO | Independente | Sem gate | Torcao e propriedade da estrutura a termo |
| DEGRAUS | Independente | Sem gate | Staircasing e observavel direto |
| MONOTONIA_STRUCT | Independente | Sem gate | Monotonia e propriedade intrinseca |

### D5: VOLATILIDADE_MODERADA

(Sem alteracao.)

```python
features["VOLATILITY_MODERATE"] = _bool_feat(
    "VOLATILITY_MODERATE",
    config.volatilidade_baixa < volatilidade < config.volatilidade_alta,
    ["indice_volatilidade"],
)
```

Score: 0 (informativo, nao afeta pontuacao).

### D6: Thresholds mantidos — categorizacao adiada

(Sem alteracao.)

Nao alterar `suavidade_relativo` (0.01), `volatilidade_baixa` (0.01), nem `volatilidade_alta` (0.05). A solucao por categorizacao em faixas requer estudo de distribuicao em dados historicos e sera tratada em mudanca futura.

## Risks / Trade-offs

- **[Risco] R199 com threshold 0.70 pode promover classes com evidencias moderadas** → **Mitigacao:** O template `fallback_primary` comunica explicitamente a incerteza. Confianca exibida reflete o score real. A auditoria via `RuleEvaluation.missing_features` permite ao usuario entender quais evidencias faltaram.
- **[Risco] RECUPERACAO_LONGA pode gerar falsos positivos em curvas com tendencias curtas** → **Mitigacao:** Requerimentos combinados de comprimento (15% da curva), proporcao de deltas (70%), slope positivo e amplitude significativa (40%) formam um filtro multicriterio robusto.
- **[Risco] Remover gates pode gerar fatos estruturais contraditorios** → **Mitigacao:** Features mutuamente baseadas em condicoes observaveis. ACHATAMENTO e EMPINAMENTO usam thresholds opostos — e possivel que nenhum ative, mas improvavel que ambos ativem simultaneamente.
- **[Trade-off] Adiar categorizacao por faixas** → Lacuna de suavidade permanece como divida tecnica documentada. VOLATILIDADE_MODERADA cobre parcialmente a lacuna de volatilidade.

## Architecture Diagram (atualizado)

```
Metrics
    │
    ▼
Features
    │
    ▼
┌──────────────────────────────────────┐
│        Classifier (puro)             │
│                                      │
│  for rule in rules:                  │
│    evaluate(rule, features)          │
│    ├── produce Fact (if activated)   │
│    └── produce RuleEvaluation ───────┤──► stored in evaluations[]
│                                      │
│  if no PRIMARY_CLASS fact:           │
│    R199 ← consumes evaluations[] ────┘
│    └── promote best if score ≥ 0.70  │
└──────────────────────────────────────┘
    │
    ▼
Facts + RuleEvaluations (audit trail)
    │
    ▼
ScoringPolicy
    │
    ▼
Report
```
