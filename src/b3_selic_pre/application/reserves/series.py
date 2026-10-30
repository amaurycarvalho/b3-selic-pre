"""Parsing, mescla incremental, janela e hash canônico das reservas."""

from __future__ import annotations

import calendar
from collections.abc import Sequence
from datetime import date, timedelta

from b3_selic_pre.application.reserves.config import RETENCAO_ANOS
from b3_selic_pre.application.reserves.hashing import (
    canonical_pairs,
    points_hash,
    snapshot_hash,
)
from b3_selic_pre.application.reserves.parsing import (
    normalize_points,
    parse_bcb_points,
    parse_reserves,
    parse_reserves_sgs,
    parse_value,
    sort_points,
)
from b3_selic_pre.domain.market import MarketQuote


def shift_months(value: date, months: int) -> date:
    """Shift a date by whole months, clamping the day."""
    total = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(value.day, last_day))


def _is_business_day(current: date, calendar: object | None) -> bool:
    if calendar is None:
        return current.weekday() < 5
    return calendar.calendar_for(current.year).is_business_day(current)


def incremental_start(
    last_date: str,
    overlap_days: int = 5,
    calendar: object | None = None,
) -> str:
    """Return the start date, receding ``overlap_days`` business days."""
    try:
        current = date.fromisoformat(last_date)
    except (TypeError, ValueError):
        return last_date
    remaining = max(0, overlap_days)
    while remaining > 0:
        current -= timedelta(days=1)
        if _is_business_day(current, calendar):
            remaining -= 1
    return current.isoformat()


def merge_points(
    existing: Sequence[MarketQuote],
    incoming: Sequence[MarketQuote],
    reference: str | None = None,
    years: int | None = None,
) -> list[MarketQuote]:
    """Merge by date, letting revised incoming values replace old ones."""
    merged: dict[str, MarketQuote] = {
        point.data: point for point in sort_points(existing)
    }
    for point in sort_points(incoming):
        merged[point.data] = point
    result = [merged[key] for key in sorted(merged)]
    if years is None:
        return result
    return retained_points(result, reference, years)


def retained_points(
    points: Sequence[MarketQuote],
    reference: str | None = None,
    years: int = RETENCAO_ANOS,
) -> list[MarketQuote]:
    """Return points inside the retention window ending at the newest date."""
    ordered = sort_points(points)
    if not ordered:
        return []
    reference_date = _reference_date(reference, ordered[-1].data)
    if reference_date is None:
        return ordered
    try:
        cutoff = reference_date.replace(year=reference_date.year - years)
    except ValueError:
        cutoff = reference_date.replace(
            year=reference_date.year - years, day=28
        )
    return [
        point
        for point in ordered
        if date.fromisoformat(point.data) >= cutoff
    ]


def _reference_date(value: str | None, fallback: str) -> date | None:
    for candidate in (value, fallback):
        if candidate is None:
            continue
        try:
            return date.fromisoformat(candidate)
        except (TypeError, ValueError):
            continue
    return None


def window_bounds(
    points: Sequence[MarketQuote],
    months: int,
    reference: str | None = None,
) -> tuple[str, str]:
    """Return the inclusive window ending at the newest available date."""
    ordered = sort_points(points)
    end = reference or (ordered[-1].data if ordered else "")
    if not end:
        return "", ""
    try:
        parsed = date.fromisoformat(end)
    except (TypeError, ValueError):
        return "", end
    return shift_months(parsed, -months).isoformat(), end


def filter_window(
    points: Sequence[MarketQuote], inicio: str, fim: str
) -> list[MarketQuote]:
    """Return points inside an inclusive date window."""
    return [
        point for point in sort_points(points) if inicio <= point.data <= fim
    ]


__all__ = [
    "canonical_pairs",
    "filter_window",
    "incremental_start",
    "merge_points",
    "normalize_points",
    "parse_bcb_points",
    "parse_reserves",
    "parse_reserves_sgs",
    "parse_value",
    "points_hash",
    "retained_points",
    "shift_months",
    "snapshot_hash",
    "sort_points",
    "window_bounds",
]
