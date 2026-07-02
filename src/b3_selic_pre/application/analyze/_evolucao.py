from __future__ import annotations

from dataclasses import dataclass, field

from b3_selic_pre.application.analyze._config import CurvaJurosConfig, EvolutionConfig
from b3_selic_pre.domain.models import RateRecord


def extrair_deltas(
    current_records: list[RateRecord],
    previous_records: list[RateRecord],
) -> tuple[float, float, float, float]:
    current_rates = [float(r.rate.replace(",", ".")) for r in current_records]
    previous_rates = [float(r.rate.replace(",", ".")) for r in previous_records]
    delta_short = (current_rates[0] - previous_rates[0]) * 100
    delta_long = (current_rates[-1] - previous_rates[-1]) * 100
    current_slope = (current_rates[-1] - current_rates[0]) * 100
    previous_slope = (previous_rates[-1] - previous_rates[0]) * 100
    delta_slope = current_slope - previous_slope
    delta_real = delta_short
    return delta_short, delta_long, delta_slope, delta_real


def classificar_movimento(
    delta_short: float, delta_long: float, config: EvolutionConfig
) -> str:
    threshold = config.movement_threshold_bps
    if max(abs(delta_short), abs(delta_long)) < threshold:
        return "Estável"
    if delta_short > threshold and delta_long > threshold:
        return "Bear"
    if delta_short < -threshold and delta_long < -threshold:
        return "Bull"
    if (delta_short > threshold and delta_long < -threshold) or (
        delta_short < -threshold and delta_long > threshold
    ):
        return "Twist"
    return "Estável"


def classificar_slope_movement(
    delta_slope: float, config: EvolutionConfig
) -> str:
    threshold = config.steepening_threshold_bps
    if delta_slope > threshold:
        return "Steepening"
    if delta_slope < -threshold:
        return "Flattening"
    return "Parallel Shift"


def classificar_regime(movimento: str, slope_movement: str) -> str:
    if movimento == "Estável":
        return "Estável"
    if movimento == "Twist":
        return "Twist"
    return f"{movimento} {slope_movement}"


def classificar_intensidade(
    delta_short: float, delta_long: float, config: EvolutionConfig
) -> str:
    max_abs = max(abs(delta_short), abs(delta_long))
    if max_abs <= config.very_weak_max:
        return "Muito Fraca"
    if max_abs <= config.weak_max:
        return "Fraca"
    if max_abs <= config.moderate_max:
        return "Moderada"
    if max_abs <= config.strong_max:
        return "Forte"
    return "Muito Forte"


def classificar_politica_monetaria(
    delta_real: float, config: EvolutionConfig
) -> str:
    if delta_real > config.highly_restrictive_min:
        return "Mercado passou a precificar política mais restritiva"
    if delta_real > config.slightly_restrictive_min:
        return "Política ligeiramente mais restritiva"
    if abs(delta_real) <= config.neutral_max:
        return "Política praticamente inalterada"
    if delta_real < -config.slightly_loose_max:
        return "Mercado passou a precificar política significativamente menos restritiva"
    if delta_real < -config.slightly_restrictive_min:
        return "Política ligeiramente menos restritiva"
    return "Política praticamente inalterada"


def classificar_premio_prazo(
    delta_slope: float, config: EvolutionConfig
) -> str:
    if delta_slope > config.significantly_increased_min:
        return "Prêmio de prazo aumentou significativamente"
    if delta_slope > config.increased_min:
        return "Prêmio aumentou"
    if abs(delta_slope) <= config.increased_min:
        return "Praticamente estável"
    if delta_slope < -config.decreased_min:
        return "Forte redução do prêmio"
    if delta_slope < -config.increased_min:
        return "Prêmio diminuiu"
    return "Praticamente estável"


def derivar_direcao_geral(regime: str, intensidade: str) -> str:
    if regime == "Estável":
        return "→ Estrutura a Juros Praticamente Estável"
    if regime == "Twist":
        return "↕ Movimento Misto na Estrutura"
    if regime.startswith("Bear"):
        if intensidade in ("Muito Fraca",):
            return "→ Juros Marginalmente Mais Altos"
        return "↑ Revisão Altista dos Juros"
    if regime.startswith("Bull"):
        if intensidade in ("Muito Fraca",):
            return "→ Juros Marginalmente Mais Baixos"
        return "↓ Revisão Baixista dos Juros"
    return "→ Estrutura a Juros Praticamente Estável"


@dataclass
class EvolutionReport:
    statements: list[str] = field(default_factory=list)
    delta_short_bps: float = 0.0
    delta_long_bps: float = 0.0
    delta_slope_bps: float = 0.0
    delta_real_bps: float = 0.0
    regime: str = ""
    intensity: str = ""
    monetary_policy_msg: str = ""
    term_premium_msg: str = ""
    direction: str = ""
    market_message: str = ""


def analyze_evolution(
    current: list[RateRecord],
    previous: list[RateRecord],
    config: CurvaJurosConfig | None = None,
) -> EvolutionReport | None:
    if not previous:
        return None

    if config is None:
        config = CurvaJurosConfig.from_settings()

    evol_config = config.evolucao
    delta_short, delta_long, delta_slope, delta_real = extrair_deltas(current, previous)

    movimento = classificar_movimento(delta_short, delta_long, evol_config)
    slope_movement = classificar_slope_movement(delta_slope, evol_config)
    regime = classificar_regime(movimento, slope_movement)

    if movimento == "Estável":
        intensidade = "Muito Fraca"
    else:
        intensidade = classificar_intensidade(delta_short, delta_long, evol_config)
    politica_msg = classificar_politica_monetaria(delta_real, evol_config)
    premio_msg = classificar_premio_prazo(delta_slope, evol_config)
    direction = derivar_direcao_geral(regime, intensidade)

    return EvolutionReport(
        statements=[],
        delta_short_bps=round(delta_short, 2),
        delta_long_bps=round(delta_long, 2),
        delta_slope_bps=round(delta_slope, 2),
        delta_real_bps=round(delta_real, 2),
        regime=regime,
        intensity=intensidade,
        monetary_policy_msg=politica_msg,
        term_premium_msg=premio_msg,
        direction=direction,
        market_message="",
    )
