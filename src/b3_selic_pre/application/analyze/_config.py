from dataclasses import dataclass


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
    recuperacao_longa_min_pct: float = 0.15
    recuperacao_longa_min_ratio: float = 0.70
    recuperacao_longa_min_amplitude: float = 0.40
