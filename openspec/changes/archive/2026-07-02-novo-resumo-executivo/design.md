## Context

O módulo `application/analyze/` atualmente implementa um classificador geométrico de curvas com 28 regras, 30+ features e 28 parâmetros de configuração. A nova especificação substitui isso por um **analisador de regime macroeconômico** baseado em 9 indicadores calculados diretamente dos vértices da curva, parametrizados por inflação esperada e thresholds configuráveis.

A GUI (`presentation/gui.py`) exibe o resultado da análise num sidebar `tk.Text` com tags de formatação. O `settings.py` persiste configurações em JSON em `~/.config/b3-selic-pre/settings.json`.

## Goals / Non-Goals

**Goals:**
- Substituir completamente o motor de análise da curva pelo Resumo Executivo
- Implementar 9 indicadores: taxa curta, taxa longa, inclinação, prêmio de prazo, nível nominal, juro real, grau de restrição, estabilidade das expectativas, steepening/flattening
- Gerar texto automático em 5 blocos concatenados
- Configurar parâmetros via `settings.json` (chaves `curva_juros` e `curva_evolucao`)
- Adaptar o sidebar da GUI ao novo layout (sem bordas ASCII, com tags tk.Text)
- Implementar fallback para estabilidade e steepening quando não há histórico suficiente
- Remover todo o código e testes do motor antigo

**Non-Goals:**
- Análise com evolução da curva (será tratada em especificação técnica própria)
- Suporte a outros idiomas além do português
- Exibição do Resumo Executivo no CLI

## Decisions

### 1. Formato de configuração: JSON unificado no settings.json
- **Decisão**: Manter todos os parâmetros no `settings.json` existente, sob as chaves `curva_juros` e `curva_evolucao`
- **Alternativa considerada**: INI separado com configparser (rejeitado: evita dependência extra, unifica persistência, compatibilidade retroativa)
- **Consequência**: Leitores antigos do JSON ignoram as novas chaves silenciosamente

### 2. Estrutura do módulo de análise: 4 arquivos
- `__init__.py` — fachada pública `analyze()`
- `_resumo.py` — lógica central: extração de indicadores e classificação
- `_texto.py` — geração do texto dos 5 blocos + mensagem final
- `_config.py` — dataclass `CurvaJurosConfig` com valores padrão, populada a partir do settings.json
- **Alternativa considerada**: Manter estrutura atual com adaptações (rejeitado: complexidade residual desnecessária)

### 3. Remoção completa do motor antigo
- Os 8 arquivos do motor antigo são removidos (`_metrics.py`, `_features.py`, `_classifier.py`, `_registry.py`, `_scoring.py`, `_templates.py`, `_report.py`, `_metrics_evolution.py`)
- `AnalysisReport` migra para `_resumo.py` (a definição da dataclass permanece, mas simplificada)
- `ENGINE_VERSION` e `RULESET_VERSION` são removidos

### 4. Cálculo dos indicadores (matemática)
Todos os indicadores são calculados a partir dos rates extraídos dos `RateRecord`:
- `taxa_curta` = rates[0] (primeiro vértice)
- `taxa_longa` = rates[-1] (último vértice)
- `inclinacao_bps` = (taxa_longa - taxa_curta) * 100
- `juro_real` = taxa_curta - expected_inflation
- Classificações por faixas configuráveis (nominal, real, prêmio de prazo)

### 4a. Classificação da Inclinação da Curva
A inclinação é classificada em 5 categorias com base em thresholds fixos (não configuráveis):
- |slope| < 10 bps → "Quase Plana"
- 10-30 bps → "Muito Plana"
- 30-60 bps → "Plana"
- 60-100 bps → "Moderadamente Inclinada"
- > 100 bps → "Muito Inclinada"
- Decisão: Usar faixas fixas (não configuráveis no settings.json) por se basearem na prática brasileira de análise de curva de juros, onde os thresholds são consensuais.

### 5. Estabilidade das Expectativas
- Número de curvas: `stability_window = 4` (já carregadas no modo evolução)
- Fallback `default`: assume `default_mean_deviation_bps = 15` (→ "Média")
- Fallback `auto`: estima `desvio = |slope_bps| / 5`
- Fallback `unavailable`: oculta a linha (se stability_fallback = unavailable)
- Faixas: <5 → Muito Alta, <10 → Alta, <20 → Média, <35 → Baixa, >=35 → Muito Baixa
- Quando o valor é estimado (fallback), o display mostra "(estimado por ausência de histórico)" em vez do valor bruto em bps, para que o usuário saiba que não foi observado

### 6. Steepening/Flattening
- `ΔSlope = inclinacao_atual - inclinacao_anterior`
- Sem curva anterior: fallback `unavailable` (oculta linha "Última Mudança") — este é o comportamento padrão
- Fallback `default`: `estimated_delta_slope_bps = 15`
- Fallback `auto`: `ΔSlope = |slope_bps| / 5`
- Magnitude: <10 → Leve, <20 → Moderado, <40 → Forte, >=40 → Muito Forte
- Direção: ΔSlope > 0 → Steepening (▲), ΔSlope < 0 → Flattening (▼)
- O valor padrão de `steepening_fallback` no settings.json é `"unavailable"`; o usuário deve explicitamente configurar `"default"` ou `"auto"` para ativar

### 7. Layout no sidebar
- `tk.Text` com tags: "header" (bold), "positive" (green), "negative" (red)
- Sem bordas ASCII (remove `┌──┐` do layout original)
- 7 linhas nomeadas + mensagem final em bloco separado
- Linha "Última Mudança" omitida se steepening_fallback = "unavailable" e sem histórico

### 8. Testes
- `tests/test_analyze.py` removido por completo
- Novos testes em `tests/test_novo_resumo.py` cobrindo: cálculo dos indicadores, classificação por faixas, texto gerado, fallbacks, integração com analyze()

## Risks / Trade-offs

- **[Remoção do motor antigo]** Se a especificação futura de evolução precisar de métricas geométricas, elas terão que ser reimplementadas → Mitigação: a especificação futura definirá seus próprios indicadores
- **[Dependência de histórico]** Estabilidade e steepening dependem de dados históricos já carregados (5 curvas do modo evolução) → Mitigação: fallbacks configuráveis garantem funcionamento mesmo sem histórico
- **[settings.json compartilhado]** Se o arquivo for corrompido, o sistema perde todos os parâmetros → Mitigação: `CurvaJurosConfig` aplica valores padrão se as chaves não existirem; settings.py já trata JSON mal formado
- **[tk.Text limitado]** O layout desejado (7 linhas nomeadas + bullets) é bem servido por tk.Text, mas formatação complexa (tabelas, alinhamento) seria difícil → Não é um problema porque o design explicitamente evita bordas e tabelas
