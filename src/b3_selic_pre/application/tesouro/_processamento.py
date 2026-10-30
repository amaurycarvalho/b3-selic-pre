"""Filtros, agregação, ordenação e período das vendas do Tesouro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from b3_selic_pre.application.tesouro._errors import (
    PeriodoInvalidoError,
)
from b3_selic_pre.application.tesouro._parsing import (
    normalizar_texto,
    parse_vendas,
)
from b3_selic_pre.domain.models import VendaTesouroDireto

DEFAULT_PERIOD_DAYS = 30

__all__ = [
    "DEFAULT_PERIOD_DAYS",
    "VendaAgregada",
    "agregar_por_titulo",
    "filtrar_por_periodo",
    "filtrar_por_titulo",
    "maior_data_liquidacao",
    "normalizar_texto",
    "ordenar_vendas",
    "parse_vendas",
    "periodo_padrao",
    "resolver_periodo",
    "validar_periodo",
]


@dataclass(frozen=True)
class VendaAgregada:
    """Totais de vendas por título."""

    tipo_titulo: str
    quantidade: Decimal
    valor: Decimal
    pu_medio: Decimal


def filtrar_por_titulo(
    sales: list[VendaTesouroDireto], titulo: str | None
) -> list[VendaTesouroDireto]:
    """Filter by a partial case/accent-insensitive title."""
    if not titulo:
        return list(sales)
    needle = normalizar_texto(titulo)
    return [
        sale
        for sale in sales
        if needle in normalizar_texto(sale.tipo_titulo)
    ]


def filtrar_por_periodo(
    sales: list[VendaTesouroDireto],
    inicio: str | None,
    fim: str | None,
) -> list[VendaTesouroDireto]:
    """Filter inclusively by ``data_liquidacao`` ISO strings."""
    return [
        sale
        for sale in sales
        if (inicio is None or sale.data_liquidacao >= inicio)
        and (fim is None or sale.data_liquidacao <= fim)
    ]


def maior_data_liquidacao(sales: list[VendaTesouroDireto]) -> str | None:
    """Return the newest settlement date, or ``None`` when empty."""
    if not sales:
        return None
    return max(sale.data_liquidacao for sale in sales)


def periodo_padrao(
    sales: list[VendaTesouroDireto], days: int = DEFAULT_PERIOD_DAYS
) -> tuple[str | None, str | None]:
    """Return the last ``days`` window ending at the newest settlement date."""
    latest = maior_data_liquidacao(sales)
    if latest is None:
        return None, None
    start = date.fromisoformat(latest) - timedelta(days=days)
    return start.isoformat(), latest


def resolver_periodo(
    sales: list[VendaTesouroDireto],
    inicio: str | None,
    fim: str | None,
) -> tuple[str | None, str | None]:
    """Resolve a partial period against the newest settlement date."""
    if inicio is None and fim is None:
        return periodo_padrao(sales)
    if inicio is None:
        start = date.fromisoformat(fim) - timedelta(days=DEFAULT_PERIOD_DAYS)
        return start.isoformat(), fim
    if fim is None:
        return inicio, maior_data_liquidacao(sales)
    return inicio, fim


def ordenar_vendas(
    sales: list[VendaTesouroDireto],
) -> list[VendaTesouroDireto]:
    """Sort deterministically by settlement desc and financial keys asc."""
    ordered = sorted(
        sales,
        key=lambda item: (item.tipo_titulo, item.vencimento, item.pu),
    )
    return sorted(ordered, key=lambda item: item.data_liquidacao, reverse=True)


def agregar_por_titulo(
    sales: list[VendaTesouroDireto],
) -> list[VendaAgregada]:
    """Sum quantity/value and compute the value/quantity weighted PU."""
    totals: dict[str, list[Decimal]] = {}
    for sale in sales:
        entry = totals.setdefault(sale.tipo_titulo, [Decimal(0), Decimal(0)])
        entry[0] += sale.quantidade
        entry[1] += sale.valor
    aggregates = [
        VendaAgregada(
            tipo_titulo=titulo,
            quantidade=value[0],
            valor=value[1],
            pu_medio=(value[1] / value[0] if value[0] else Decimal(0)),
        )
        for titulo, value in totals.items()
    ]
    return sorted(aggregates, key=lambda item: item.tipo_titulo)


def _validate_iso_date(value: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise PeriodoInvalidoError(
            f"Data inválida '{value}'. Use o formato AAAA-MM-DD."
        ) from exc
    if parsed.isoformat() != value:
        raise PeriodoInvalidoError(
            f"Data inválida '{value}'. Use o formato AAAA-MM-DD."
        )


def validar_periodo(inicio: str | None, fim: str | None) -> None:
    """Validate ISO period bounds and ordering."""
    for value in (inicio, fim):
        if value is not None:
            _validate_iso_date(value)
    if inicio is not None and fim is not None and inicio > fim:
        raise PeriodoInvalidoError(
            "--inicio não pode ser maior que --fim."
        )
