## Context

O motor de inferência atual (`application/analyze/`) implementa 14 regras (R001–R014) sobre métricas extraídas da curva de juros detalhada. Durante revisão da especificação original, foram identificados bugs lógicos em 4 regras (R004, R005, R006, R013), métricas calculadas sem uso, e gaps de design (classificação de score sem distinção de direção, threshold de suavidade absoluto). Este design documenta as correções e extensões necessárias.

O pipeline permanece inalterado: `raw data → _metrics.py → _rules.py → _report.py`. As mudanças são internas a `_metrics.py`, `_rules.py`, `_thresholds.py` e `__init__.py`. Nenhuma alteração na GUI, CLI ou formato de exportação.

## Goals / Non-Goals

**Goals:**
- Corrigir bugs que distorcem a ativação de R004, R005, R006, R013
- Adicionar 6 novas regras (R015–R020) capturando fenômenos economicamente relevantes
- Tornar R010 (Curva Suave) relativo à amplitude da curva
- Introduzir classificação dual (ascendente/descendente) baseada na tendência global
- Aproveitar métricas já calculadas e não utilizadas (`qtd_mudancas`, curvatura)

**Non-Goals:**
- Alterar a estrutura do relatório (4 blocos)
- Modificar a GUI ou o fluxo de redraw
- Implementar análise para modos consolidado/evolução
- Alterar o formato de `RateRecord` ou `AnalysisReport`
- Mudar a API pública de `analyze()`

## Decisions

### D1: Correção de R004 — Posição relativa

**Problema:** `pos_ratio = pos_min / len(range(len(metrics.minimos_locais)))` sempre resulta em `pos/1` quando há exatamente 1 mínimo. Além disso, `max_day=756` está hardcoded.

**Decisão:** A posição relativa deve ser `indice_do_minimo_global / total_de_pontos`. Usar o índice diretamente do array de taxas (índice 0-based / `len(rates)`). O `max_day` hardcoded é substituído por `max(days)` dos dados reais.

**Alternativa considerada:** Usar `du_do_minimo / max_du` (razão por dias úteis). Rejeitada porque o índice no array é mais simples e equivalente quando os pontos são espaçados regularmente.

### D2: Correção de R005 — Queda contínua

**Problema:** A condição "seguido de queda contínua" é implementada apenas como `longo.slope < 0`, ignorando o comportamento da curva entre o pico e o final.

**Decisão:** Após identificar o índice do máximo local único, calcular os deltas ponto-a-ponto (`np.diff(rates)`) a partir daquela posição até o final. Exigir que ≥80% desses deltas sejam negativos (mesmo threshold de "proporção" usado em R006 e R013).

### D3: Correção de R006 e R013 — Deltas ponto-a-ponto

**Problema:** Ambas as regras usam deltas entre taxas finais de segmentos (3–4 valores) quando a especificação exige deltas sucessivos entre pontos consecutivos da curva.

**Decisão:** 
- **R006:** Após a posição do mínimo global (nova métrica `indice_minimo_global`), calcular `np.diff(rates[indice_minimo_global:])` e verificar se ≥80% são positivos.
- **R013:** Calcular `np.diff(rates)` da curva inteira e verificar se ≥90% possuem o mesmo sinal (todos positivos ou todos negativos).

### D4: Nova métrica — `indice_minimo_global`

Para suportar R006 corrigido, `DetailedMetrics` ganha o campo `indice_minimo_global: int` com o índice (0-based) onde ocorre a taxa mínima da curva. Em caso de empate, usa o primeiro índice.

### D5: R010 — Threshold relativo à amplitude

**Problema:** A especificação menciona "percentil definido pelo sistema", mas o threshold atual `suavidade_percentil = 0.05` é absoluto. Uma oscilação de 0.05 é insignificante em curva com amplitude 5.0, mas enorme em curva com amplitude 0.10.

**Decisão:** Normalizar: `indice_suavidade_relativo = indice_suavidade / amplitude`. Se `amplitude == 0` (curva perfeitamente plana), a suavidade também é 0, então a curva é considerada suave por definição. O threshold é renomeado de `suavidade_percentil` para `suavidade_relativo` com valor default calibrado (ex: 0.01).

**Alternativa considerada:** Percentil contra distribuição histórica. Rejeitada porque exigiria acesso a dados históricos no escopo de uma chamada `analyze()`, violando o princípio de função pura.

### D6: Classificação dual por direção

**Problema:** A faixa 5–7 é rotulada "Curva estruturalmente ascendente", mas curvas descendentes também podem atingir score 5–7 via R002 (+2) + outras regras.

**Decisão:** `_classificar_score()` agora recebe também a direção da tendência (`"asc"`, `"desc"`, `"plana"`), determinada por qual regra de tendência ativou (R001, R002 ou R003). Labels são espelhados:

| Score | Ascendente                         | Descendente                         | Plana                  |
|-------|------------------------------------|-------------------------------------|------------------------|
| 0–2   | Mercado estável                    | Mercado estável                     | Mercado estável        |
| 3–4   | Mudança moderada                   | Mudança moderada                    | Mudança moderada       |
| 5–7   | Curva estruturalmente ascendente   | Curva estruturalmente invertida     | Curva estruturada      |
| 8–10  | Reprecificação ascendente relevante| Reprecificação descendente relevante| Reprecificação relevante|
| 11+   | Mudança estrutural asc. expressiva | Mudança estrutural desc. expressiva | Mudança estrutural expressiva |

### D7: Novas regras R015–R020

Cada regra segue o mesmo padrão das existentes: função pura recebendo `DetailedMetrics` + `AnalysisThresholds`, retornando `RuleResult`.

| Regra | Nome                  | Métrica usada          | Score | Bloco       |
|-------|-----------------------|------------------------|-------|-------------|
| R015  | Oscilação Elevada     | `qtd_mudancas / n`     | −1    | geometrica  |
| R016  | Amplitude Reduzida    | `amplitude`            | 0     | geometrica  |
| R017  | Amplitude Elevada     | `amplitude`            | +1    | geometrica  |
| R018  | Curva Invertida       | `curto.delta`, `longo.delta` | +2 | geometrica |
| R019  | Achamento/Empinamento | `curto.delta`, `longo.delta` | +1 | geometrica |
| R020  | Formato-S             | `qtd_inflexoes`        | +1    | geometrica  |

**R015** usa `qtd_mudancas` (trocas de sinal da primeira derivada), métrica já calculada em `_metrics.py` mas nunca usada em regra.

**R016/R017** detectam amplitudes extremas. Curva com amplitude < 0.10 indica forte consenso; amplitude > 1.50 indica dispersão elevada.

**R018** detecta torção: segmento curto sobe (`delta > +threshold`) enquanto o longo desce (`delta < -threshold`), configurando uma inversão localizada mesmo que a tendência global (R002) não dispare.

**R019** compara magnitudes: se `curto.delta > longo.delta * 2` → achatamento (flattening); se `longo.delta > curto.delta * 2` → empinamento (steepening). Só ativa quando ambos os segmentos têm o mesmo sinal de delta.

**R020** ativa quando `qtd_inflexoes >= 2`, indicando formato sigmoide (múltiplas mudanças de concavidade).

### D8: Thresholds adicionais

Novos campos em `AnalysisThresholds`:

| Campo                      | Default | Uso     |
|----------------------------|---------|---------|
| `suavidade_relativo`       | 0.01    | R010    |
| `oscilacao_ratio`          | 0.30    | R015    |
| `amplitude_reduzida`       | 0.10    | R016    |
| `amplitude_elevada`        | 1.50    | R017    |
| `curva_invertida_delta`    | 0.10    | R018    |
| `steepening_ratio`         | 2.0     | R019    |

Campos removidos/renomeados:
- `suavidade_percentil` → removido, substituído por `suavidade_relativo`

## Risks / Trade-offs

- **R010 normalizado:** Com amplitude pequena, o índice relativo pode ser alto mesmo com oscilações absolutas baixas. Mitigação: threshold `suavidade_relativo` é configurável; default 0.01 calibrado para dados reais da B3.
- **R006/R013 corrigidos:** Curvas que antes ativavam essas regras incorretamente podem deixar de ativar, alterando scores. Mitigação: documentado como breaking change; testes unitários cobrem os novos comportamentos.
- **R015 pode sobrepor R011:** Ambas detectam irregularidade, mas por ângulos diferentes (R011 = magnitude, R015 = frequência). Overlap é aceitável — reforça o sinal.
- **R018 pode sobrepor R002:** R018 é mais específico (torção entre segmentos), R002 é global. Ambas podem ativar simultaneamente sem contradição.
- **Expansão de 14 para 20 regras:** Aumenta a complexidade de manutenção, mas cada regra é uma função pura isolada, sem efeitos colaterais.

## Open Questions

- Os thresholds default (`suavidade_relativo=0.01`, `amplitude_reduzida=0.10`, `amplitude_elevada=1.50`, `oscilacao_ratio=0.30`) precisam de calibração empírica com dados reais da B3 após implementação.
