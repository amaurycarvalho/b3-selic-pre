from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisThresholds:
    curva_ascendente_min: float = 0.20
    curva_descendente_min: float = 0.20
    curva_plana_max: float = 0.15
    inclinacao_muito_forte: float = 0.010
    inclinacao_forte: float = 0.005
    inclinacao_moderada: float = 0.002
    inclinacao_fraca: float = 0.0005
    convexidade_relevante: float = 0.0001
    volatilidade_muito_alta: float = 0.15
    volatilidade_alta: float = 0.10
    volatilidade_normal_max: float = 0.06
    volatilidade_baixa: float = 0.03
    oscilacoes_alto: int = 15
    spread_muito_estreito: float = 0.05
    spread_padrao_min: float = 0.05
    spread_padrao_max: float = 0.30
    difusao_disseminado: float = 0.80
    intensidade_muito_grande: float = 0.30
    intensidade_grande: float = 0.15
    intensidade_moderada: float = 0.08
    intensidade_pequena: float = 0.03
    score_expressivo: int = 13
    score_relevante: int = 8
    score_moderado: int = 4
