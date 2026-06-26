## Objetivo

Gerar automaticamente um relatório textual em linguagem natural que interpreta a geometria da curva SELIC Pré para qualquer modo de visualização (raw, consolidado, evolução). O relatório é 100% determinístico, baseado em regras objetivas e métricas geométricas, sem uso de IA ou heurísticas subjetivas.

## Comportamento

### 1. Entrada

A função `analyze()` recebe:
- `view_mode: str` — `"raw"`, `"consolidado"` ou `"evolucao"` (default: `"raw"`)
- `taxas: list[float]` — vetor de taxas (obrigatório para raw)
- `opcoes: dict` — dicionário opcional com thresholds customizados

Para `view_mode = "raw"`, o motor extrai métricas e aplica as 14 regras. Para `"consolidado"` e `"evolucao"`, retorna placeholder `"não implementada"` até que regras específicas sejam desenvolvidas nesses modos.

### 2. Métricas Extraídas

Para o modo `"raw"`, as seguintes métricas são calculadas:

| Métrica                    | Descrição                                                     |
|----------------------------|---------------------------------------------------------------|
| `indice_tendencia`         | Diferença percentual entre último e primeiro ponto (normalizada) |
| `segmentos`                | 3 segmentos (curto, médio, longo) com variação percentual     |
| `indice_suavidade`         | Desvio padrão das diferenças consecutivas normalizado          |
| `extremos`                 | Lista de máximos e mínimos locais (primeiro/último excluídos) |
| `mudancas_inclinacao`      | Pontos onde a inclinação muda de sinal                        |
| `pontos_inflexao`          | Pontos onde a concavidade muda                                |

### 3. Regras (14 Regras)

Cada regra retorna `RuleResult(rule_id, inference, score, activated, evidence)`.

| ID    | Inferência              | Condição                                                      | Score |
|-------|-------------------------|---------------------------------------------------------------|-------|
| R001  | tendencia_global_asc    | `indice_tendencia > threshold.asc` (≥ +20%)                   | +2    |
| R002  | tendencia_global_desc   | `indice_tendencia < threshold.desc` (≤ −20%)                  | −1    |
| R003  | curva_plana             | `\|indice_tendencia\| < threshold.plano` (< 5%)                | −1    |
| R004  | vale                    | mínimo local na primeira metade                               | +1    |
| R005  | pico                    | máximo local na segunda metade                                | +1    |
| R006  | recuperacao_sustentada  | vale presente + segmento longo ascendente                     | +2    |
| R007  | segmento_curto          | segmento curto com variação > delta_relevante                 | +1    |
| R008  | segmento_medio          | segmento médio com variação > delta_relevante                 | +1    |
| R009  | segmento_longo          | segmento longo com variação > delta_relevante                 | +1    |
| R010  | curva_suave             | `indice_suavidade < suavidade_suave`                          | −1    |
| R011  | curva_serrilhada        | `indice_suavidade > suavidade_serrilhada`                     | +1    |
| R012  | mudanca_estrutural      | mudança de inclinação com variação > mudanca_estrutural_min   | +1    |
| R013  | movimento_monotono      | sem mudanças de inclinação e sem pontos de inflexão           | −1    |
| R014  | curva_em_recuperacao    | vale na primeira metade + recuperação no segmento longo       | +2    |

### 4. Score Agregado

Soma aritmética de todos os scores ativados:

| Score  | Classificação                     |
|--------|-----------------------------------|
| 0–2    | Mercado estável                   |
| 3–4    | Mudança moderada                  |
| 5–7    | Curva estruturalmente ascendente  |
| 8–10   | Reprecificação relevante          |
| 11+    | Mudança estrutural expressiva     |

### 5. Relatório

O relatório possui 4 blocos fixos, nesta ordem:

1. **Tendência Geral** — mostra as regras R001/R002/R003 ativadas
2. **Forma Geométrica** — mostra R004/R005/R010/R011/R012/R013 ativadas
3. **Segmentos** — mostra R006/R007/R008/R009/R014 ativadas
4. **Conclusão** — score total e classificação textual

Cada bloco lista apenas as regras que foram ativadas (`activated = True`), com o texto de `evidence`.

O relatório começa com um cabeçalho: `Análise - Score: {score} | {classificação}`.

### 6. View Mode Routing

| view_mode    | Comportamento                        |
|--------------|--------------------------------------|
| `"raw"`      | Aplica regras R001–R014              |
| `"consolidado"`| Placeholder: "não implementada"    |
| `"evolucao"` | Placeholder: "não implementada"      |

### 7. GUI Integration

- Painel lateral direito exibindo o relatório textual
- Checkbox "Análise" no bottom_frame alterna visibilidade
- Conteúdo atualizado automaticamente no redraw
- Placeholder para modos não implementados

### 8. Testes

Testes devem cobrir:
- Extração de métricas com dados sintéticos (reta ascendente, reta descendente, senoide, plana)
- Cada regra individual com dados que ativam e não ativam a regra
- Limite entre classifications de score
- Placeholder para consolidado/evolucao
- Smoke test do facade

### 9. Exemplo

**Entrada:** `taxas = [10.0, 10.2, 10.5, 10.3, 10.8, 11.0, 11.2, 11.5, 11.3, 11.8]` (tendência ascendente)

**Saída esperada (resumo):**
- R001 ativado: "Tendência global ascendente" (+2)
- Score total: 2–7 (dependendo de outras regras)
- Classificação: "Mudança moderada" ou superior
- Relatório com 4 blocos, apenas regras ativadas listadas
