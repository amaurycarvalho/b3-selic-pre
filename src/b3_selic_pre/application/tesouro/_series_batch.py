"""Orquestração do pré-cálculo em lote das séries do Tesouro Direto."""

from __future__ import annotations

from b3_selic_pre.application.tesouro._series_demand import (
    build_demanda_snapshot,
)
from b3_selic_pre.application.tesouro._series_flow import build_fluxo_snapshot
from b3_selic_pre.application.tesouro._series_snapshot import (
    SeriesSourceSnapshot,
)
from b3_selic_pre.application.tesouro._series_stock import (
    build_estoque_snapshot,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)


def build_series_snapshots(
    vendas: list[VendaTesouroDireto] | tuple[VendaTesouroDireto, ...],
    resgates: list[ResgateTesouroDireto]
    | tuple[ResgateTesouroDireto, ...],
    estoque: list[EstoqueTesouroDireto]
    | tuple[EstoqueTesouroDireto, ...],
) -> dict[str, SeriesSourceSnapshot]:
    """Build each available source snapshot in a single pass per source."""
    snapshots: dict[str, SeriesSourceSnapshot] = {}
    stock = build_estoque_snapshot(estoque)
    if stock is not None:
        snapshots[stock.name] = stock
    demand = build_demanda_snapshot(vendas)
    if demand is not None:
        snapshots[demand.name] = demand
    flow = build_fluxo_snapshot(vendas, resgates)
    if flow is not None:
        snapshots[flow.name] = flow
    return snapshots


__all__ = [
    "SeriesSourceSnapshot",
    "build_demanda_snapshot",
    "build_estoque_snapshot",
    "build_fluxo_snapshot",
    "build_series_snapshots",
]
