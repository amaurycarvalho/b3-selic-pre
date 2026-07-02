## Context

O change `novo-resumo-executivo` substitui o motor de análise geométrica por um painel "Resumo Executivo — Curva Atual" que calcula 9 indicadores de nível (taxa curta, taxa longa, inclinação, prêmio de prazo, nível nominal, juro real, grau de restrição, estabilidade, steepening/flattening). Esse painel é uma **fotografia** do mercado.

Este change adiciona um segundo painel "Resumo Executivo — Evolução da Curva" que calcula indicadores **delta** (Δ) entre a curva atual e a imediatamente anterior — o **filme**. Ambos compartilham o mesmo arquivo de configuração `settings.json` e o mesmo módulo `application/analyze/`.

O segundo painel só faz sentido no modo "Evolução", quando há curva anterior carregada em `historical_data`.

## Goals / Non-Goals

**Goals:**
- Implementar 10 indicadores de evolução: ΔCurto, ΔLongo, ΔReal, ΔSlope, regime composto (Bear/Bull Steepening/Flattening), intensidade, ΔPolítica Monetária, ΔPrêmio de Prazo, Direção Geral
- Gerar texto automático em 6 blocos (regime, política monetária, prêmio de prazo, intensidade, direção geral, mensagem final)
- Configurar parâmetros via `settings.json` (chave `curva_evolucao`)
- Adicionar sub-painel no sidebar da GUI, visível apenas quando modo Evolução está ativo
- Reutilizar `CurvaJurosConfig` do change anterior (estendendo com parâmetros de evolução)
- Implementar threshold suppression: movimentos abaixo de `movement_threshold_bps` são classificados como "Estável"
- Suprimir o painel inteiro se não houver curva anterior disponível

**Non-Goals:**
- Modificar o funcionamento ou layout do painel "Curva Atual"
- Modificar a assinatura de `analyze()` (curva atual)
- Análise com múltiplas curvas históricas além da imediatamente anterior (o modo evolução carrega 5 curvas, mas apenas a adjacente é usada para o delta)
- Suporte a outros idiomas além do português

## Decisions

### 1. Arquitetura: módulo existente vs novo módulo
- **Decisão**: Adicionar 2 arquivos ao módulo `application/analyze/` existente: `_evolucao.py` e `_texto_evolucao.py`. A função pública `analyze_evolution()` é exportada via `__init__.py`.
- **Alternativa considerada**: Novo módulo `application/analyze_evolution/` (rejeitado: os indicadores compartilham tipos como `RateRecord` e `CurvaJurosConfig`; manter no mesmo módulo reduz acoplamento e duplicação)
- **Consequência**: O módulo `analyze/` cresce de 4 para 6 arquivos, mas a separão de responsabilidades permanece clara (nível vs delta)

### 2. Função pública: nova função vs modo em analyze()
- **Decisão**: Criar `analyze_evolution(current: list[RateRecord], previous: list[RateRecord], config: CurvaJurosConfig) -> EvolutionReport`. Função independente, sem modificar `analyze()`.
- **Alternativa considerada**: Adicionar `mode="evolution"` à `analyze()` (rejeitado: mistura responsabilidades; futuras evoluções — ex: comparação com N períodos atrás — seriam mais fáceis com função dedicada)
- **Consequência**: GUI chama duas funções separadas e concatena os resultados no sidebar

### 3. Estrutura de dados: EvolutionReport
- **Decisão**: Dataclass `EvolutionReport` com campos: `statements: list[str]`, `delta_short_bps: float`, `delta_long_bps: float`, `delta_slope_bps: float`, `delta_real_bps: float`, `regime: str`, `intensity: str`, `monetary_policy_msg: str`, `term_premium_msg: str`, `direction: str`, `market_message: str`
- **Alternativa considerada**: Reutilizar `AnalysisReport` com fields opcionais (rejeitado: semântica diferente; `EvolutionReport` é auto-contido e tem campos específicos)
- **Consequência**: GUI precisa tratar dois tipos de relatório, mas a tipagem é explícita e clara

### 4. Configuração: estender CurvaJurosConfig vs dataclass separada
- **Decisão**: Adicionar os parâmetros da evolução (`movement_threshold_bps`, `steepening_threshold_bps`, faixas de intensidade, faixas de Δ política monetária, faixas de Δ prêmio de prazo) à dataclass `CurvaJurosConfig` existente (criada no change anterior), sob um namespace `evolucao: EvolutionConfig`.
- **Alternativa considerada**: Dataclass separada `CurvaEvolucaoConfig` (rejeitado: duplicaria o carregamento do settings.json e o método `from_settings()`; prefere-se composição)
- **Consequência**: `CurvaJurosConfig` ganha um sub-campo `evolucao` do tipo `EvolutionConfig`; `from_settings()` carrega ambos da mesma fonte JSON

### 5. Threshold suppression (sua sugestão adotada)
- O regime só é classificado se `max(|ΔCurto|, |ΔLongo|) >= movement_threshold_bps`. Caso contrário, regime = "Estável" e intensidade = "Muito Fraca".
- As mensagens de texto refletem "A curva permaneceu praticamente estável desde a última atualização."

### 6. Direção Geral
- **Decisão**: Formalizada como indicador derivado do regime composto + intensidade:

| Regime | Intensidade mínima | Direção Geral |
|---|---|---|
| Bear (qualquer) | Fraca | ↑ Revisão Altista dos Juros |
| Bear (qualquer) | Muito Fraca | → Juros Marginalmente Mais Altos |
| Bull (qualquer) | Fraca | ↓ Revisão Baixista dos Juros |
| Bull (qualquer) | Muito Fraca | → Juros Marginalmente Mais Baixos |
| Twist | qualquer | ↕ Movimento Misto na Estrutura |
| Estável | — | → Estrutura a Juros Praticamente Estável |

### 7. Layout no sidebar
- Sub-painel "Resumo Executivo — Evolução da Curva" abaixo do painel de Curva Atual, separado por uma linha horizontal (─╌─╌─) para clara distinção visual
- Mesmas tags tk.Text do painel anterior: "header" (bold), "positive" (green), "negative" (red)
- 6 linhas nomeadas + mensagem final
- Visível apenas quando `evolution_active = True` E há curva anterior disponível
- Se a evolução indicar "Estável" (abaixo do threshold), exibe versão resumida com 3 linhas + mensagem

### 8. Testes
- `tests/test_evolucao_resumo.py` cobrindo: cálculo dos indicadores delta, classificação de regime com/sem threshold, classificação de intensidade, classificação de Δ política monetária, classificação de Δ prêmio de prazo, direção geral, texto gerado, supressão por threshold, integração com `analyze_evolution()`

## Risks / Trade-offs

- **[Dependência do change anterior]** Este change depende do `novo-resumo-executivo` estar implementado primeiro (tipos `CurvaJurosConfig`, `RateRecord`, infraestrutura de configuração) → Mitigação: artifacts deste change especificam os requisitos de forma independente; a implementação só começa após o change anterior ser arquivado
- **[Steepening duplicado]** O painel "Curva Atual" já exibe "Última Mudança" com ΔSlope via steepening. O painel de evolução recalcula o mesmo ΔSlope e o classifica como parte do regime composto → Mitigação: o painel "Curva Atual" tem fallback `unavailable` que oculta a linha "Última Mudança" quando configurado; o usuário pode optar por esconder a redundância
- **[Curva anterior inexistente]** No primeiro uso do modo Evolução, não há curva anterior → Mitigação: `analyze_evolution()` retorna `None` se `previous` for vazia; a GUI oculta o sub-painel neste caso
- **[Precisão dos deltas]** Δ's calculados em bps podem ter ruído de arredondamento dos dados da B3 → Mitigação: `movement_threshold_bps = 5` filtra variações irrelevantes; thresholds configuráveis permitem ajuste
