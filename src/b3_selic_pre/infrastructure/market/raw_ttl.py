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


def ttl_minutes(
    config: MarketConfig, data_date: str, reference: str | None = None
) -> int | None:
    """Return the TTL for a data date, or ``None`` when immutable."""
    day = _parse_date(data_date)
    ref = _parse_date(reference or datetime.now(UTC).date().isoformat())
    if day is None or ref is None:
        return config.cache.recente_minutos
    if (ref - day).days <= config.resolucao.diario_dias:
        return config.cache.recente_minutos
    if (day.year, day.month) == (ref.year, ref.month):
        return config.cache.mes_horas * 60
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
    ttl = ttl_minutes(cache.config, data, reference)
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
