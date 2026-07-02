## Why

O painel "Resumo Executivo — Curva Atual" (change `novo-resumo-executivo`) é uma fotografia do mercado: mostra o nível dos juros, o juro real, a inclinação, o prêmio de prazo. Mas investidores também precisam do **filme** — o que mudou desde a última curva? Este painel complementa a fotografia com a evolução, respondendo: "Como mudou a visão do mercado sobre a política monetária desde a última curva?"

## What Changes

- **BREAKING**: Adiciona a seção "Resumo Executivo — Evolução da Curva" ao sidebar da GUI, abaixo do painel de Curva Atual
- Adiciona 2 novos arquivos ao módulo `application/analyze/`: `_evolucao.py` (lógica do painel de evolução) e `_texto_evolucao.py` (geração de texto)
- Adiciona parâmetros de configuração no `settings.json` sob a chave `curva_evolucao`
- Atualiza `__init__.py` do módulo `analyze` para exportar a nova função `analyze_evolution()`
- Adiciona o sub-painel "Evolução da Curva" no sidebar da GUI, visível apenas quando o modo Evolução está ativo (há curva anterior disponível)
- Adiciona a struct `EvolutionReport` com os indicadores calculados e texto gerado

## Capabilities

### New Capabilities
- `evolucao-resumo-executivo`: Cálculo dos indicadores de evolução da curva (ΔCurto, ΔLongo, ΔReal, ΔSlope, regime Bear/Bull Steepening/Flattening, intensidade, ΔPolítica Monetária, ΔPrêmio de Prazo, Direção Geral) e geração automática do texto-resumo da evolução

### Modified Capabilities
- `analysis-panel`: O sidebar da GUI passa a exibir um segundo sub-painel "Resumo Executivo — Evolução da Curva" abaixo do painel de Curva Atual, com formatação rica (tags tk.Text header/positive/negative) e visibilidade condicional ao modo Evolução

## Impact

- `src/b3_selic_pre/application/analyze/` — adiciona `_evolucao.py`, `_texto_evolucao.py`, atualiza `__init__.py` com nova exportação
- `src/b3_selic_pre/presentation/settings.py` — novos parâmetros sob `curva_evolucao`
- `src/b3_selic_pre/presentation/gui.py` — novo sub-painel no sidebar, condicionado ao modo Evolução
- `tests/test_evolucao_resumo.py` — novos testes para o painel de evolução
