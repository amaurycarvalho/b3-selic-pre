## 1. Estrutura do módulo analyze

- [ ] 1.1 Criar diretório `b3_selic_pre/` com `__init__.py` vazio
- [ ] 1.2 Criar `b3_selic_pre/_thresholds.py` com dataclass `AnalysisThresholds` e valores default
- [ ] 1.3 Criar `b3_selic_pre/_metrics.py` com funções de extração de métricas (curva detalhada)
- [ ] 1.4 Criar `b3_selic_pre/_metrics_evolution.py` com funções de métricas para modo evolução
- [ ] 1.5 Criar `b3_selic_pre/_rules.py` com definição de todas as regras das 11 camadas
- [ ] 1.6 Criar `b3_selic_pre/_report.py` com composição do relatório final (seções, score)
- [ ] 1.7 Criar `b3_selic_pre/analyze.py` como facade pública

## 2. Métricas do gráfico detalhado

- [ ] 2.1 Implementar `extract_detailed_metrics(records, thresholds)` → `DetailedMetrics`
- [ ] 2.2 Calcular taxa inicial, final, máxima, mínima
- [ ] 2.3 Implementar regressão linear para slope (numpy polyfit degree 1)
- [ ] 2.4 Implementar regressão quadrática para convexidade (numpy polyfit degree 2)
- [ ] 2.5 Calcular desvio padrão das diferenças sucessivas (volatilidade)
- [ ] 2.6 Contar inversões de direção (oscilações)

## 3. Métricas do envelope consolidado

- [ ] 3.1 Implementar `extract_envelope_metrics(records, thresholds)` → `EnvelopeMetrics`
- [ ] 3.2 Calcular spread médio entre min e max por ano
- [ ] 3.3 Detectar tendência do spread (crescente/decrescente ao longo dos anos)

## 4. Métricas da evolução consolidada

- [ ] 4.1 Implementar `extract_evolution_metrics(historical_data)` → `EvolutionMetrics`
- [ ] 4.2 Calcular deltas entre as 5 datas para cada ano
- [ ] 4.3 Detectar tendência (alta contínua, queda contínua, instabilidade)
- [ ] 4.4 Analisar difusão do movimento (quantos anos subiram/desceram)
- [ ] 4.5 Classificar rotação da curva (bear/bull steepening/flattening)
- [ ] 4.6 Calcular intensidade do movimento (delta médio absoluto)

## 5. Regras e textos

- [ ] 5.1 Implementar regra de forma da curva (ascendente/descendente/plana)
- [ ] 5.2 Implementar regra de classificação da inclinação
- [ ] 5.3 Implementar regra de classificação da convexidade
- [ ] 5.4 Implementar regra de classificação da volatilidade
- [ ] 5.5 Implementar regra de oscilações
- [ ] 5.6 Implementar regra de spread do envelope
- [ ] 5.7 Implementar regra de tendência do envelope
- [ ] 5.8 Implementar regra de tendência da evolução
- [ ] 5.9 Implementar regra de difusão do movimento
- [ ] 5.10 Implementar regra de rotação da curva
- [ ] 5.11 Implementar regra de intensidade do movimento
- [ ] 5.12 Implementar regra de score agregado com pesos

## 6. Composição do relatório

- [ ] 6.1 Implementar `build_report(statements, score, score_label)` → `AnalysisReport`
- [ ] 6.2 Organizar statements nas seções: Formato da Curva, Dispersão e Consenso, Evolução Recente, Qualidade do Movimento, Conclusão
- [ ] 6.3 Implementar `format_report(report)` → string formatada com seções e score

## 7. Facade pública

- [ ] 7.1 Implementar `analyze(records, historical_data, view_mode, evolution_active, thresholds=None)` → `AnalysisReport`
- [ ] 7.2 Roteamento: modo detalhado usa métricas detalhadas; consolidado usa envelope; evolution usa evolution
- [ ] 7.3 Caso sem dados retorna `AnalysisReport` vazio

## 8. Painel lateral na GUI

- [ ] 8.1 Adicionar `ttk.PanedWindow` no `SelicPreApp.__init__` separando gráfico (esquerda) e sidebar (direita)
- [ ] 8.2 Criar frame da sidebar com botão toggle (▶/▼ "Análise") e widget `tk.Text` readonly com scrollbar
- [ ] 8.3 Implementar toggle expandir/recolher (largura 0 ↔ ~280px)
- [ ] 8.4 Integrar chamada a `analyze()` no `_redraw_chart` e atualizar o widget de texto
- [ ] 8.5 Atualizar geometria da janela para acomodar sidebar

## 9. Dependências e limpeza

- [ ] 9.1 Adicionar `numpy>=1.20.0` ao `requirements.txt`
- [ ] 9.2 Verificar que `b3_selic_pre/__init__.py` existe
- [ ] 9.3 Rodar testes existentes e garantir que não quebraram

## 10. Testes do motor de análise

- [ ] 10.1 Criar `tests/test_analyze.py`
- [ ] 10.2 Testar extração de métricas com dados sintéticos
- [ ] 10.3 Testar todas as 11 regras individualmente (curva ascendente, descendente, plana, etc.)
- [ ] 10.4 Testar relatório completo com dados simulados
- [ ] 10.5 Testar caso sem dados (lista vazia)
- [ ] 10.6 Testar thresholds customizados
- [ ] 10.7 Testar integração com GUI (sidebar exibe texto)
