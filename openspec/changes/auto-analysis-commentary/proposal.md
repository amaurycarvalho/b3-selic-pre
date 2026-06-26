## Why

O programa exibe gráficos de taxas SELIC Pré, mas não oferece nenhuma interpretação textual dos dados. O usuário precisa analisar visualmente a curva, o envelope consolidado e a evolução histórica para extrair conclusões — o que exige conhecimento técnico e expõe a interpretações subjetivas. Um motor de inferência baseado em regras, 100% determinístico, pode gerar automaticamente um relatório em linguagem natural, transformando métricas objetivas em insights imediatos. Isso torna a ferramenta mais acessível e reduz o viés de interpretação.

## What Changes

- Adicionar módulo `analyze.py` com motor de inferência baseado em regras, composto por 11 camadas de análise:
  1. Forma da curva (ascendente/descendente/plana)
  2. Inclinação (regressão linear)
  3. Convexidade (regressão quadrática)
  4. Volatilidade (desvio padrão das diferenças sucessivas)
  5. Oscilações (contagem de inversões de direção)
  6. Envelope consolidado (spread médio e comportamento)
  7. Evolução consolidada (tendência das 5 datas)
  8. Difusão do movimento (quantos anos subiram/desceram)
  9. Rotação da curva (Bear/Bull Steepening/Flattening)
  10. Intensidade do movimento (delta médio absoluto)
  11. Score agregado (peso das regras ativadas)
- Adicionar painel lateral direito collapsível na GUI (`SelicPreApp`) para exibir o relatório textual
- Integrar a análise no fluxo de redraw do gráfico (`_redraw_chart`), atualizando o relatório automaticamente a cada nova visualização
- Thresholds ajustáveis por parâmetro nas funções do motor

## Capabilities

### New Capabilities
- `auto-analysis`: Motor de inferência rule-based que extrai métricas dos dados de taxa, aplica regras e gera relatório textual em linguagem natural, exibido em painel lateral collapsível na GUI

### Modified Capabilities

*(Nenhuma — a análise é uma nova capacidade independente, sem alterar requisitos existentes.)*

## Impact

- Arquivo novo: `b3_selic_pre/analyze.py` (módulo do motor de inferência)
- Arquivo modificado: `b3_selic_pre.py` (adição do painel lateral e integração no `_redraw_chart`)
- Nenhuma dependência externa nova (numpy já é dependência transitória do matplotlib; pode ser explicitada no `requirements.txt`)
- Nenhuma mudança na API pública, CLI, ou formato de exportação de dados
- Nenhuma mudança nos specs existentes
