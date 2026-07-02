from __future__ import annotations

from dataclasses import dataclass, field

from b3_selic_pre.presentation.settings import Settings


@dataclass
class EvolutionConfig:
    movement_threshold_bps: float = 5.0
    steepening_threshold_bps: float = 5.0
    very_weak_max: float = 5.0
    weak_max: float = 15.0
    moderate_max: float = 30.0
    strong_max: float = 50.0
    highly_restrictive_min: float = 20.0
    slightly_restrictive_min: float = 5.0
    neutral_max: float = 5.0
    slightly_loose_max: float = 20.0
    significantly_increased_min: float = 20.0
    increased_min: float = 10.0
    decreased_min: float = 20.0

    @classmethod
    def from_settings(cls, curva_evolucao: dict) -> EvolutionConfig:
        return cls(
            movement_threshold_bps=curva_evolucao.get("movement_threshold_bps", 5.0),
            steepening_threshold_bps=curva_evolucao.get("steepening_threshold_bps", 5.0),
            very_weak_max=curva_evolucao.get("very_weak_max", 5.0),
            weak_max=curva_evolucao.get("weak_max", 15.0),
            moderate_max=curva_evolucao.get("moderate_max", 30.0),
            strong_max=curva_evolucao.get("strong_max", 50.0),
            highly_restrictive_min=curva_evolucao.get("highly_restrictive_min", 20.0),
            slightly_restrictive_min=curva_evolucao.get("slightly_restrictive_min", 5.0),
            neutral_max=curva_evolucao.get("neutral_max", 5.0),
            slightly_loose_max=curva_evolucao.get("slightly_loose_max", 20.0),
            significantly_increased_min=curva_evolucao.get("significantly_increased_min", 20.0),
            increased_min=curva_evolucao.get("increased_min", 10.0),
            decreased_min=curva_evolucao.get("decreased_min", 20.0),
        )


@dataclass
class CurvaJurosConfig:
    expected_inflation: float = 3.0
    faixas_nominais: list[float] = field(default_factory=lambda: [6.0, 9.0, 11.0, 13.0])
    faixas_juro_real: list[float] = field(default_factory=lambda: [2.0, 4.0, 6.0])
    stability_window: int = 4
    stability_fallback: str = "default"
    default_mean_deviation_bps: float = 15.0
    faixas_estabilidade: list[float] = field(default_factory=lambda: [5.0, 10.0, 20.0, 35.0])
    steepening_fallback: str = "unavailable"
    estimated_delta_slope_bps: float = 15.0
    steepening_threshold_bps: float = 5.0
    steepening_small_bps: float = 10.0
    steepening_medium_bps: float = 20.0
    steepening_large_bps: float = 40.0
    evolucao: EvolutionConfig = field(default_factory=EvolutionConfig)

    @classmethod
    def from_settings(cls) -> CurvaJurosConfig:
        settings = Settings()
        curva_juros = settings.get("curva_juros", {})
        curva_evolucao = settings.get("curva_evolucao", {})

        return cls(
            expected_inflation=curva_juros.get("expected_inflation", 3.0),
            faixas_nominais=curva_juros.get("faixas_nominais", [6.0, 9.0, 11.0, 13.0]),
            faixas_juro_real=curva_juros.get("faixas_juro_real", [2.0, 4.0, 6.0]),
            stability_window=curva_juros.get("stability_window", 4),
            stability_fallback=curva_juros.get("stability_fallback", "default"),
            default_mean_deviation_bps=curva_juros.get("default_mean_deviation_bps", 15.0),
            faixas_estabilidade=curva_juros.get("faixas_estabilidade", [5.0, 10.0, 20.0, 35.0]),
            steepening_fallback=curva_evolucao.get("steepening_fallback", "unavailable"),
            estimated_delta_slope_bps=curva_evolucao.get("estimated_delta_slope_bps", 15.0),
            steepening_threshold_bps=curva_evolucao.get("steepening_threshold_bps", 5.0),
            steepening_small_bps=curva_evolucao.get("steepening_small_bps", 10.0),
            steepening_medium_bps=curva_evolucao.get("steepening_medium_bps", 20.0),
            steepening_large_bps=curva_evolucao.get("steepening_large_bps", 40.0),
            evolucao=EvolutionConfig.from_settings(curva_evolucao),
        )
