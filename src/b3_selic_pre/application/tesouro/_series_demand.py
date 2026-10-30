"""Pré-cálculo da série diária de demanda do Tesouro Direto."""

from __future__ import annotations

from decimal import Decimal

from b3_selic_pre.application.tesouro._series_contract import (
    METRICA_DEMANDA_PCT,
    METRICA_DEMANDA_VALOR,
    SeriesPoint,
)
from b3_selic_pre.application.tesouro._series_snapshot import (
    NAME_DEMANDA,
    SeriesSourceSnapshot,
    cutoff,
    keys,
    ordered,
    percentual,
)
from b3_selic_pre.domain.models import VendaTesouroDireto


def _demand_points(records: list[VendaTesouroDireto]) -> list[SeriesPoint]:
    totals: dict[str, Decimal] = {}
    sums: dict[tuple[str, str, str], Decimal] = {}
    for item in records:
        period = item.data_liquidacao
        totals[period] = totals.get(period, Decimal(0)) + item.valor
        for dimension, key in keys(item.tipo_titulo):
            sums[(dimension, key, period)] = sums.get(
                (dimension, key, period), Decimal(0)
            ) + item.valor
    points: list[SeriesPoint] = []
    for (dimension, key, period), value in sums.items():
        total = totals[period]
        points.append(
            SeriesPoint(
                period,
                METRICA_DEMANDA_PCT,
                percentual(value, total),
                total,
                dimension,
                key,
            )
        )
        points.append(
            SeriesPoint(
                period,
                METRICA_DEMANDA_VALOR,
                value,
                total,
                dimension,
                key,
            )
        )
    return points


def build_demanda_snapshot(
    vendas: list[VendaTesouroDireto] | tuple[VendaTesouroDireto, ...],
) -> SeriesSourceSnapshot | None:
    """Build the retained daily sales series from parsed sales records."""
    if not vendas:
        return None
    latest = max(item.data_liquidacao for item in vendas)
    start = cutoff(latest)[:10]
    records = [
        item
        for item in vendas
        if start <= item.data_liquidacao <= latest
    ]
    if not records:
        return None
    titles = tuple(sorted({item.tipo_titulo for item in records}))
    return SeriesSourceSnapshot(
        NAME_DEMANDA,
        ordered(_demand_points(records)),
        latest,
        titles,
    )


__all__ = ["build_demanda_snapshot"]
