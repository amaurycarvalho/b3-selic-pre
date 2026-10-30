"""Pré-cálculo da série diária de fluxo líquido do Tesouro Direto."""

from __future__ import annotations

from decimal import Decimal

from b3_selic_pre.application.tesouro._series_contract import (
    METRICA_FLUXO_LIQUIDO,
    SeriesPoint,
)
from b3_selic_pre.application.tesouro._series_snapshot import (
    NAME_FLUXO,
    SeriesSourceSnapshot,
    cutoff,
    keys,
    ordered,
)
from b3_selic_pre.domain.models import (
    ResgateTesouroDireto,
    VendaTesouroDireto,
)


def _flow_points(
    sales: list[VendaTesouroDireto],
    redemptions: list[ResgateTesouroDireto],
) -> list[SeriesPoint]:
    totals: dict[str, Decimal] = {}
    sale_values: dict[tuple[str, str, str], Decimal] = {}
    redemption_values: dict[tuple[str, str, str], Decimal] = {}
    for item in sales:
        period = item.data_liquidacao
        totals[period] = totals.get(period, Decimal(0)) + item.valor
        for dimension, key in keys(item.tipo_titulo):
            sale_values[(dimension, key, period)] = sale_values.get(
                (dimension, key, period), Decimal(0)
            ) + item.valor
    for item in redemptions:
        period = item.data_resgate
        for dimension, key in keys(item.tipo_titulo):
            redemption_values[(dimension, key, period)] = (
                redemption_values.get((dimension, key, period), Decimal(0))
                + item.valor
            )
    points: list[SeriesPoint] = []
    for dimension, key, period in sorted(
        set(sale_values) | set(redemption_values)
    ):
        points.append(
            SeriesPoint(
                period,
                METRICA_FLUXO_LIQUIDO,
                sale_values.get((dimension, key, period), Decimal(0))
                - redemption_values.get(
                    (dimension, key, period), Decimal(0)
                ),
                totals.get(period, Decimal(0)),
                dimension,
                key,
            )
        )
    return points


def _latest(
    vendas: list[VendaTesouroDireto] | tuple[VendaTesouroDireto, ...],
    resgates: list[ResgateTesouroDireto]
    | tuple[ResgateTesouroDireto, ...],
) -> str | None:
    dates = [item.data_liquidacao for item in vendas]
    dates.extend(item.data_resgate for item in resgates)
    return max(dates) if dates else None


def _sales_window(
    vendas: list[VendaTesouroDireto] | tuple[VendaTesouroDireto, ...],
    start: str,
    end: str,
) -> list[VendaTesouroDireto]:
    return [
        item
        for item in vendas
        if start <= item.data_liquidacao <= end
    ]


def _redemptions_window(
    resgates: list[ResgateTesouroDireto]
    | tuple[ResgateTesouroDireto, ...],
    start: str,
    end: str,
) -> list[ResgateTesouroDireto]:
    return [
        item
        for item in resgates
        if item.tipo_resgate == "recompra"
        and start <= item.data_resgate <= end
    ]


def _titles(
    sales: list[VendaTesouroDireto],
    redemptions: list[ResgateTesouroDireto],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {item.tipo_titulo for item in sales}
            | {item.tipo_titulo for item in redemptions}
        )
    )


def build_fluxo_snapshot(
    vendas: list[VendaTesouroDireto] | tuple[VendaTesouroDireto, ...],
    resgates: list[ResgateTesouroDireto]
    | tuple[ResgateTesouroDireto, ...],
) -> SeriesSourceSnapshot | None:
    """Build the retained daily net-flow series from sales and redemptions."""
    latest = _latest(vendas, resgates)
    if latest is None:
        return None
    start = cutoff(latest)[:10]
    sales = _sales_window(vendas, start, latest)
    redemptions = _redemptions_window(resgates, start, latest)
    return SeriesSourceSnapshot(
        NAME_FLUXO,
        ordered(_flow_points(sales, redemptions)),
        latest,
        _titles(sales, redemptions),
    )


__all__ = ["build_fluxo_snapshot"]
