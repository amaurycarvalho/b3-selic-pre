"""Índice e lacunas do cache bruto de mercado."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def last_date(cache: MarketRawCache, fonte: str | None = None) -> str | None:
    """Return the newest valid date, optionally for one source."""
    directories = (
        [cache.raw_dir / fonte]
        if fonte is not None
        else sorted(
            path for path in cache.raw_dir.glob("*") if path.is_dir()
        )
        if cache.raw_dir.exists()
        else []
    )
    dates: list[str] = []
    for directory in directories:
        if not directory.exists():
            continue
        for target in directory.glob("*.json"):
            if _parse_date(target.stem) is not None:
                dates.append(target.stem)
    return max(dates) if dates else None


def _business_day(
    current: date, calendar: object | None
) -> bool:
    if calendar is None:
        return current.weekday() < 5
    return calendar.calendar_for(current.year).is_business_day(current)


def missing_dates(
    cache: MarketRawCache, fonte: str, inicio: str, fim: str
) -> list[str]:
    """Return business days in the window without a cache entry."""
    start = _parse_date(inicio)
    end = _parse_date(fim)
    if start is None or end is None or start > end:
        return []
    calendar = getattr(cache, "calendar", None)
    missing: list[str] = []
    current = start
    while current <= end:
        if _business_day(current, calendar) and not cache.path(
            fonte, current.isoformat()
        ).exists():
            missing.append(current.isoformat())
        current += timedelta(days=1)
    return missing
