## Why

O programa exibe gráficos de taxas SELIC Pré, mas não oferece nenhuma interpretação textual dos dados. O usuário precisa analisar visualmente a curva, o envelope consolidado e a evolução histórica para extrair conclusões — o que exige conhecimento técnico e expõe a interpretações subjetivas. Um motor de inferência baseado em regras, 100% determinístico, pode gerar automaticamente um relatório em linguagem natural, transformando métricas objetivas em insights imediatos. Isso torna a ferramenta mais acessível e reduz o viés de interpretação.

## What Changes

- Adicionar subpacote `application/analyze/` com motor de inferência baseado em regras, composto por 14 regras (R001–R014):
  1. R001: Tendência Global Ascendente
  2. R002: Tendência Global Descendente
  3. R003: Curva Plana
  4. R004: Vale
  5. R005: Pico
  6. R006: Recuperação Sustentada
  7. R007: Segmento Curto
  8. R008: Segmento Médio
  9. R009: Segmento Longo
  10. R010: Curva Suave
  11. R011: Curva Serrilhada
  12. R012: Mudança Estrutural
  13. R013: Movimento Monótono
  14. R014: Curva em Recuperação
- Extração de métricas geométricas: Índice de Tendência, segmentação da curva (curto/médio/longo), suavidade, extremos locais, mudanças de inclinação e pontos de inflexão
- Score agregado com pesos (+2, +1, 0, −1) classificado em 5 níveis (estável a mudança estrutural expressiva)
- Relatório estruturado em 4 blocos: Tendência Geral → Forma Geométrica → Segmentos → Conclusão
- Adicionar painel lateral direito collapsível na GUI (`SelicPreApp` em `presentation/gui.py`) para exibir o relatório textual
- Checkbox "Análise" no bottom_frame para alternar visibilidade do painel
- Integrar a análise no fluxo de redraw do gráfico (`_redraw_chart`), atualizando o relatório automaticamente a cada nova visualização
- Thresholds ajustáveis por parâmetro nas funções do motor

## Capabilities

### New Capabilities
- `auto-analysis`: Motor de inferência rule-based que extrai métricas geométricas da curva de juros, aplica 14 regras determinísticas e gera relatório textual em linguagem natural com score, exibido em painel lateral collapsível na GUI

### Modified Capabilities

*(Nenhuma — a análise é uma nova capacidade independente, sem alterar requisitos existentes.)*

## Impact

- Pacote novo: `src/b3_selic_pre/application/analyze/` com `__init__.py`, `_thresholds.py`, `_metrics.py`, `_rules.py`, `_report.py`
- Arquivo modificado: `src/b3_selic_pre/presentation/gui.py` (adição do painel lateral, checkbox e integração no `_redraw_chart`)
- Nenhuma dependência externa nova (numpy já é dependência transitória do matplotlib; explicitada no `pyproject.toml`)
- Nenhuma mudança na API pública, CLI, ou formato de exportação de dados
- Nenhuma mudança nos specs existentes
