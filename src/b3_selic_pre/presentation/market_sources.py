"""Constantes e funções puras das fontes de mercado."""

from __future__ import annotations

import bisect
from datetime import date
from typing import Any

from b3_selic_pre.application.market.forecast import FocusExpectation
from b3_selic_pre.application.market.series import derive_gold
from b3_selic_pre.domain.market import MarketQuote

SGS_SOURCE = "bcb_sgs_1"
B3_SOURCE = "b3_bdi"
GOLD_SOURCE = "ouro_derivado"
YAHOO_SOURCE = "yahoo_gc_f"
DOL_SOURCE = "dol_front"
FOCUS_SOURCE = "bcb_focus"
FOCUS_DOCUMENT = "focus.json"
WINDOW_DAYS = 365
FETCH_DAYS = 400
STALE_GAP_DAYS = 2
_MONTH_CODES = "FGHJKMNQUVXZ"


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}

def _focus_payload(
    expectations: list[FocusExpectation],
) -> dict[str, object]:
    return {
        "expectations": [
            {
                "ano": item.ano,
                "mediana": item.mediana,
                "minimo": item.minimo,
                "maximo": item.maximo,
            }
            for item in expectations
        ]
    }

def _parse_focus(payload: dict[str, Any]) -> list[FocusExpectation]:
    rows = payload.get("expectations")
    expectations: list[FocusExpectation] = []
    for row in rows if isinstance(rows, list) else []:
        data = _as_dict(row)
        try:
            expectations.append(
                FocusExpectation(
                    ano=int(data["ano"]),
                    mediana=float(data["mediana"]),
                    minimo=(
                        float(data["minimo"])
                        if data.get("minimo") is not None
                        else None
                    ),
                    maximo=(
                        float(data["maximo"])
                        if data.get("maximo") is not None
                        else None
                    ),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(expectations, key=lambda item: item.ano)

def _usd_on_or_before(
    dates: list[str], quotes: list[MarketQuote], target: str
) -> MarketQuote | None:
    index = bisect.bisect_right(dates, target) - 1
    if index < 0:
        return None
    candidate = quotes[index]
    if (date.fromisoformat(target) - date.fromisoformat(candidate.data)).days > 7:
        return None
    return candidate

def derive_gold_series(
    usd: list[MarketQuote], xau: list[MarketQuote]
) -> list[MarketQuote]:
    """Derive gold for every XAU/USD date with an available USD/BRL quote."""
    ordered_usd = sorted(usd, key=lambda quote: quote.data)
    dates = [quote.data for quote in ordered_usd]
    derived: list[MarketQuote] = []
    for quote in sorted(xau, key=lambda item: item.data):
        usd_quote = _usd_on_or_before(dates, ordered_usd, quote.data)
        if usd_quote is not None:
            derived.append(derive_gold(quote, usd_quote))
    return derived

def dol_ticker(reference: date) -> str:
    """Return the next-month DOL ticker for ``reference``."""
    total = reference.year * 12 + reference.month
    year, month_index = divmod(total, 12)
    month = month_index + 1
    return f"DOL{_MONTH_CODES[month - 1]}{str(year % 100).zfill(2)}"
