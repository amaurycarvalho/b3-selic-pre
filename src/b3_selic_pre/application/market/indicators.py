"""Indicadores determinísticos de política cambial."""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from datetime import date, timedelta

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.application.market.forecast import dol_short_premium
from b3_selic_pre.domain.market import MarketQuote, PolicyIndicators


def _values_in_window(
    history: Sequence[MarketQuote], reference: date, days: int
) -> list[float]:
    cutoff = reference - timedelta(days=days)
    return [
        quote.valor
        for quote in sorted(history, key=lambda item: item.data)
        if date.fromisoformat(quote.data) > cutoff
    ]


def _log_returns(values: Sequence[float]) -> list[float]:
    return [
        math.log(current / previous)
        for previous, current in itertools.pairwise(values)
        if previous > 0 and current > 0
    ]


def realized_volatility(
    values: Sequence[float], business_days: int = 252
) -> float | None:
    """Return annualized realized volatility in percent."""
    returns = _log_returns(values)
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / (
        len(returns) - 1
    )
    return math.sqrt(variance) * math.sqrt(business_days) * 100


def window_volatility(
    history: Sequence[MarketQuote],
    reference: date,
    days: int,
    business_days: int = 252,
) -> float | None:
    """Return realized volatility for the trailing ``days`` window."""
    return realized_volatility(
        _values_in_window(history, reference, days), business_days
    )


def window_drift(
    history: Sequence[MarketQuote], reference: date, days: int
) -> float | None:
    """Return the mean log return of the trailing ``days`` window."""
    returns = _log_returns(_values_in_window(history, reference, days))
    if not returns:
        return None
    return sum(returns) / len(returns)


def term_premium(focus: float, spot: float) -> float | None:
    """Return the annualized Focus premium over spot in percent."""
    if spot <= 0:
        return None
    return (focus / spot - 1) * 100


def focus_gap(focus: float, spot: float) -> float:
    """Return the absolute gap between the Focus expectation and spot."""
    return focus - spot


def regime_signal(
    vol30: float | None,
    vol90: float | None,
    drift30: float | None,
    drift90: float | None,
    threshold: float,
) -> bool | None:
    """Return the deterministic regime flag when all inputs exist."""
    if vol30 is None or vol90 is None:
        return None
    if drift30 is None or drift90 is None or vol90 <= 0:
        return None
    ratio = vol30 / vol90
    return ratio >= threshold and (drift30 > 0) != (drift90 > 0)


def compute_indicators(
    history: Sequence[MarketQuote],
    spot: MarketQuote,
    config: MarketConfig,
    focus: float | None = None,
    dol_front: MarketQuote | None = None,
    dias_ate_vencimento: int | None = None,
) -> PolicyIndicators:
    """Compute every available signal, omitting those without inputs."""
    reference = date.fromisoformat(spot.data)
    vol30 = window_volatility(
        history, reference, config.projecao.vol_curta,
        config.projecao.dias_uteis_ano,
    )
    vol90 = window_volatility(
        history, reference, config.projecao.vol_longa,
        config.projecao.dias_uteis_ano,
    )
    drift30 = window_drift(history, reference, config.projecao.vol_curta)
    drift90 = window_drift(history, reference, config.projecao.vol_longa)
    regime = regime_signal(
        vol30, vol90, drift30, drift90, config.projecao.regime_ratio
    )
    premio_dol = None
    if dol_front is not None and dias_ate_vencimento is not None:
        premio_dol = dol_short_premium(
            dol_front,
            spot,
            dias_ate_vencimento,
            config.projecao.dias_uteis_ano,
        )
    return PolicyIndicators(
        premio_termo=term_premium(focus, spot.valor) if focus else None,
        premio_dol=premio_dol,
        gap_focus=focus_gap(focus, spot.valor) if focus else None,
        vol30=vol30,
        vol90=vol90,
        regime=regime,
        limiar_regime=config.projecao.regime_ratio,
        referencia=spot.data,
    )


__all__ = [
    "compute_indicators",
    "focus_gap",
    "realized_volatility",
    "regime_signal",
    "term_premium",
    "window_drift",
    "window_volatility",
]
