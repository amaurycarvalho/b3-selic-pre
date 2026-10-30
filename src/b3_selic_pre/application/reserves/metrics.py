"""Métricas individuais e regime determinístico das reservas."""

from __future__ import annotations

import bisect
import math
from collections.abc import Sequence
from datetime import date, timedelta

from b3_selic_pre.application.reserves.series import (
    shift_months,
    sort_points,
)
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import (
    ReservesRegime,
    ReservesThresholds,
)

DIAS_UTEIS_ANO = 252


def _by_date(points: Sequence[MarketQuote]) -> list[MarketQuote]:
    return sort_points(points)


def point_on_or_before(
    points: Sequence[MarketQuote], target: date
) -> MarketQuote | None:
    """Return the newest point at or before ``target``, without interpolation."""
    ordered = _by_date(points)
    dates = [point.data for point in ordered]
    index = bisect.bisect_right(dates, target.isoformat()) - 1
    return ordered[index] if index >= 0 else None


def window_points(
    points: Sequence[MarketQuote], reference: date, days: int
) -> list[MarketQuote]:
    """Return points inside the trailing ``days`` calendar window."""
    cutoff = reference - timedelta(days=days)
    return [
        point
        for point in _by_date(points)
        if date.fromisoformat(point.data) > cutoff
    ]


def window_points_months(
    points: Sequence[MarketQuote], reference: date, months: int
) -> list[MarketQuote]:
    """Return points inside the trailing ``months`` window."""
    cutoff = shift_months(reference, -months)
    return [
        point
        for point in _by_date(points)
        if date.fromisoformat(point.data) > cutoff
    ]


def variation(
    points: Sequence[MarketQuote], reference: date, months: int
) -> float | None:
    """Return the percent variation over ``months`` without interpolation."""
    ordered = _by_date(points)
    if not ordered:
        return None
    target = point_on_or_before(ordered, shift_months(reference, -months))
    latest = ordered[-1]
    if target is None or target.valor <= 0:
        return None
    return (latest.valor / target.valor - 1) * 100


def trend_90d(
    points: Sequence[MarketQuote], reference: date, days: int = 90
) -> float | None:
    """Return the annualized OLS slope of log levels in the trailing window."""
    sample = window_points(points, reference, days)
    pairs = [
        (date.fromisoformat(point.data), point.valor)
        for point in sample
        if point.valor > 0
    ]
    if len(pairs) < 2:
        return None
    origin = pairs[0][0]
    xs = [(day - origin).days for day, _ in pairs]
    ys = [math.log(value) for _, value in pairs]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return None
    slope = (
        sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        / denominator
    )
    return slope * DIAS_UTEIS_ANO * 100


def drawdown(
    points: Sequence[MarketQuote], reference: date, months: int = 12
) -> float | None:
    """Return the percent drawdown from the window maximum."""
    sample = window_points_months(points, reference, months)
    if not sample:
        return None
    highest = max(point.valor for point in sample)
    if highest == 0:
        return None
    return (sample[-1].valor / highest - 1) * 100


def range_position(
    points: Sequence[MarketQuote], reference: date, months: int = 12
) -> float | None:
    """Return the position of the latest value inside the window range."""
    sample = window_points_months(points, reference, months)
    if len(sample) < 2:
        return None
    lowest = min(point.valor for point in sample)
    highest = max(point.valor for point in sample)
    if highest <= lowest:
        return None
    return (sample[-1].valor - lowest) / (highest - lowest)


def average(
    points: Sequence[MarketQuote], reference: date, days: int
) -> float | None:
    """Return the mean level in the trailing window."""
    sample = window_points(points, reference, days)
    if not sample:
        return None
    return sum(point.valor for point in sample) / len(sample)


def classify_regime(
    var_3m: float | None,
    drawdown_12m: float | None,
    above_average: bool | None,
    thresholds: ReservesThresholds | None = None,
) -> ReservesRegime | None:
    """Classify the deterministic regime from the available metrics."""
    if var_3m is None:
        return None
    limits = thresholds or ReservesThresholds()
    if var_3m > limits.var_aumento and above_average:
        return ReservesRegime.AUMENTO
    if (
        var_3m < limits.var_deterioracao
        and drawdown_12m is not None
        and drawdown_12m <= limits.drawdown
    ):
        return ReservesRegime.DETERIORACAO
    return ReservesRegime.ESTAVEL


__all__ = [
    "DIAS_UTEIS_ANO",
    "average",
    "classify_regime",
    "drawdown",
    "point_on_or_before",
    "range_position",
    "trend_90d",
    "variation",
    "window_points",
    "window_points_months",
]
