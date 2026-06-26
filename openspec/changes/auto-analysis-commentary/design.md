## Design

### Data Model

```python
@dataclass
class AnalysisThresholds:
    indice_tendencia_asc: float = 0.20
    indice_tendencia_desc: float = -0.20
    indice_tendencia_plano: float = 0.05
    vale_posicao_max: float = 0.35
    pico_posicao_min: float = 0.65
    delta_segmento_relevante: float = 0.005
    suavidade_suave: float = 0.15
    suavidade_serrilhada: float = 0.35
    segmento_curto_max: float = 0.25
    segmento_longo_min: float = 0.50
    vale_recuperacao_min: float = 0.35
    mudanca_estrutural_min: float = 0.15

@dataclass
class MetricResults:
    segmentos: list[SegmentoInfo]
    indice_tendencia: float
    indice_suavidade: float
    extremos: list[ExtremoInfo]
    mudancas_inclinacao: list[MudancaInclinacaoInfo]
    pontos_inflexao: list[PontoInflexaoInfo]

@dataclass
class SegmentoInfo:
    nome: str          # "curto", "médio", "longo"
    inicio: int
    fim: int
    variacao: float
    classificacao: str # "ascendente", "descendente", "estável"

@dataclass
class ExtremoInfo:
    tipo: str          # "máximo" or "mínimo"
    indice: int
    valor: float

@dataclass
class MudancaInclinacaoInfo:
    indice: int
    angulo_anterior: float
    angulo_posterior: float

@dataclass
class PontoInflexaoInfo:
    indice: int
    concavidade_anterior: str
    concavidade_posterior: str

@dataclass
class RuleResult:
    rule_id: str            # "R001"–"R014"
    inference: str          # inference code, e.g. "tendencia_global_asc"
    score: int              # +2, +1, 0, −1
    activated: bool
    evidence: str           # human-readable justification
```

### Inference Engine Architecture

The engine follows a pipeline: **raw data** → **metric extraction** → **rule evaluation** → **report generation**.

```
               ┌──────────────────┐
               │  Raw data (taxas) │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │  _metrics.py     │
               │  (extraction)    │
               │  - IndiceTenden. │
               │  - 3 segmentos   │
               │  - suavidade     │
               │  - extremos      │
               │  - inflexão      │
               └────────┬─────────┘
                        │ MetricResults
                        ▼
               ┌──────────────────┐
               │  _rules.py       │
               │  (14 regras)     │
               │  R001–R014       │
               │  cada uma c/     │
               │  score ±2/±1/0   │
               └────────┬─────────┘
                        │ list[RuleResult]
                        ▼
               ┌──────────────────┐
               │  _report.py      │
               │  (montagem)      │
               │  4 blocos        │
               │  + score total   │
               │  + classificação │
               └────────┬─────────┘
                        │ str (relatório)
                        ▼
               ┌──────────────────┐
               │  gui.py          │
               │  (exibição)      │
               │  painel lateral  │
               └──────────────────┘
```

### Report Structure

O relatório possui 4 blocos fixos:

1. **Tendência Geral** — R001, R002, R003 (direção global da curva)
2. **Forma Geométrica** — R004, R005, R010, R011, R012, R013 (vales, picos, suavidade, mudanças estruturais)
3. **Segmentos** — R006, R007, R008, R009, R014 (recuperação e análise segmentada)
4. **Conclusão** — score total e classificação textual

### Score Classification

| Score  | Classificação                     |
|--------|-----------------------------------|
| 0–2    | Mercado estável                   |
| 3–4    | Mudança moderada                  |
| 5–7    | Curva estruturalmente ascendente  |
| 8–10   | Reprecificação relevante          |
| 11+    | Mudança estrutural expressiva     |

### GUI Component

- `Checkbutton` no `bottom_frame`: texto "Análise", vinculado ao `BooleanVar(self.sidebar_var)`
- `Text` widget à direita do canvas: altura igual ao canvas, largura 60 caracteres, com scrollbar
- Visibilidade controlada por `grid()` / `grid_remove()` no método `_toggle_sidebar`
- Conteúdo atualizado via `_update_analysis()` chamado dentro de `_redraw_chart`
- Placeholder `"não implementada"` para os modos "consolidado" e "evolução"

### Thresholds

Todos os thresholds são expostos no dataclass `AnalysisThresholds` e podem ser sobrescritos na chamada. A aplicação usa valores default definidos em `_thresholds.py`.

### Test Strategy

- Testes unitários para métricas (`_metrics.py`)
- Testes unitários para cada regra (`_rules.py`)
- Teste de integração para relatório (`_report.py`)
- Teste de fumaça para o facade (`__init__.py`)
- Arquivo: `tests/test_analyze.py` com 25 testes

### Risks

- **Falsos positivos em regras:** scores baixos (0–2) minimizam alarmes falsos; classificação "estável" é segura.
- **Thresholds fixos:** podem não se adaptar a todos os regimes de mercado; resolvido expondo thresholds como parâmetros ajustáveis.
- **Desempenho:** o cálculo é O(n) e não impacta o redraw do gráfico (n < 1000 pontos).
- **Manutenção:** regras isoladas em funções puras facilitam adicionar/remover regras sem efeito colateral.
