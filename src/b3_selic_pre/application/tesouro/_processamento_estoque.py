"""Filtros, agregação e ordenação do estoque do Tesouro Direto."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from b3_selic_pre.application.tesouro._errors import PeriodoInvalidoError
from b3_selic_pre.application.tesouro._processamento import (
    filtrar_por_titulo_generico,
)
from b3_selic_pre.domain.models import EstoqueTesouroDireto

_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class EstoqueAgregado:
    """Totais de estoque por título dentro de um único mês."""

    tipo_titulo: str
    quantidade: Decimal
    valor_estoque: Decimal
    pu_medio: Decimal


def _validar_mes(value: str) -> None:
    if _MONTH.match(value) is None:
        raise PeriodoInvalidoError(
            f"Mês inválido '{value}'. Use o formato AAAA-MM."
        )


def validar_meses(inicio: str | None, fim: str | None) -> None:
    """Validate month bounds and ordering."""
    for value in (inicio, fim):
        if value is not None:
            _validar_mes(value)
    if inicio is not None and fim is not None and inicio > fim:
        raise PeriodoInvalidoError("--inicio não pode ser maior que --fim.")


def filtrar_estoque_por_titulo(
    records: list[EstoqueTesouroDireto], titulo: str | None
) -> list[EstoqueTesouroDireto]:
    """Filter by a partial case/accent-insensitive title."""
    return filtrar_por_titulo_generico(records, titulo)


def filtrar_estoque_por_periodo(
    records: list[EstoqueTesouroDireto],
    inicio: str | None,
    fim: str | None,
) -> list[EstoqueTesouroDireto]:
    """Filter inclusively by ``mes`` strings."""
    return [
        item
        for item in records
        if (inicio is None or item.mes >= inicio)
        and (fim is None or item.mes <= fim)
    ]


def ultimo_mes(records: list[EstoqueTesouroDireto]) -> str | None:
    """Return the newest month, or ``None`` when empty."""
    if not records:
        return None
    return max(item.mes for item in records)


def resolver_periodo_estoque(
    records: list[EstoqueTesouroDireto],
    inicio: str | None,
    fim: str | None,
    mes: str | None,
) -> tuple[str | None, str | None]:
    """Resolve the selected month interval, defaulting to the last month."""
    if mes is not None:
        return mes, mes
    if inicio is None and fim is None:
        latest = ultimo_mes(records)
        return latest, latest
    return inicio, fim


def meses_presentes(
    records: list[EstoqueTesouroDireto],
) -> list[str]:
    """Return distinct months in ascending order."""
    return sorted({item.mes for item in records})


def ordenar_estoque(
    records: list[EstoqueTesouroDireto],
) -> list[EstoqueTesouroDireto]:
    """Sort by month desc and financial keys asc."""
    ordered = sorted(
        records,
        key=lambda item: (item.tipo_titulo, item.vencimento, item.pu),
    )
    return sorted(ordered, key=lambda item: item.mes, reverse=True)


def agregar_estoque(
    records: list[EstoqueTesouroDireto],
) -> list[EstoqueAgregado]:
    """Aggregate by title within a single month, never across months."""
    if len(meses_presentes(records)) > 1:
        raise PeriodoInvalidoError(
            "A agregação de estoque exige um único mês."
        )
    totals: dict[str, list[Decimal]] = {}
    for item in records:
        entry = totals.setdefault(
            item.tipo_titulo, [Decimal(0), Decimal(0)]
        )
        entry[0] += item.quantidade
        entry[1] += item.valor_estoque
    aggregates = [
        EstoqueAgregado(
            tipo_titulo=titulo,
            quantidade=value[0],
            valor_estoque=value[1],
            pu_medio=(value[1] / value[0] if value[0] else Decimal(0)),
        )
        for titulo, value in totals.items()
    ]
    return sorted(aggregates, key=lambda item: item.tipo_titulo)
