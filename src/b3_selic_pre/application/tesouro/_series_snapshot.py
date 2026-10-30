"""Estruturas e utilitários do pré-cálculo de séries do Tesouro."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from b3_selic_pre.application.tesouro._percentuais import (
    JANELA_3_ANOS,
    inicio_janela,
)
from b3_selic_pre.application.tesouro._series_contract import (
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    SeriesPoint,
)
from b3_selic_pre.application.tesouro._taxonomia import classificar_familia

_CEM = Decimal(100)
NAME_ESTOQUE = "estoque"
NAME_DEMANDA = "demanda"
NAME_FLUXO = "fluxo"


@dataclass(frozen=True)
class SeriesSourceSnapshot:
    """Pontos pré-calculados de uma fonte, prontos para persistência."""

    name: str
    points: tuple[SeriesPoint, ...]
    latest_data_date: str
    titles: tuple[str, ...]


def percentual(value: Decimal, total: Decimal) -> Decimal:
    """Return the percentage of ``value`` over ``total``."""
    return (value / total * _CEM) if total else Decimal(0)


def anchor(latest_data_date: str) -> str:
    """Return a date usable as a window anchor."""
    if len(latest_data_date) == 10:
        return latest_data_date
    return f"{latest_data_date[:7]}-01"


def cutoff(latest_data_date: str) -> str:
    """Return the three-year retention cutoff for a latest date."""
    return inicio_janela(anchor(latest_data_date), JANELA_3_ANOS)


def ordered(points: list[SeriesPoint]) -> tuple[SeriesPoint, ...]:
    """Return points in a deterministic order."""
    return tuple(
        sorted(
            points,
            key=lambda item: (
                item.period,
                item.metric,
                item.dimension,
                item.key,
            ),
        )
    )


def keys(tipo_titulo: str) -> tuple[tuple[str, str], ...]:
    """Return the family and product keys of a title."""
    return (
        (DIMENSAO_FAMILIA, classificar_familia(tipo_titulo).familia),
        (DIMENSAO_PRODUTO, tipo_titulo),
    )


__all__ = [
    "NAME_DEMANDA",
    "NAME_ESTOQUE",
    "NAME_FLUXO",
    "SeriesSourceSnapshot",
    "anchor",
    "cutoff",
    "keys",
    "ordered",
    "percentual",
]
