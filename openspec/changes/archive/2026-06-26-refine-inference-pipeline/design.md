## Context

O motor atual implementa `Métricas → Classifier → Report`. Score e classificação estão acoplados. Não há rastreabilidade, versionamento, nem separação entre regras e política de pontuação. Features são booleanas ad-hoc. Templates são strings inline.

## Goals / Non-Goals

**Goals:**
- Pipeline: `Métricas → Features → Registry → Classifier → Facts → ScoringPolicy → Report`
- ScoringPolicy independente do Registry (pesos não pertencem às regras)
- Rastreabilidade em dois níveis (Feature → Métrica, Fact → Feature)
- InferenceConfig centralizando todos os limiares
- Versionamento do motor para reprodutibilidade
- Classifier puro (determinístico, sem estado, sem mutação)
- Features imutáveis pós-computação
- Templates internacionalizáveis por `template_id`

**Non-Goals:**
- Alterar a estrutura conceitual de 5 níveis
- Implementar análise consolidada/evolução

## Decisions

### D1: ScoringPolicy separada do Registry

**Problema:** Se o peso está na regra, o Classifier já produz score. Isso impede políticas diferentes de score sem alterar regras.

**Decisão:** O Registry define apenas lógica (quais features ativam qual fato). A ScoringPolicy define valor (quanto cada fato contribui para o score). São módulos independentes.

```python
# _registry.py — NUNCA contém weight
@dataclass
class RuleDef:
    id: str
    priority: int          # menor = maior prioridade
    exclusive_group: str   # "PRIMARY_CLASS", "STRUCTURE", "" (sem grupo)
    required_features: list[str]
    optional_features: list[str]
    min_optional: int
    gated_by: list[str]
    generated_fact: str
    fact_type: FactType
    template_id: str       # referência, não texto inline

# _scoring.py — pesos vivem aqui
SCORING_POLICY: dict[str, tuple[int, int]] = {
    "CURVA_COM_VALE": (2, 3),       # (score_base, weight_level)
    "RECUPERACAO_SUSTENTADA": (1, 2),
    ...
}
```

**Alternativa:** Manter weight no Registry. Rejeitada porque acopla classificação e pontuação.

### D2: Rastreabilidade em dois níveis

```
Fact
  ├── derived_from_features: ["MIN_GLOBAL_LEFT", "AFTER_MIN_UP", ...]
  │
  └── (via Feature)
        └── derived_from_metrics: ["slope_global", "indice_minimo_global", ...]
```

Cada Feature armazena quais métricas a produziram. Cada Fact armazena quais Features o ativaram. A cadeia completa é reconstruível.

```python
@dataclass
class Feature:
    name: str
    value: Any
    type: FeatureType
    derived_from_metrics: list[str]  # nomes das métricas usadas

@dataclass
class Fact:
    id: str
    rule_id: str
    fact_type: FactType
    confidence: float
    derived_from_features: list[str]  # nomes das Features que ativaram
    text: str
```

### D3: Features imutáveis

Após `compute_features(metrics, rates, config) -> dict[str, Feature]`, o dicionário de Features é congelado. Nenhuma regra pode modificá-lo. Apenas o Classifier pode gerar novos Facts a partir dele.

### D4: FactType

```python
class FactType(Enum):
    CLASSIFICATION = "classification"   # Nível 1
    STRUCTURE = "structure"             # Nível 2
    QUALITY = "quality"                 # Nível 3
    INTENSITY = "intensity"             # Nível 4 (produzido pelo Scorer)
    AUXILIARY = "auxiliary"             # informativo, não conta para score
```

O Report usa `FactType` para agrupar fatos nos blocos corretos, sem depender de nomes de regras.

### D5: Grupos de exclusividade

```python
@dataclass
class RuleDef:
    exclusive_group: str  # "PRIMARY_CLASS" → apenas uma regra deste grupo ativa
```

Quando uma regra de um `exclusive_group` ativa, as demais do mesmo grupo são ignoradas. Exemplo: `ASCENDENTE` e `DESCENDENTE` pertencem a `"PRIMARY_CLASS"` — apenas uma pode ser escolhida.

### D6: Confiança por Fact

```python
fact.confidence = len(satisfied_optional) / len(optional_features)
```

Se todas as opcionais foram satisfeitas → 1.0. Se apenas o mínimo → 0.75 (3/4). Exibida no relatório.

### D7: InferenceConfig

```python
@dataclass
class InferenceConfig:
    epsilon_slope: float = 0.00005
    epsilon_convexity: float = 0.001
    epsilon_amplitude: float = 1e-9
    epsilon_horizontal: float = 0.00002
    vale_posicao_max: float = 0.40
    pico_posicao_max: float = 0.60
    recuperacao_min_ratio: float = 0.80
    recuperacao_magnitude: float = 0.50
    oscilacao_threshold: float = 0.35
    suavidade_relativo: float = 0.01
    suavidade_serrilhado: float = 0.15
    volatilidade_baixa: float = 0.01
    volatilidade_alta: float = 0.05
    amplitude_consenso: float = 0.10
    amplitude_dispersao: float = 1.50
    degraus_min_pct: float = 0.05
    degraus_min_count: int = 3
    sigmoide_segment_min: float = 0.15
    steepening_ratio: float = 2.0
    monotonico_ratio: float = 0.90
```

Todos os ε em um único lugar. Passado como parâmetro, permitindo override por chamada.

### D8: Versionamento do motor

```python
ENGINE_VERSION = "2.0.0"
RULESET_VERSION = "1.0.0"

@dataclass
class AnalysisResult:
    engine_version: str
    ruleset_version: str
    generated_at: str  # ISO 8601
    facts: list[Fact]
    score: int
    intensity_label: str
    confidence: dict[str, float]
```

Garante reprodutibilidade: mesma versão do motor + mesmo ruleset + mesmos dados → mesmo resultado.

### D9: Report consome apenas Facts

O Report não importa `_features.py` nem `_metrics.py`. Recebe apenas `list[Fact]` e `AnalysisResult`. Toda informação necessária está nos Facts (texto, tipo, confiança, derived_from).

### D10: Classifier puro

O Classifier é uma função pura:
- Entradas: `features: dict[str, Feature]`, `registry: list[RuleDef]`
- Saída: `list[Fact]`
- Sem estado interno, sem cache, sem logging, sem mutação dos parâmetros recebidos
- Determinístico: mesmas entradas → mesmas saídas

### D11: Prioridade explícita

`priority` é um inteiro. **Menor = maior prioridade.** Regras são ordenadas por `priority` ascendente antes da avaliação. Prioridade 0 executa antes de prioridade 100.

```python
rules = sorted(registry, key=lambda r: r.priority)
for rule in rules:
    if evaluate(rule, features):
        break  # ou continue, dependendo do exclusive_group
```

### D12: Templates internacionalizáveis

```python
# _templates.py
TEMPLATES = {
    "pt": {
        "vale_primary": "Observa-se uma depressão na parte curta da curva, seguida por recuperação gradual das taxas.",
        "recuperacao": "A recuperação observada na parte curta se mantém ao longo dos vencimentos médios e longos.",
        ...
    },
    "en": {
        "vale_primary": "A depression is observed in the short end of the curve, followed by gradual rate recovery.",
        ...
    }
}
```

Regras referenciam `template_id`. O Report resolve `template_id` + `locale` → texto.

## Architecture Diagram

```
Raw Data
    │
    ▼
Metrics (_metrics.py)
    │
    ▼
Features (_features.py) ◄── InferenceConfig (_config.py)
    │
    ▼
Rule Registry (_registry.py)
    │
    ▼
Classifier (_classifier.py)  [PURO]
    │
    ▼
Facts ◄── derived_from_features
    │         │
    │         └── Feature.derived_from_metrics
    │
    ▼
ScoringPolicy (_scoring.py)
    │
    ▼
Score + Intensity
    │
    ▼
Report Templates (_templates.py)
    │
    ▼
Analysis Report (_report.py)
```

## Risks / Trade-offs

- **ScoringPolicy separada:** adiciona um arquivo, mas desacopla pontuação de classificação. Troca justa.
- **Dois níveis de rastreabilidade:** aumenta o tamanho dos objetos Feature e Fact. Mitigação: listas de strings são pequenas.
- **Templates internacionalizáveis:** requer manutenção de traduções. Mitigação: começar apenas com `pt`.
- **InferenceConfig:** muitos parâmetros podem ser intimidantes. Mitigação: defaults sensíveis, documentados.
