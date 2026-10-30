"""Helpers de cache do cliente do Tesouro Direto."""

from __future__ import annotations

import logging
from collections.abc import Callable

from b3_selic_pre.application.tesouro import (
    TesouroDataError,
    parse_resgates,
    parse_vendas,
)
from b3_selic_pre.domain.models import VendaTesouroDireto
from b3_selic_pre.infrastructure.tesouro_cache import TesouroCache

logger = logging.getLogger(__name__)


def fallback(
    cache: TesouroCache, key: str, exc: Exception
) -> tuple[list[object], dict[str, object]] | None:
    """Reuse a previous resource cache when its download fails."""
    cached = cache.read()
    if cached is None:
        return None
    try:
        records = parse_resgates(cached[0], key)
    except TesouroDataError:
        return None
    logger.warning(
        "Recurso %s do Tesouro falhou; reutilizando cache: %s", key, exc
    )
    return records, cached[1]


def cached_value(
    cached: tuple[bytes, dict[str, object]] | None, key: str
) -> str | None:
    """Return a non-empty metadata string from the cached resource."""
    if cached is None:
        return None
    value = cached[1].get(key)
    return value if isinstance(value, str) and value else None


def from_cache(
    cached: tuple[bytes, dict[str, object]],
    source_callback: Callable[[str], None] | None,
) -> tuple[list[VendaTesouroDireto], dict[str, object], str]:
    """Parse sales from the cached CSV and report the cache origin."""
    sales = parse_vendas(cached[0])
    if source_callback:
        source_callback("Cache")
    return sales, cached[1], "cache"


__all__ = ["cached_value", "fallback", "from_cache"]
