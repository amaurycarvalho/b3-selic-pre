"""Cenário do dólar (Focus) e projeção estatística do ouro."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.application.market.forecast_stat import (
    ewma_sigma,
    log_returns,
    statistical_forecast,
)
from b3_selic_pre.application.market.forecast_types import (
    CENARIO_ESTATISTICO,
    CENARIO_MERCADO,
    FOCUS_AUSENTE,
    HISTORICO_INSUFICIENTE,
    FocusExpectation,
    ForecastOutcome,
    add_months,
)
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    METODO_MERCADO,
    ForecastBand,
    ForecastPoint,
    MarketQuote,
)


def _sorted(expectations: Sequence[FocusExpectation]) -> list[FocusExpectation]:
    return sorted(expectations, key=lambda item: item.ano)


def _bracket(
    expectations: Sequence[FocusExpectation], target: date
) -> tuple[FocusExpectation, FocusExpectation, float] | None:
    ordered = _sorted(expectations)
    if not ordered:
        return None
    lower = ordered[0]
    upper = ordered[-1]
    for item in ordered:
        if item.ano <= target.year:
            lower = item
        if item.ano >= target.year:
            upper = item
            break
    if lower.ano == upper.ano:
        return lower, upper, 0.0
    start = date(lower.ano, 12, 31)
    end = date(upper.ano, 12, 31)
    weight = (target - start).days / (end - start).days
    return lower, upper, min(1.0, max(0.0, weight))


def _log_interpolate(lower: float, upper: float, weight: float) -> float:
    return math.exp(
        math.log(lower) * (1 - weight) + math.log(upper) * weight
    )


def focus_target(
    expectations: Sequence[FocusExpectation],
    reference: date,
    months: int,
) -> float | None:
    """Interpolate the Focus median for the horizon end date."""
    bracket = _bracket(expectations, add_months(reference, months))
    if bracket is None:
        return None
    lower, upper, weight = bracket
    return _log_interpolate(lower.mediana, upper.mediana, weight)


def _relative_dispersion(item: FocusExpectation) -> float:
    if item.minimo is not None and item.maximo is not None:
        width = (item.maximo - item.minimo) / 2
        return width / item.mediana if item.mediana else 0.05
    return 0.05


def focus_dispersion(
    expectations: Sequence[FocusExpectation],
    reference: date,
    months: int,
) -> float:
    """Interpolate the relative Focus dispersion at the horizon."""
    bracket = _bracket(expectations, add_months(reference, months))
    if bracket is None:
        return 0.05
    lower, upper, weight = bracket
    low = _relative_dispersion(lower)
    high = _relative_dispersion(upper)
    return low * (1 - weight) + high * weight


def forecast_usd(
    spot: MarketQuote,
    expectations: Sequence[FocusExpectation],
    reference: date,
    config: MarketConfig,
) -> ForecastOutcome:
    """Build the Focus-anchored dollar scenario with 80/95% bands."""
    target = focus_target(expectations, reference, config.projecao.meses)
    if target is None or spot.valor <= 0:
        return ForecastOutcome(motivo=FOCUS_AUSENTE)
    dispersion = focus_dispersion(
        expectations, reference, config.projecao.meses
    )
    ratio = target / spot.valor
    points: list[ForecastPoint] = []
    for month in range(1, config.projecao.meses + 1):
        fraction = month / config.projecao.meses
        center = spot.valor * (ratio**fraction)
        sigma = dispersion * math.sqrt(fraction)
        points.append(
            ForecastPoint(
                data=add_months(reference, month).isoformat(),
                ativo=ATIVO_USD,
                cenario=CENARIO_MERCADO,
                metodo=METODO_MERCADO,
                centro=center,
                bandas=(
                    ForecastBand(
                        80,
                        center * math.exp(-config.projecao.z80 * sigma),
                        center * math.exp(config.projecao.z80 * sigma),
                    ),
                    ForecastBand(
                        95,
                        center * math.exp(-config.projecao.z95 * sigma),
                        center * math.exp(config.projecao.z95 * sigma),
                    ),
                ),
            )
        )
    return ForecastOutcome(tuple(points))


def dol_short_premium(
    dol_front: MarketQuote,
    spot: MarketQuote,
    dias_ate_vencimento: int,
    business_days: int = 252,
) -> float | None:
    """Return the annualized short-term DOL premium versus spot."""
    if dias_ate_vencimento <= 0 or spot.valor <= 0:
        return None
    premium = (dol_front.valor / spot.valor - 1) * business_days
    return premium * 100 / dias_ate_vencimento



__all__ = [
    "ATIVO_OURO",
    "CENARIO_ESTATISTICO",
    "CENARIO_MERCADO",
    "FOCUS_AUSENTE",
    "HISTORICO_INSUFICIENTE",
    "FocusExpectation",
    "ForecastOutcome",
    "add_months",
    "dol_short_premium",
    "ewma_sigma",
    "focus_dispersion",
    "focus_target",
    "forecast_usd",
    "log_returns",
    "statistical_forecast",
]
