"""Projeção estatística com drift encolhido e volatilidade EWMA."""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from datetime import date

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.application.market.forecast_types import (
    CENARIO_ESTATISTICO,
    HISTORICO_INSUFICIENTE,
    ForecastOutcome,
    add_months,
)
from b3_selic_pre.domain.market import (
    METODO_ESTATISTICO,
    ForecastBand,
    ForecastPoint,
    MarketQuote,
)


def log_returns(values: Sequence[float]) -> list[float]:
    """Return logarithmic returns, skipping non-positive observations."""
    returns: list[float] = []
    for previous, current in itertools.pairwise(values):
        if previous > 0 and current > 0:
            returns.append(math.log(current / previous))
    return returns


def ewma_sigma(returns: Sequence[float], lam: float) -> float:
    """Return the EWMA volatility of a return sequence."""
    if not returns:
        return 0.0
    variance = returns[0] ** 2
    for value in returns[1:]:
        variance = lam * variance + (1 - lam) * value**2
    return math.sqrt(variance)


def statistical_forecast(
    ativo: str,
    history: Sequence[MarketQuote],
    reference: date,
    config: MarketConfig,
) -> ForecastOutcome:
    """Build a random-walk scenario with shrunk drift and EWMA bands."""
    if not history:
        return ForecastOutcome(motivo=HISTORICO_INSUFICIENTE)
    ordered = sorted(history, key=lambda item: item.data)
    values = [quote.valor for quote in ordered]
    returns = log_returns(values)
    if len(returns) < config.projecao.min_retornos:
        return ForecastOutcome(motivo=HISTORICO_INSUFICIENTE)
    drift = config.projecao.drift_shrink * (
        sum(returns) / len(returns)
    )
    sigma = ewma_sigma(returns, config.projecao.ewma_lambda)
    last = ordered[-1]
    points: list[ForecastPoint] = []
    for month in range(1, config.projecao.meses + 1):
        horizon = month * 21
        fraction = horizon / config.projecao.dias_uteis_ano
        center = last.valor * math.exp(drift * fraction)
        width = sigma * math.sqrt(fraction)
        points.append(
            ForecastPoint(
                data=add_months(reference, month).isoformat(),
                ativo=ativo,
                cenario=CENARIO_ESTATISTICO,
                metodo=METODO_ESTATISTICO,
                centro=center,
                bandas=(
                    ForecastBand(
                        80,
                        center * math.exp(-config.projecao.z80 * width),
                        center * math.exp(config.projecao.z80 * width),
                    ),
                    ForecastBand(
                        95,
                        center * math.exp(-config.projecao.z95 * width),
                        center * math.exp(config.projecao.z95 * width),
                    ),
                ),
            )
        )
    return ForecastOutcome(tuple(points))


