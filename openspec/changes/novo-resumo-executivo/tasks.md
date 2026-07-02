## 1. Preparação

- [ ] 1.1 Remover arquivos do motor antigo: `_metrics.py`, `_features.py`, `_classifier.py`, `_registry.py`, `_scoring.py`, `_templates.py`, `_report.py`, `_metrics_evolution.py`
- [ ] 1.2 Remover `tests/test_analyze.py`
- [ ] 1.3 Verificar se há imports do motor antigo em outros módulos (gui.py, cli.py, etc.) e atualizá-los

## 2. Configuração (_config.py)

- [ ] 2.1 Criar dataclass `CurvaJurosConfig` com parâmetros de `curva_juros`: expected_inflation, faixas nominais, faixas de juro real, stability_window, stability_fallback, default_mean_deviation_bps, faixas de estabilidade
- [ ] 2.2 Adicionar parâmetros de `curva_evolucao`: steepening_fallback, estimated_delta_slope_bps, movement_threshold_bps, steepening_threshold_bps, steepening_small/medium/large_bps
- [ ] 2.3 Implementar método `from_settings()` que carrega do settings.json ou aplica defaults
- [ ] 2.4 Atualizar `presentation/settings.py` para reconhecer as novas chaves de configuração

## 3. Lógica Central (_resumo.py)

- [ ] 3.1 Implementar função `extrair_indicadores(records, config)` que calcula: taxa_curta, taxa_longa, inclinacao_bps, juro_real
- [ ] 3.2 Implementar função `classificar_nominal(taxa_curta, config)` com as 5 faixas
- [ ] 3.3 Implementar função `classificar_restricao(juro_real, config)` com as 4 faixas
- [ ] 3.4 Implementar função `classificar_premio(inclinacao_bps, config)` com as 5 faixas
- [ ] 3.5 Implementar função `classificar_inclinacao(inclinacao_bps)` com 3 faixas (Muito Plana/<20, Moderada/20-90, Muito Inclinada/>90)
- [ ] 3.6 Implementar função `calcular_estabilidade(historical_data, records, config)` com fallback default/auto/unavailable
- [ ] 3.7 Implementar função `calcular_steepening(records, historical_data, config)` com fallback unavailable/default/auto, direção e magnitude
- [ ] 3.8 Implementar dataclass `AnalysisReport` simplificada (statements, score=0, score_label="")

## 4. Geração de Texto (_texto.py)

- [ ] 4.1 Implementar função `gerar_texto_nominal(classificacao)` com 5 variações
- [ ] 4.2 Implementar função `gerar_texto_restricao(classificacao)` com 4 variações
- [ ] 4.3 Implementar função `gerar_texto_inclinacao(classificacao)` com 3 variações
- [ ] 4.4 Implementar função `gerar_texto_steepening(direcao, magnitude, delta_bps)` que formata "▲ Steepening Moderado (+18 bps)" ou "▼ Flattening"
- [ ] 4.5 Implementar função `montar_resumo_executivo(indicadores, config)` que monta os 7 blocos + mensagem final, omitindo blocos indisponíveis

## 5. Fachada (__init__.py)

- [ ] 5.1 Reescrever `analyze()` para usar o novo pipeline: extrair_indicadores → classificar → montar_resumo_executivo
- [ ] 5.2 Remover dependências do motor antigo dos imports
- [ ] 5.3 Atualizar `__all__` com os novos tipos exportados

## 6. Atualização da GUI (gui.py)

- [ ] 6.1 Atualizar `_update_analysis()` para formatar o novo `AnalysisReport` com as tags tk.Text apropriadas
- [ ] 6.2 Aplicar tag "positive" (green) para ▲ e "negative" (red) para ▼
- [ ] 6.3 Aplicar tag "header" (bold) para os nomes das seções
- [ ] 6.4 Garantir que linhas indisponíveis (ex: Última Mudança sem steepening) sejam omitidas

## 7. Testes

- [ ] 7.1 Criar `tests/test_novo_resumo.py` com testes para cálculo de indicadores (curta, longa, slope, real)
- [ ] 7.2 Testar classificação por faixas (nominal, restrição, prêmio, inclinação, estabilidade, steepening)
- [ ] 7.3 Testar geração de texto dos 5 blocos + mensagem final
- [ ] 7.4 Testar fallbacks de estabilidade (default, auto, unavailable)
- [ ] 7.5 Testar fallbacks de steepening (default, auto, unavailable)
- [ ] 7.6 Testar integração com `analyze()` (records válidos, vazios, config customizada)
- [ ] 7.7 Executar bateria completa: `python -m pytest tests/`
