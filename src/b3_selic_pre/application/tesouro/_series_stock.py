"""Pré-cálculo da série mensal de estoque do Tesouro Direto."""

from __future__ import annotations

from decimal import Decimal

from b3_selic_pre.application.tesouro._series_contract import (
    METRICA_ESTOQUE_PCT,
    METRICA_ESTOQUE_VALOR,
    SeriesPoint,
)
from b3_selic_pre.application.tesouro._series_snapshot import (
    NAME_ESTOQUE,
    SeriesSourceSnapshot,
    cutoff,
    keys,
    ordered,
    percentual,
)
from b3_selic_pre.domain.models import EstoqueTesouroDireto


def _stock_points(records: list[EstoqueTesouroDireto]) -> list[SeriesPoint]:
    totals: dict[str, Decimal] = {}
    sums: dict[tuple[str, str, str], Decimal] = {}
    for item in records:
        totals[item.mes] = totals.get(item.mes, Decimal(0)) + (
            item.valor_estoque
        )
        for dimension, key in keys(item.tipo_titulo):
            sums[(dimension, key, item.mes)] = sums.get(
                (dimension, key, item.mes), Decimal(0)
            ) + item.valor_estoque
    points: list[SeriesPoint] = []
    for (dimension, key, period), value in sums.items():
        total = totals[period]
        points.append(
            SeriesPoint(
                period,
                METRICA_ESTOQUE_PCT,
                percentual(value, total),
                total,
                dimension,
                key,
            )
        )
        points.append(
            SeriesPoint(
                period,
                METRICA_ESTOQUE_VALOR,
                value,
                total,
                dimension,
                key,
            )
        )
    return points


def build_estoque_snapshot(
    estoque: list[EstoqueTesouroDireto] | tuple[EstoqueTesouroDireto, ...],
) -> SeriesSourceSnapshot | None:
    """Build the retained monthly stock series from parsed stock records."""
    if not estoque:
        return None
    latest = max(item.mes for item in estoque)
    start = cutoff(latest)[:7]
    records = [item for item in estoque if start <= item.mes <= latest]
    if not records:
        return None
    titles = tuple(sorted({item.tipo_titulo for item in records}))
    return SeriesSourceSnapshot(
        NAME_ESTOQUE,
        ordered(_stock_points(records)),
        latest,
        titles,
    )


__all__ = ["build_estoque_snapshot"]
