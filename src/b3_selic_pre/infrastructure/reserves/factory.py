"""Fábrica de adaptadores e caches de reservas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from b3_selic_pre.application.reserves.config import ReservesConfig
from b3_selic_pre.infrastructure.market.precompute_cache import (
    MarketPrecomputeCache,
)
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache
from b3_selic_pre.infrastructure.reserves.adapter import BcbReservesClient

RESERVES_NAMESPACE = "reservas"


@dataclass
class ReservesServices:
    """Adaptadores e caches usados pela GUI, CLI e MCP."""

    config: ReservesConfig
    source: object
    raw: MarketRawCache
    precompute: MarketPrecomputeCache


def build_reserves_services(
    cache_dir: str | Path | None = None,
    config: ReservesConfig | None = None,
    *,
    source: object | None = None,
    raw: MarketRawCache | None = None,
    precompute: MarketPrecomputeCache | None = None,
) -> ReservesServices:
    """Build reserves services, allowing fake adapters for tests."""
    reserves_config = config or ReservesConfig()
    raw_cache = raw or MarketRawCache(cache_dir)
    precompute_cache = precompute or MarketPrecomputeCache(
        cache_dir, namespace=RESERVES_NAMESPACE
    )
    return ReservesServices(
        config=reserves_config,
        source=source if source is not None else BcbReservesClient(),
        raw=raw_cache,
        precompute=precompute_cache,
    )


__all__ = [
    "RESERVES_NAMESPACE",
    "ReservesServices",
    "build_reserves_services",
]
