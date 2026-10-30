"""Tipos, constantes e datas comuns aos cenários de mercado."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

from b3_selic_pre.domain.market import ForecastPoint

CENARIO_MERCADO = "Cenário de mercado"
CENARIO_ESTATISTICO = "Projeção estatística"
FOCUS_AUSENTE = "focus_ausente"
HISTORICO_INSUFICIENTE = "historico_insuficiente"


@dataclass(frozen=True)
class FocusExpectation:
    """Expectativa Focus anual para o câmbio."""

    ano: int
    mediana: float
    minimo: float | None = None
    maximo: float | None = None


@dataclass(frozen=True)
class ForecastOutcome:
    """Result of one forecast track, including an optional absence reason."""

    pontos: tuple[ForecastPoint, ...] = ()
    motivo: str | None = None

    @property
    def disponivel(self: ForecastOutcome) -> bool:
        """Return whether the outcome contains forecast points."""
        return bool(self.pontos)


def add_months(value: date, months: int) -> date:
    """Add calendar months, clamping to the last day of the target month."""
    total = value.year * 12 + (value.month - 1) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

