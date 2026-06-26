## Why

O motor de inferência atual avalia 20 regras como um conjunto plano: todas competem no mesmo nível, sem hierarquia, sem exclusão mútua entre conceitos contraditórios. Isso produz relatórios com afirmações inconsistentes (ex: "curva plana" + "curva com vale" + "formato sigmoide" simultaneamente). Além disso, a direção da tendência usa `(final - inicial) / amplitude` — um proxy frágil que subestima tendências quando a curva tem vale ou pico inicial. A correção exige substituir a arquitetura plana por uma hierarquia de 5 níveis que espelha como um analista humano interpreta uma curva de juros: primeiro a forma geral, depois características estruturais, depois qualidade e intensidade.

## What Changes

- **Substituir a arquitetura plana de 20 regras por um motor hierárquico de 5 níveis**:
  - **Nível 1 — Classificação Primária** (exclusiva): OSCILANTE > VALE > PICO > SIGMOIDE > ASCENDENTE > DESCENDENTE > PLANA. Determinada por `slope_global` (regressão linear), amplitude, extremos locais, e contagem de inflexões com segmentos mínimos.
  - **Nível 2 — Características Estruturais** (múltiplas, gated por classe primária): RECUPERAÇÃO, ACHATAMENTO, EMPINAMENTO, TORÇÃO, MONOTONIA, MUDANÇA ESTRUTURAL.
  - **Nível 3 — Qualidade da Curva** (múltiplas, independentes): SUAVE, SERRILHADA, CONSENSO, DISPERSÃO.
  - **Nível 4 — Intensidade** (score ponderado + confiança por nível): pesos diferenciados (N1×3, N2×2, N3×1), confiança como razão de regras satisfeitas por nível.
  - **Nível 5 — Relatório**: separação entre FORMA (diagnóstico geométrico) e INTENSIDADE (magnitude do movimento).
- **Adicionar `slope_global` ao `DetailedMetrics`**: coeficiente angular da regressão linear sobre toda a curva, substituindo `IndiceTendencia` como métrica de direção.
- **Endurecer condições de PLANA**: requer `amplitude < 0.10` **E** `|delta_final| < 0.05` **E** `|slope_global| < limiar` (tripla condição).
- **Endurecer R012 (Mudança Estrutural)**: exige diferença entre slopes > 30%, não apenas 1 inflexão.
- **Endurecer R020 (Formato-S → SIGMOIDE)**: exige ≥ 2 inflexões com cada trecho > 15% da curva.
- **Remover `IndiceTendencia`** do `DetailedMetrics` (substituído por `slope_global`).
- **Reescrever `_rules.py`** como `_classifier.py` com a nova arquitetura hierárquica.
- **Remover `_thresholds.py`** e integrar thresholds diretamente no classifier (thresholds específicos por nível).

## Capabilities

### New Capabilities

*(Nenhuma — reestruturação de capacidade existente sem criar nova.)*

### Modified Capabilities

- `auto-analysis`: Arquitetura do motor de inferência completamente reestruturada de avaliação plana de regras (R001–R020) para classificação hierárquica de 5 níveis com classe primária exclusiva, gating de regras estruturais, score ponderado e métrica de confiança.

## Impact

- **Arquivos reescritos**:
  - `src/b3_selic_pre/application/analyze/_rules.py` → substituído por `_classifier.py` (nova arquitetura)
  - `src/b3_selic_pre/application/analyze/_thresholds.py` → removido (thresholds integrados no classifier)
- **Arquivos modificados**:
  - `src/b3_selic_pre/application/analyze/_metrics.py` — adicionar `slope_global`, remover `indice_tendencia`
  - `src/b3_selic_pre/application/analyze/__init__.py` — integrar novo classifier, score ponderado, confiança
  - `src/b3_selic_pre/application/analyze/_report.py` — novo formato de relatório (FORMA + INTENSIDADE)
  - `tests/test_analyze.py` — reescrito para nova arquitetura
- **Nenhuma dependência externa nova**.
- **Nenhuma mudança na GUI, CLI, ou formato de exportação**.
- **BREAKING**: API do `DetailedMetrics` muda (adiciona `slope_global`, remove `indice_tendencia`). API do facade `analyze()` mantém contratos. Relatório muda de estrutura.
