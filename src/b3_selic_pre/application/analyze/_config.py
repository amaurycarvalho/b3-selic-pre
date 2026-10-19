"""Configurações das análises de evolução e da curva de juros prefixados."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvolutionConfig:
    """Configuração dos limiares usados na análise de evolução da curva."""

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
    def from_mapping(
        cls: type[EvolutionConfig], curva_evolucao: dict | None = None
    ) -> EvolutionConfig:
        """Constrói a configuração de evolução a partir de um dicionário de ajustes."""
        data = curva_evolucao or {}
        return cls(
            movement_threshold_bps=data.get("movement_threshold_bps", 5.0),
            steepening_threshold_bps=data.get("steepening_threshold_bps", 5.0),
            very_weak_max=data.get("very_weak_max", 5.0),
            weak_max=data.get("weak_max", 15.0),
            moderate_max=data.get("moderate_max", 30.0),
            strong_max=data.get("strong_max", 50.0),
            highly_restrictive_min=data.get("highly_restrictive_min", 20.0),
            slightly_restrictive_min=data.get("slightly_restrictive_min", 5.0),
            neutral_max=data.get("neutral_max", 5.0),
            slightly_loose_max=data.get("slightly_loose_max", 20.0),
            significantly_increased_min=data.get("significantly_increased_min", 20.0),
            increased_min=data.get("increased_min", 10.0),
            decreased_min=data.get("decreased_min", 20.0),
        )


@dataclass
class CurvaJurosConfig:
    """Configuração das faixas e parâmetros da análise da curva de juros."""

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
    def from_mapping(
        cls: type[CurvaJurosConfig],
        curva_juros: dict | None = None,
        curva_evolucao: dict | None = None,
    ) -> CurvaJurosConfig:
        """Constrói a configuração da curva a partir de mappings simples."""
        juros = curva_juros or {}
        evolucao = curva_evolucao or {}

        return cls(
            expected_inflation=juros.get("expected_inflation", 3.0),
            faixas_nominais=juros.get("faixas_nominais", [6.0, 9.0, 11.0, 13.0]),
            faixas_juro_real=juros.get("faixas_juro_real", [2.0, 4.0, 6.0]),
            stability_window=juros.get("stability_window", 4),
            stability_fallback=juros.get("stability_fallback", "default"),
            default_mean_deviation_bps=juros.get("default_mean_deviation_bps", 15.0),
            faixas_estabilidade=juros.get("faixas_estabilidade", [5.0, 10.0, 20.0, 35.0]),
            steepening_fallback=evolucao.get("steepening_fallback", "unavailable"),
            estimated_delta_slope_bps=evolucao.get("estimated_delta_slope_bps", 15.0),
            steepening_threshold_bps=evolucao.get("steepening_threshold_bps", 5.0),
            steepening_small_bps=evolucao.get("steepening_small_bps", 10.0),
            steepening_medium_bps=evolucao.get("steepening_medium_bps", 20.0),
            steepening_large_bps=evolucao.get("steepening_large_bps", 40.0),
            evolucao=EvolutionConfig.from_mapping(evolucao),
        )
