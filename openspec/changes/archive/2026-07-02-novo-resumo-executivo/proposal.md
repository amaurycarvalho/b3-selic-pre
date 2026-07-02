## Why

O atual motor de análise de curva (`application/analyze/`) classifica a geometria da curva (ascendente, vale, pico, plana, oscilante) usando 28 regras heurísticas e 30+ features extraídas dos dados. Essa abordagem não responde às perguntas que um investidor realmente tem: "O que o mercado espera para os juros?" e "Quão restritiva é a política monetária?". Além disso, o motor atual é complexo (9 arquivos, ~650 linhas) e de difícil manutenção.

## What Changes

- **BREAKING**: Substitui completamente o módulo `application/analyze/` por uma nova implementação baseada no **Resumo Executivo da Curva de Juros**
- Remove 8 arquivos do motor antigo (`_metrics.py`, `_features.py`, `_classifier.py`, `_registry.py`, `_scoring.py`, `_templates.py`, `_report.py`, `_metrics_evolution.py`)
- Cria 4 novos arquivos no lugar: `__init__.py`, `_resumo.py`, `_texto.py`, `_config.py`
- Adiciona novos parâmetros de configuração no `settings.json` sob as chaves `curva_juros` e `curva_evolucao`
- Atualiza o sidebar da GUI para exibir o novo layout do Resumo Executivo
- Remove a classe de análise para os modos "consolidado" e "evolução" (placeholders), que agora são cobertos pelo novo resumo
- Remove todos os testes antigos do motor de análise (`test_analyze.py`)
- **BREAKING**: Altera o contrato da função `analyze()` — agora recebe parâmetros de configuração adicionais e retorna um `AnalysisReport` com estrutura diferente

## Capabilities

### New Capabilities
- `novo-resumo-executivo`: Cálculo dos indicadores do Resumo Executivo (taxa curta, taxa longa, inclinação, prêmio de prazo, nível nominal, juro real, grau de restrição, estabilidade das expectativas, steepening/flattening) e geração automática do texto-resumo em 5 blocos concatenados

### Modified Capabilities
- `analysis-panel`: O layout do sidebar e a formatação do texto de análise são atualizados para refletir o novo formato do Resumo Executivo (sem bordas ASCII, com tags tk.Text para header/positive/negative, 7 linhas nomeadas + mensagem final)

## Impact

- `src/b3_selic_pre/application/analyze/` — reestruturação completa (remove 8 arquivos, cria 4)
- `src/b3_selic_pre/presentation/settings.py` — novos parâmetros de configuração
- `src/b3_selic_pre/presentation/gui.py` — atualização do `_update_analysis()` e formatação do sidebar
- `src/b3_selic_pre/application/analyze/__init__.py` — novo contrato da função `analyze()`
- `tests/test_analyze.py` — removido (testes do motor antigo)
- `openspec/specs/analysis-panel/spec.md` — atualizado com novos requisitos de formatação
