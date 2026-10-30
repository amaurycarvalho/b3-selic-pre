"""Filtros, agregação e ordenação dos resgates do Tesouro Direto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from b3_selic_pre.application.tesouro._processamento import (
    DEFAULT_PERIOD_DAYS,
    filtrar_por_titulo_generico,
)
from b3_selic_pre.domain.models import ResgateTesouroDireto


@dataclass(frozen=True)
class ResgateAgregado:
    """Totais de resgates por tipo de resgate e título."""

    tipo_resgate: str
    tipo_titulo: str
    quantidade: Decimal
    valor: Decimal
    pu_medio: Decimal | None


def filtrar_resgates_por_tipo(
    records: list[ResgateTesouroDireto], tipo_resgate: str | None
) -> list[ResgateTesouroDireto]:
    """Filter by an exact redemption type."""
    if not tipo_resgate:
        return list(records)
    return [item for item in records if item.tipo_resgate == tipo_resgate]


def filtrar_resgates_por_titulo(
    records: list[ResgateTesouroDireto], titulo: str | None
) -> list[ResgateTesouroDireto]:
    """Filter by a partial case/accent-insensitive title."""
    return filtrar_por_titulo_generico(records, titulo)


def filtrar_resgates_por_periodo(
    records: list[ResgateTesouroDireto],
    inicio: str | None,
    fim: str | None,
) -> list[ResgateTesouroDireto]:
    """Filter inclusively by ``data_resgate`` ISO strings."""
    return [
        item
        for item in records
        if (inicio is None or item.data_resgate >= inicio)
        and (fim is None or item.data_resgate <= fim)
    ]


def maior_data_resgate(
    records: list[ResgateTesouroDireto],
) -> str | None:
    """Return the newest redemption date, or ``None`` when empty."""
    if not records:
        return None
    return max(item.data_resgate for item in records)


def periodo_padrao_resgates(
    records: list[ResgateTesouroDireto], days: int = DEFAULT_PERIOD_DAYS
) -> tuple[str | None, str | None]:
    """Return the last ``days`` window ending at the newest redemption."""
    latest = maior_data_resgate(records)
    if latest is None:
        return None, None
    start = date.fromisoformat(latest) - timedelta(days=days)
    return start.isoformat(), latest


def resolver_periodo_resgates(
    records: list[ResgateTesouroDireto],
    inicio: str | None,
    fim: str | None,
) -> tuple[str | None, str | None]:
    """Resolve a partial period against the newest redemption date."""
    if inicio is None and fim is None:
        return periodo_padrao_resgates(records)
    if inicio is None:
        start = date.fromisoformat(fim) - timedelta(days=DEFAULT_PERIOD_DAYS)
        return start.isoformat(), fim
    if fim is None:
        return inicio, maior_data_resgate(records)
    return inicio, fim


def _pu_key(item: ResgateTesouroDireto) -> Decimal:
    return item.pu if item.pu is not None else Decimal(0)


def ordenar_resgates(
    records: list[ResgateTesouroDireto],
) -> list[ResgateTesouroDireto]:
    """Sort by redemption desc and financial keys asc."""
    ordered = sorted(
        records,
        key=lambda item: (
            item.tipo_resgate,
            item.tipo_titulo,
            item.vencimento,
            _pu_key(item),
        ),
    )
    return sorted(ordered, key=lambda item: item.data_resgate, reverse=True)


def agregar_resgates(
    records: list[ResgateTesouroDireto],
) -> list[ResgateAgregado]:
    """Sum quantity/value and compute PU only when every row has one."""
    totals: dict[tuple[str, str], list[object]] = {}
    for item in records:
        key = (item.tipo_resgate, item.tipo_titulo)
        entry = totals.setdefault(key, [Decimal(0), Decimal(0), True])
        entry[0] += item.quantidade
        entry[1] += item.valor
        entry[2] = entry[2] and item.pu is not None
    aggregates = [
        ResgateAgregado(
            tipo_resgate=key[0],
            tipo_titulo=key[1],
            quantidade=value[0],
            valor=value[1],
            pu_medio=(
                value[1] / value[0]
                if value[2] and value[0]
                else None
            ),
        )
        for key, value in totals.items()
    ]
    return sorted(
        aggregates, key=lambda item: (item.tipo_resgate, item.tipo_titulo)
    )
