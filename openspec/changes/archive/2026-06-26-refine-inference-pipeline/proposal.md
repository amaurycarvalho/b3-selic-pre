## Why

O motor hierárquico atual (`hierarchical-inference-engine`) ainda depende de contagem de extremos locais para classificação VALE/PICO — uma abordagem que quebra com dados reais da B3. Além disso, métricas são ambíguas, a especificação está acoplada a bibliotecas, score e classificação estão misturados no mesmo módulo, e não há rastreabilidade. Esta especificação introduz uma arquitetura de **sistema especialista determinístico** com: (1) pipeline `Métricas → Features → Registry → Classifier → Facts → ScoringPolicy → Report`; (2) **ScoringPolicy** independente (pesos não pertencem às regras); (3) **rastreabilidade em dois níveis** (`derived_from_features` + `derived_from_metrics`); (4) **InferenceConfig** centralizando todos os limiares; (5) **versionamento** do motor para reprodutibilidade; (6) Classifier **puro** (sem estado, sem mutação, determinístico); (7) **templates internacionalizáveis** por `template_id`; (8) Features **imutáveis** pós-computação.

## What Changes

- **Pipeline completo**: `Raw Data → Metrics → Features → Rule Registry → Classifier → Facts → ScoringPolicy → Score → Report Templates → Analysis Report`. Registry, ScoringPolicy e Templates são componentes independentes.
- **ScoringPolicy separada do Registry**: regras no Registry definem apenas `id`, `priority`, `required_features`, `generated_fact`, `text_template_id`, `exclusive_group` — nunca `weight`. A ScoringPolicy mapeia `fact → weight` externamente, permitindo múltiplas políticas de score (conservadora, agressiva) sem alterar regras.
- **Rastreabilidade em dois níveis**: cada Fact carrega `derived_from_features`. Cada Feature carrega `derived_from_metrics`. A cadeia completa `Métrica → Feature → Fact` é auditável.
- **Features imutáveis**: após `compute_features()`, nenhuma regra pode alterar Features. Apenas gerar novos Facts.
- **FactType**: `CLASSIFICATION`, `STRUCTURE`, `QUALITY`, `INTENSITY`, `AUXILIARY`. Simplifica o Report.
- **Grupos de exclusividade no Registry**: `exclusive_group = "PRIMARY_CLASS"` impede que regras contraditórias coexistam.
- **Confiança por Fact**: `confidence = opcionais_satisfeitas / total_opcionais`, de 0 a 1. Mesmo sendo determinístico, melhora a explicabilidade.
- **InferenceConfig**: centraliza todos os ε (slope, convexidade, amplitude, horizontal) em um único dataclass parametrizável.
- **Versionamento do motor**: `AnalysisResult` inclui `engine_version`, `ruleset_version`, `generated_at` para reprodutibilidade.
- **Classifier puro**: mesmas entradas → mesmas saídas. Sem estado interno, sem cache, sem mutação de objetos recebidos.
- **Prioridade explícita**: `priority` menor = maior prioridade (0 executa antes de 100).
- **Templates internacionalizáveis**: regras referenciam `template_id`, não texto inline. Textos residem em um mapa de templates por locale.
- **Report consome apenas Facts**: nunca acessa Features ou métricas diretamente.
- **Framework VALE/PICO** com short-circuit (condição A obrigatória, 3/4 opcionais).
- **Métricas com fórmulas explícitas** e independentes de biblioteca; normalização X ∈ [0,1]; guarda contra divisão por zero.

## Capabilities

### New Capabilities

*(Nenhuma — refinamento de capacidade existente.)*

### Modified Capabilities

- `auto-analysis`: ScoringPolicy separada do Registry; rastreabilidade em dois níveis; InferenceConfig centralizado; versionamento do motor; Classifier puro; Features imutáveis; FactType; grupos de exclusividade; confiança por Fact; templates internacionalizáveis.

## Impact

- **Arquivos novos**:
  - `_features.py` — Features tipadas e imutáveis, com `derived_from_metrics`
  - `_registry.py` — Registry declarativo (sem weight), com `exclusive_group`
  - `_scoring.py` — **NOVO**: ScoringPolicy (substitui `_scorer.py`)
  - `_config.py` — **NOVO**: InferenceConfig (todos os ε centralizados)
  - `_templates.py` — **NOVO**: mapa de templates por locale, indexado por `template_id`
- **Arquivos modificados**:
  - `_metrics.py` — métricas com fórmulas explícitas e guards
  - `_classifier.py` — puro, consome Registry + Features; produz Facts com `derived_from_features`
  - `_report.py` — consome apenas Facts; 5 blocos; rastreabilidade; resumo por template
  - `__init__.py` — pipeline integrado com versionamento
  - `tests/test_analyze.py` — testes para cada componente isolado
- **Arquivos removidos**:
  - `_scorer.py` (substituído por `_scoring.py`)
- **BREAKING**: estrutura interna completamente reorganizada; API pública de `analyze()` mantida.
