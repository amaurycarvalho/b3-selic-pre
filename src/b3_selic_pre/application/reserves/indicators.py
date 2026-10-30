"""Indicadores determinísticos de direção das reservas internacionais."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from b3_selic_pre.application.reserves.config import ReservesConfig
from b3_selic_pre.application.reserves.metrics import (
    DIAS_UTEIS_ANO,
    average,
    classify_regime,
    drawdown,
    point_on_or_before,
    range_position,
    trend_90d,
    variation,
    window_points,
    window_points_months,
)
from b3_selic_pre.application.reserves.series import sort_points
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import (
    UNIDADE_RESERVAS_BILHOES,
    ReservesIndicators,
)


def compute_indicators(
    points: Sequence[MarketQuote],
    config: ReservesConfig | None = None,
) -> ReservesIndicators:
    """Compute every available metric over the daily reserves series."""
    settings = config or ReservesConfig()
    thresholds = settings.thresholds
    ordered = sort_points(points)
    if not ordered:
        return ReservesIndicators(thresholds=thresholds)
    latest = ordered[-1]
    reference = date.fromisoformat(latest.data)
    media = average(ordered, reference, thresholds.media_dias)
    drawdown_12m = drawdown(ordered, reference)
    maximum = window_points_months(ordered, reference, 12)
    max_value = max((point.valor for point in maximum), default=None)
    min_value = min((point.valor for point in maximum), default=None)
    above_average = (
        None if media is None else latest.valor >= media
    )
    var_3m = variation(ordered, reference, 3)
    return ReservesIndicators(
        nivel_atual=latest.valor / 1000,
        var_1m=variation(ordered, reference, 1),
        var_3m=var_3m,
        var_12m=variation(ordered, reference, 12),
        tendencia_90d=trend_90d(ordered, reference),
        drawdown_12m=drawdown_12m,
        posicao_faixa_12m=range_position(ordered, reference),
        media_90d=None if media is None else media / 1000,
        max_12m=None if max_value is None else max_value / 1000,
        min_12m=None if min_value is None else min_value / 1000,
        regime=classify_regime(
            var_3m, drawdown_12m, above_average, thresholds
        ),
        thresholds=thresholds,
        referencia=latest.data,
        unidade=UNIDADE_RESERVAS_BILHOES,
    )


regime_for = classify_regime


__all__ = [
    "DIAS_UTEIS_ANO",
    "average",
    "classify_regime",
    "compute_indicators",
    "drawdown",
    "point_on_or_before",
    "range_position",
    "regime_for",
    "trend_90d",
    "variation",
    "window_points",
    "window_points_months",
]
