"""Parsing e normalização dos pontos do BCB SGS 13621."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import datetime

from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import (
    ATIVO_RESERVAS,
    FONTE_RESERVAS,
    METODO_RESERVAS,
    UNIDADE_RESERVAS,
)


def _parse_br(value: str) -> str:
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


def parse_value(value: object) -> float | None:
    """Parse a BCB numeric string with Brazilian or plain separators."""
    if value is None:
        return None
    text = str(value).strip()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _rows(payload: object) -> list[object]:
    if isinstance(payload, (bytes, str)):
        try:
            decoded = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return []
        return decoded if isinstance(decoded, list) else []
    return list(payload) if isinstance(payload, list) else []


def sort_points(points: Sequence[MarketQuote]) -> list[MarketQuote]:
    """Return valid, finite points sorted by date."""
    valid = [
        point
        for point in points
        if point.data and math.isfinite(point.valor)
    ]
    return sorted(valid, key=lambda point: point.data)


def parse_reserves_sgs(
    payload: object, extraido_em: str = ""
) -> list[MarketQuote]:
    """Parse an SGS 13621 JSON fixture into reserves quotes in US$ millions."""
    quotes: list[MarketQuote] = []
    for row in _rows(payload):
        if not isinstance(row, Mapping):
            continue
        raw_date = row.get("data")
        valor = parse_value(row.get("valor"))
        if not isinstance(raw_date, str) or valor is None:
            continue
        try:
            day = _parse_br(raw_date)
        except ValueError:
            continue
        quotes.append(
            MarketQuote(
                data=day,
                ativo=ATIVO_RESERVAS,
                valor=valor,
                unidade=UNIDADE_RESERVAS,
                origem=FONTE_RESERVAS,
                metodo=METODO_RESERVAS,
                extraido_em=extraido_em,
            )
        )
    return sort_points(quotes)


parse_reserves = parse_reserves_sgs
parse_bcb_points = parse_reserves_sgs
normalize_points = parse_reserves_sgs


__all__ = [
    "normalize_points",
    "parse_bcb_points",
    "parse_reserves",
    "parse_reserves_sgs",
    "parse_value",
    "sort_points",
]
