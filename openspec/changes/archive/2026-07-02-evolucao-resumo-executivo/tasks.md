## 1. Configuração (estender _config.py)

- [x] 1.1 Criar dataclass `EvolutionConfig` com parâmetros: movement_threshold_bps, steepening_threshold_bps, faixas de intensidade (very_weak_max, weak_max, moderate_max, strong_max), faixas de Δ política monetária (highly_restrictive_min, slightly_restrictive_min, neutral_max, slightly_loose_max), faixas de Δ prêmio de prazo (significantly_increased_min, increased_min, neutral_max, decreased_min)
- [x] 1.2 Adicionar campo `evolucao: EvolutionConfig` à dataclass `CurvaJurosConfig`
- [x] 1.3 Atualizar `from_settings()` para carregar a sub-chave `curva_evolucao` do settings.json e popular `EvolutionConfig`

## 2. Lógica Central (_evolucao.py)

- [x] 2.1 Implementar função `extrair_deltas(current_records, previous_records)` que retorna ΔCurto, ΔLongo, ΔSlope, ΔReal em bps
- [x] 2.2 Implementar função `classificar_movimento(delta_short, delta_long, config)` — Bear/Bull/Twist/Estável com threshold suppression
- [x] 2.3 Implementar função `classificar_slope_movement(delta_slope, config)` — Steepening/Flattening/Parallel Shift
- [x] 2.4 Implementar função `classificar_regime(movimento, slope_movement)` — combina movimento + inclinação nos 8 regimes possíveis
- [x] 2.5 Implementar função `classificar_intensidade(delta_short, delta_long, config)` — 5 faixas de Muito Fraca a Muito Forte
- [x] 2.6 Implementar função `classificar_politica_monetaria(delta_real, config)` — 5 faixas com mensagens
- [x] 2.7 Implementar função `classificar_premio_prazo(delta_slope, config)` — 5 faixas com mensagens
- [x] 2.8 Implementar função `derivar_direcao_geral(regime, intensidade)` — tabela de 6 regras de direção
- [x] 2.9 Implementar dataclass `EvolutionReport` com todos os campos: statements, delta_short_bps, delta_long_bps, delta_slope_bps, delta_real_bps, regime, intensity, monetary_policy_msg, term_premium_msg, direction, market_message
- [x] 2.10 Implementar função `analyze_evolution(current, previous, config=None)` que orquestra todo o pipeline e retorna `EvolutionReport` ou `None` se previous vazio

## 3. Geração de Texto (_texto_evolucao.py)

- [x] 3.1 Implementar função `gerar_texto_regime(regime)` com 7 variações (Bear/Bull Steepening/Flattening, Parallel Shift, Twist, Estável)
- [x] 3.2 Implementar função `gerar_texto_politica(monetary_policy_msg, delta_real)` que adiciona prefixo ▲/▼/→ e formata "+X bps"
- [x] 3.3 Implementar função `gerar_texto_premio(term_premium_msg, delta_slope)` que adiciona prefixo ▲/▼/→
- [x] 3.4 Implementar função `gerar_texto_intensidade(intensidade)` com 5 variações
- [x] 3.5 Implementar função `gerar_texto_direcao(direction)` — retorna a direção como string simples
- [x] 3.6 Implementar função `montar_evolucao_resumo(evolution_report, config)` que monta os 6 blocos + mensagem final em linguagem natural, com versão compacta para regime "Estável"

## 4. Fachada (__init__.py do analyze)

- [x] 4.1 Importar e exportar `analyze_evolution` e `EvolutionReport`
- [x] 4.2 Adicionar ao `__all__` os novos símbolos públicos

## 5. Atualização da GUI (gui.py)

- [x] 5.1 Em `_update_analysis()`, após processar o painel de Curva Atual, verificar se evolution_active está ligado e há historical_data
- [x] 5.2 Identificar a curva anterior (a mais recente antes da atual) de `historical_data`
- [x] 5.3 Chamar `analyze_evolution(current_records, previous_records, config)` se houver curva anterior
- [x] 5.4 Renderizar o sub-painel "Resumo Executivo — Evolução da Curva" com divisor horizontal, usando tags tk.Text "header", "positive", "negative"
- [x] 5.5 Aplicar versão compacta (3 linhas) quando regime for "Estável"
- [x] 5.6 Garantir que o sub-painel seja oculto quando evolution_active = False ou sem curva anterior

## 6. Testes

- [x] 6.1 Criar `tests/test_evolucao_resumo.py` com testes para extração de deltas (curta, longa, slope, real)
- [x] 6.2 Testar classificação de movimento com threshold suppression (Bear, Bull, Twist, Estável)
- [x] 6.3 Testar classificação de regime combinado (8 regimes)
- [x] 6.4 Testar classificação de intensidade (5 faixas)
- [x] 6.5 Testar classificação de política monetária (5 faixas)
- [x] 6.6 Testar classificação de prêmio de prazo (5 faixas)
- [x] 6.7 Testar derivação de direção geral (6 regras)
- [x] 6.8 Testar geração de texto dos 6 blocos + versão compacta
- [x] 6.9 Testar `analyze_evolution()` com previous vazio (retorna None)
- [x] 6.10 Testar integração com configuração customizada
- [x] 6.11 Executar bateria completa: `python -m pytest tests/`
