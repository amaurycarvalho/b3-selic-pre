## Context

O motor atual (`fix-inference-engine-rules`) avalia 20 regras (R001–R020) como funções independentes em uma lista plana. Três blocos (tendência, geométrico, segmentos) organizam a saída, mas não impõem exclusão mútua entre conceitos contraditórios. O `IndiceTendencia = (final - inicial) / amplitude` é sensível a outliers nas pontas. A classificação de score usa soma simples com pesos uniformes (+2, +1, 0, −1), ignorando a importância relativa de cada descoberta.

O novo design substitui a arquitetura plana por 5 níveis hierárquicos, onde cada nível tem responsabilidade e semântica distintas. A classificação primária é mutuamente exclusiva, eliminando contradições. O score é ponderado por nível. Uma métrica de confiança por nível complementa o score.

## Goals / Non-Goals

**Goals:**
- Classificação primária exclusiva (apenas uma classe geométrica por curva)
- Direção da tendência via regressão linear (`slope_global`), não endpoint-difference
- Score ponderado: Nível 1 ×3, Nível 2 ×2, Nível 3 ×1
- Confiança por nível (razão de regras satisfeitas / aplicáveis)
- Relatório com separação FORMA vs INTENSIDADE
- Condições mais estritas para PLANA, SIGMOIDE, e MUDANÇA ESTRUTURAL

**Non-Goals:**
- Alterar métricas de entrada (`DetailedMetrics` mantém todos os campos, adiciona `slope_global`, remove `indice_tendencia`)
- Modificar GUI, CLI, ou formato de exportação
- Alterar contrato público de `analyze()` (mesmos parâmetros, mesmo tipo de retorno)
- Implementar análise para modos consolidado/evolução

## Decisions

### D1: Arquitetura de 5 níveis

```
Nível 1: Classificação Primária (1 escolhida)
         OSCILANTE > VALE > PICO > SIGMOIDE > ASC > DESC > PLANA

Nível 2: Características Estruturais (múltiplas, gated por N1)
         RECUPERACAO | ACHATAMENTO | EMPINAMENTO | TORCAO
         MONOTONIA | MUDANCA_ESTRUTURAL

Nível 3: Qualidade da Curva (múltiplas, sempre habilitadas)
         SUAVE | SERRILHADA | CONSENSO | DISPERSAO

Nível 4: Intensidade (score ponderado + confiança)
         Score = Σ(nível_peso × regra_score)
         Confiança por nível = ativadas / aplicáveis

Nível 5: Relatório (FORMA + INTENSIDADE + QUALIDADE)
```

**Alternativa considerada:** Manter regras planas com sistema de prioridades via pré-condições. Rejeitada porque não resolve a raiz do problema (níveis conceituais diferentes competindo no mesmo plano) e seria frágil — cada nova regra exigiria reavaliar interações com todas as outras.

### D2: `slope_global` substitui `IndiceTendencia`

**Problema:** `IndiceTendencia = (final - inicial) / amplitude` usa apenas dois pontos. Uma curva com vale (inicial alta → mínima → final alta) tem `final - inicial` pequeno mesmo sendo claramente ascendente após o vale.

**Decisão:** `slope_global = np.polyfit(days, rates, 1)[0]` — coeficiente angular da regressão linear sobre dias úteis. Unidade: taxa por DU. Robusto a outliers porque considera todos os pontos.

**Threshold:** `slope_global > 0.00005` → ASC, `slope_global < -0.00005` → DESC. Equivale a ~0.038 de variação em 756 DU, ou ~3.8 bps ao longo da curva.

### D3: Algoritmo de classificação primária

Executado em ordem de precedência. A primeira condição satisfeita define a classe:

| # | Classe      | Condição                                              |
|---|-------------|-------------------------------------------------------|
| 1 | OSCILANTE   | `qtd_mudancas / n >= 0.15`                            |
| 2 | VALE        | `qtd_minimos == 1` E `pos/n < 0.35` E `final > inic`  |
| 3 | PICO        | `qtd_maximos == 1` E `≥80% deltas pós-pico negativos` |
| 4 | SIGMOIDE    | `qtd_inflexoes >= 2` E cada trecho entre inflexões > 15% da curva |
| 5 | ASCENDENTE  | `slope_global > 0.00005`                              |
| 6 | DESCENDENTE | `slope_global < -0.00005`                             |
| 7 | PLANA       | `amplitude < 0.10` E `|delta_final| < 0.05` E `|slope_global| < 0.00005` |

A classe PLANA só é atribuída se **todas as 3 condições** forem verdadeiras.

### D4: Gating do Nível 2

Cada classe primária habilita um subconjunto das regras estruturais:

| Classe      | Regras habilitadas                                    |
|-------------|-------------------------------------------------------|
| OSCILANTE   | (nenhuma)                                             |
| VALE        | RECUPERACAO, ACHATAMENTO, EMPINAMENTO                 |
| PICO        | TORCAO                                                |
| SIGMOIDE    | MUDANCA_ESTRUTURAL                                    |
| ASCENDENTE  | MONOTONIA, ACHATAMENTO, EMPINAMENTO                   |
| DESCENDENTE | MONOTONIA, ACHATAMENTO, EMPINAMENTO, TORCAO           |
| PLANA       | (nenhuma)                                             |

Regras não habilitadas não são avaliadas (nem contam para confiança).

### D5: Score ponderado por nível

| Nível | Peso  | Justificativa                                  |
|-------|-------|------------------------------------------------|
| 1     | ×3    | Define a forma geral — é a descoberta principal |
| 2     | ×2    | Refina com características estruturais          |
| 3     | ×1    | Qualidade e textura — informativo               |

Score base por classe primária:
- ASC/DESC = +2 (peso 3 → contribuição +6)
- VALE/PICO/SIGMOIDE = +2 (peso 3 → contribuição +6)
- OSCILANTE = +1 (peso 3 → contribuição +3)
- PLANA = 0 (peso 3 → contribuição 0)

Regras de nível 2 e 3 mantêm scores +1/0/−1 existentes, multiplicados pelo peso do nível.

### D6: Confiança por nível

```
Confiança_N1 = 100% (sempre uma classe escolhida)
Confiança_N2 = ativadas / aplicáveis (ex: 2/3 = 67%)
Confiança_N3 = ativadas / total_n3 (ex: 3/4 = 75%)
```

Se nenhuma regra for aplicável em N2, confiança = 100% (nada a verificar).
Reportada como percentual no relatório.

### D7: Relatório — separação FORMA / INTENSIDADE

```
FORMA
─────
Classe Primária: VALE
Estrutura: Recuperação sustentada, segmento longo ascendente

QUALIDADE
─────────
Curva suave, amplitude dentro do padrão

INTENSIDADE
───────────
Score: 9 — Reprecificação relevante
Confiança: N1 100% | N2 67% | N3 75%
```

O bloco FORMA é sempre emitido. QUALIDADE e INTENSIDADE complementam.

### D8: Data model changes

```python
# _metrics.py — DetailedMetrics
# Adiciona:
slope_global: float  # np.polyfit(days, rates, 1)[0]

# Remove:
indice_tendencia: float  # substituído por slope_global

# _thresholds.py → removido, integrado como constantes no _classifier.py

# Novo: ClassificationResult (substitui lista plana de RuleResult)
@dataclass
class LevelResult:
    class_name: str       # "VALE", "ASCENDENTE", etc.
    text: str             # descrição legível
    score: int            # contribuição ao score
    weight: int           # peso do nível (3, 2, ou 1)

@dataclass
class InferenceResult:
    primary: LevelResult              # Nível 1 (único)
    structural: list[LevelResult]     # Nível 2 (múltiplo)
    quality: list[LevelResult]        # Nível 3 (múltiplo)
    total_score: int
    confidence: dict[str, float]      # {"n1": 1.0, "n2": 0.67, "n3": 0.75}
    intensity_label: str
```

### D9: Nova estrutura de arquivos

```
application/analyze/
├── __init__.py          # facade analyze(), modificado
├── _metrics.py          # +slope_global, -indice_tendencia
├── _classifier.py       # NOVO: classificação hierárquica 5 níveis
├── _report.py           # modificado: novo formato FORMA/INTENSIDADE
├── _rules.py            # REMOVIDO (substituído por _classifier.py)
├── _thresholds.py       # REMOVIDO (thresholds integrados em _classifier.py)
└── _metrics_evolution.py # mantido (não usado por este change)
```

## Risks / Trade-offs

- **`slope_global` vs `IndiceTendencia`:** slope_global é robusto a outliers mas pode não capturar curvas em "U" ou "V" simétricas (onde a regressão dá ~0). Mitigação: VALE e PICO são detectados antes de ASC/DESC na prioridade, capturando esses casos.
- **OSCILANTE como topo:** pode classificar curvas com padrões reais como ruído se o threshold for baixo. Mitigação: threshold default 0.15 (15% de trocas de direção), calibrável. Curvas da B3 raramente excedem 0.10.
- **Remoção de `_thresholds.py`:** perde-se a conveniência de um dataclass único para customização externa. Mitigação: thresholds são expostos como parâmetros keyword no facade `analyze()`.
- **Confiança por nível:** se N2 não tem regras aplicáveis (ex: PLANA), confiança 100% pode ser enganosa. Mitigação: reportar "N/A" em vez de percentual nesse caso.
- **Migração de testes:** ~39 testes existentes precisam ser reescritos para a nova API. Custo alto, mas necessário — a arquitetura mudou fundamentalmente.

## Open Questions

- O threshold `slope_global > 0.00005` (3.8 bps em 756 DU) é adequado para distinguir ASC de PLANA? Pode precisar de calibração com dados reais.
- Deve-se manter `detailed_metrics.indice_tendencia` como campo calculado mas não usado (para backward compat de testes/análise manual)?
- A confiança deve ser exposta no `AnalysisReport` ou apenas no texto formatado?
