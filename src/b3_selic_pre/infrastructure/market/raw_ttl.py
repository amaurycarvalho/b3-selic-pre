"""TTL por recência das entradas brutas de mercado."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from b3_selic_pre.application.market.config import MarketConfig

if TYPE_CHECKING:
    from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _recent_days(config: object) -> int:
    resolucao = getattr(config, "resolucao", None)
    return int(getattr(resolucao, "diario_dias", 14))


def _recent_minutes(config: object) -> int:
    cache = getattr(config, "cache", None)
    return int(
        getattr(cache, "recente_minutos", None)
        or getattr(config, "recente_minutos", 20)
    )


def _month_minutes(config: object) -> int:
    cache = getattr(config, "cache", None)
    return int(
        getattr(cache, "mes_horas", None)
        or getattr(config, "mes_horas", 3)
    ) * 60


def _reference_business_day(ref: date, calendar: object | None) -> date:
    if calendar is None:
        return ref
    return calendar.calendar_for(ref.year).previous_business_day(ref)


def ttl_minutes(
    config: MarketConfig | object,
    data_date: str,
    reference: str | None = None,
    calendar: object | None = None,
) -> int | None:
    """Return the TTL for a data date, or ``None`` when immutable."""
    day = _parse_date(data_date)
    ref = _parse_date(reference or datetime.now(UTC).date().isoformat())
    if day is None or ref is None:
        return _recent_minutes(config)
    business_ref = _reference_business_day(ref, calendar)
    if (business_ref - day).days <= _recent_days(config):
        return _recent_minutes(config)
    if (day.year, day.month) == (ref.year, ref.month):
        return _month_minutes(config)
    return None


def is_fresh(
    cache: MarketRawCache,
    fonte: str,
    data: str,
    reference: str | None = None,
) -> bool:
    """Return whether a cached entry is still valid for its recency."""
    payload = cache.read(fonte, data)
    if payload is None:
        return False
    ttl = ttl_minutes(
        cache.config, data, reference, getattr(cache, "calendar", None)
    )
    if ttl is None:
        return True
    raw = payload.get("cached_at")
    if not isinstance(raw, str):
        return False
    try:
        cached_at = datetime.fromisoformat(raw)
    except ValueError:
        return False
    if cached_at.tzinfo is None:
        cached_at = cached_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - cached_at < timedelta(minutes=ttl)
