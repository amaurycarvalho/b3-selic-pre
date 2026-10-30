"""Agregação de séries em janelas para consumo pela apresentação."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from b3_selic_pre.application.tesouro._series_contract import SeriesPoint

_CEM = Decimal(100)


@dataclass(frozen=True)
class SeriesShare:
    """Participação agregada de uma chave em uma janela de séries."""

    key: str
    dimension: str
    value: Decimal
    total: Decimal
    percentual: Decimal


def agregar_series(
    points: Iterable[SeriesPoint],
    *,
    metrica_valor: str,
) -> list[SeriesShare]:
    """Aggregate value metrics over a window and return their share."""
    period_totals: dict[str, Decimal] = {}
    values: dict[tuple[str, str], Decimal] = {}
    for point in points:
        if point.metric != metrica_valor:
            continue
        period_totals[point.period] = point.total
        chave = (point.dimension, point.key)
        values[chave] = values.get(chave, Decimal(0)) + point.value
    total = sum(period_totals.values(), Decimal(0))
    return [
        SeriesShare(
            key=key,
            dimension=dimension,
            value=value,
            total=total,
            percentual=(value / total * _CEM) if total else Decimal(0),
        )
        for (dimension, key), value in sorted(values.items())
    ]
