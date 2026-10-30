"""Itens e lacunas de mercado usados pelas tools MCP."""

from __future__ import annotations

from datetime import date, timedelta


def market_items(payload: dict[str, object]) -> list[dict[str, object]]:
    """Return every serialized market item ordered by date and asset."""
    series = payload.get("series")
    items: list[dict[str, object]] = []
    for data in (series if isinstance(series, dict) else {}).values():
        if isinstance(data, dict):
            items.extend(
                item
                for item in data.get("itens", []) or []
                if isinstance(item, dict)
            )
    return sorted(
        items,
        key=lambda item: (str(item.get("data")), str(item.get("ativo"))),
    )


def _is_business_day(current: date, calendar: object | None) -> bool:
    if calendar is None:
        return current.weekday() < 5
    return calendar.calendar_for(current.year).is_business_day(current)


def missing_market_dates(
    payload: dict[str, object],
    inicio: str,
    fim: str,
    calendar: object | None = None,
) -> list[str]:
    """Return business days without a market point, ignoring holidays."""
    present = {str(item.get("data")) for item in market_items(payload)}
    try:
        current = date.fromisoformat(inicio)
        end = date.fromisoformat(fim)
    except ValueError:
        return []
    missing: list[str] = []
    while current <= end:
        if (
            _is_business_day(current, calendar)
            and current.isoformat() not in present
        ):
            missing.append(current.isoformat())
        current += timedelta(days=1)
    return missing


__all__ = ["market_items", "missing_market_dates"]
