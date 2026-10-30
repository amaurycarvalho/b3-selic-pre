"""Fluxo líquido calculado a partir de séries pré-calculadas."""

from __future__ import annotations

from decimal import Decimal

from b3_selic_pre.application.tesouro import (
    DIMENSAO_FAMILIA,
    FAMILIAS,
    METRICA_FLUXO_LIQUIDO,
    SeriesKey,
    SeriesProvider,
    bucket_para_janela,
    inicio_janela,
)


def fluxo_liquido_total(
    provider: SeriesProvider,
    latest_data_date: str | None,
    window: str,
) -> str | None:
    """Return the formatted net flow from precomputed series."""
    if latest_data_date is None or len(latest_data_date) != 10:
        return None
    start = inicio_janela(latest_data_date, window)
    bucket = bucket_para_janela(window)
    total = Decimal(0)
    for family in FAMILIAS:
        points = provider.fetch(
            SeriesKey(DIMENSAO_FAMILIA, family),
            start,
            latest_data_date,
            bucket,
        )
        total += sum(
            (
                point.value
                for point in points
                if point.metric == METRICA_FLUXO_LIQUIDO
            ),
            Decimal(0),
        )
    return f"{total:.2f}"


__all__ = ["fluxo_liquido_total"]
