## Context

O programa atualmente é um arquivo único (`b3_selic_pre.py`, ~1007 linhas) com funções de fetch, formatação, renderização de gráficos (matplotlib) e uma GUI (tkinter). Não há qualquer análise textual dos dados. O usuário vê os gráficos mas precisa interpretá-los manualmente.

A base de dados são `RateRecord` objects (day252, day360, rate) — uma lista plana por data, ou um dict de 5 listas no modo evolução. As funções de consolidação já existem (`consolidate_by_year`, `average_rate_by_year`), mas não há camada de interpretação semântica.

O design precisa:
- Ser 100% determinístico (mesmos dados → mesmo relatório)
- Ser modular (preparando para futuro refactoring para clean architecture)
- Ter thresholds ajustáveis por parâmetro
- Exibir o relatório em painel lateral collapsível

## Goals / Non-Goals

**Goals:**
- Implementar motor de inferência rule-based com 11 camadas de análise
- Exibir relatório textual em painel lateral direito collapsível na GUI
- Integrar automaticamente no ciclo de redraw do gráfico
- Thresholds parametrizáveis (valores default sensíveis, ajustáveis pelo chamador)
- Manter a base de código funcional pura para o motor (sem side effects)
- numpy explicitado como dependência

**Non-Goals:**
- Não alterar a API de linha de comando
- Não alterar formatos de exportação
- Não alterar os gráficos existentes
- Não introduzir ML ou modelos probabilísticos
- Não fazer refactoring para clean architecture (será change futura)

## Decisions

### 1. Módulo separado `analyze.py`
**Decisão:** Criar `b3_selic_pre/analyze.py` com o motor completo.
- `metrics.py` → extração de métricas
- `rules.py` → regras propriamente ditas
- `report.py` → formatação do relatório

Estrutura:
```
b3_selic_pre/
  analyze.py       # facade: analyze(records, historical, view_mode, ...)
  _metrics.py      # funções de extração de métricas
  _rules.py        # definição das regras e thresholds
  _report.py       # composição do relatório final
```

### 2. Dataclasses tipadas para métricas e regras
```python
@dataclass
class CurveShape:     # ascendente, descendente, plana
@dataclass
class SlopeInfo:       # muito forte, forte, moderada, fraca, nula, negativa
@dataclass
class Convexity:       # linear, côncava, convexa, em S
@dataclass
class Volatility:      # muito baixa a muito alta
@dataclass
class Oscillation:     # número de inversões
@dataclass
class EnvelopeMetrics: # spread médio, spread por ano
@dataclass
class EvolutionTrend:  # alta contínua, queda contínua, instabilidade
@dataclass
class Diffusion:       # disseminado, concentrado curto, concentrado longo
@dataclass
class Rotation:        # bear/bull steepening/flattening
@dataclass
class Intensity:       # delta médio absoluto classificado

@dataclass
class AnalysisReport:
    statements: list[str]
    score: int
    score_label: str
```

### 3. Thresholds como parâmetros, não globais
Todas as funções de métricas e regras aceitam um dataclass `AnalysisThresholds` com valores default sensíveis.

```python
@dataclass(frozen=True)
class AnalysisThresholds:
    curva_ascendente_min: float = 0.20
    curva_descendente_min: float = 0.20
    curva_plana_max: float = 0.15
    spread_muito_estreito: float = 0.05
    spread_padrao_min: float = 0.05
    spread_padrao_max: float = 0.30
    # ... todos os thresholds
```

### 4. Painel lateral tkinter collapsível
Usar `ttk.PanedWindow` com um frame à direita que contém:
- Um botão toggle (▶/▼ "Análise") no topo
- Um `tk.Text` widget (readonly) com scrollbar para o relatório
- O painel inicia recolhido (0 pixels de largura) e expande para ~280px ao clicar

O texto é atualizado via `_redraw_chart` → chama `analyze()` → preenche o widget.

### 5. NumPy explícito
Adicionar `numpy>=1.20.0` ao `requirements.txt`. Na prática já está presente como dependência do matplotlib, mas explicitar é boa prática.

## Risks / Trade-offs

- **Performance**: A análise roda no mesmo thread do redraw. Para datasets típicos (~756 records, 5 datas) a execução é sub-milissegundo. Risco aceitável.
- **Largura da janela**: O painel lateral expande a janela. A geometria atual é 800x560; com painel será ~1100x560. O usuário pode redimensionar.
- **Precisão das regressões**: Regressão linear/quadrática com numpy tem precisão numérica padrão. Para curvas com poucos pontos (modo consolidado tem ~20 anos) os coeficientes são estáveis. Risco baixo.
- **Manutenção**: 11 camadas de regras é volumoso. A estrutura de dataclasses e funções puras mitiga isso. Cada regra é uma função isolada e testável.
- **Falsos positivos**: Regras com limiares fixos podem classificar errado em cenários atípicos. Mitigação: thresholds ajustáveis e score final que pondera múltiplas regras.
