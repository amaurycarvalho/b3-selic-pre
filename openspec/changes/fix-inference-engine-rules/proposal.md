## Why

O motor de inferência implementado em `application/analyze/` contém bugs lógicos em 4 regras (R004, R005, R006, R013) que distorcem a ativação de inferências e o score final. Além disso, a classificação por score ignora a direção da tendência (ascendente/descendente), métricas são calculadas sem uso em regra alguma, e o threshold de suavidade (R010) é absoluto quando deveria ser relativo à amplitude da curva. Por fim, a especificação original prevê 14 regras, mas há espaço para novas regras que capturem fenômenos economicamente relevantes (oscilação, amplitude, curvatura, relação entre segmentos) sem as 4 regras com bugs comprometem a confiabilidade do relatório.

## What Changes

- **Corrigir R004 (Vale)**: cálculo da posição relativa do mínimo (usava `len(range(...))` em vez do total de pontos) e remover `max_day=756` hardcoded, usando `max_du` real dos dados.
- **Corrigir R005 (Pico)**: implementar verificação real de "queda contínua" após o pico (>=80% dos deltas negativos), em vez de apenas checar `longo.slope < 0`.
- **Corrigir R006 (Recuperação Sustentada)**: usar deltas ponto-a-ponto após o mínimo global, em vez de deltas entre segmentos.
- **Corrigir R013 (Movimento Monótono)**: usar deltas ponto-a-ponto da curva inteira (conforme spec), em vez de deltas entre segmentos.
- **Adicionar métrica `indice_minimo_global`** ao `DetailedMetrics` para suportar R006 corrigido.
- **Tornar R010 (Curva Suave) relativo à amplitude**: `IndiceSuavidade / Amplitude` em vez de threshold absoluto, capturando o conceito de "percentil" da especificação.
- **Classificação dual (ascendente/descendente)**: labels de classificação de score agora refletem a direção da tendência global detectada (R001, R002 ou R003).
- **Adicionar 6 novas regras (R015–R020)**:
  - R015: Oscilação Elevada — usa `qtd_mudancas` (métrica já calculada e não utilizada)
  - R016: Amplitude Reduzida — spread total muito baixo indica consenso
  - R017: Amplitude Elevada — spread total muito alto indica dispersão
  - R018: Curva Invertida — segmento curto sobe e longo desce (torção)
  - R019: Achamento/Empinamento — relação entre deltas de segmentos
  - R020: Formato-S — múltiplas inflexões (>=2)
- **Adicionar thresholds** para as novas regras em `AnalysisThresholds`.

## Capabilities

### New Capabilities

*(Nenhuma — as novas regras estendem a capacidade existente sem criar nova.)*

### Modified Capabilities

- `auto-analysis`: Requisitos de extração de métricas, avaliação de regras, cálculo de score e classificação são alterados para corrigir bugs, adicionar regras R015–R020, normalizar R010 por amplitude, e introduzir classificação dual por direção de tendência.

## Impact

- **Arquivos modificados**:
  - `src/b3_selic_pre/application/analyze/_metrics.py` — adicionar `indice_minimo_global` ao `DetailedMetrics`
  - `src/b3_selic_pre/application/analyze/_rules.py` — corrigir R004/R005/R006/R013; adicionar R015–R020; tornar R010 relativo
  - `src/b3_selic_pre/application/analyze/_thresholds.py` — adicionar thresholds para novas regras; renomear `suavidade_percentil` para `suavidade_relativo`
  - `src/b3_selic_pre/application/analyze/__init__.py` — classificação dual por direção; integrar novas regras
  - `tests/test_analyze.py` — testes para correções e novas regras
- **Nenhuma dependência externa nova**.
- **Nenhuma mudança na GUI**, CLI, ou formato de exportação.
- **Breaking**: curvas que antes ativavam R004/R006/R013 incorretamente podem mudar de score; classificação agora varia conforme direção (asc/desc).
