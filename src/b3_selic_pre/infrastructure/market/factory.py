"""Fábrica de adaptadores e caches de mercado."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.infrastructure.market.b3_client import B3MarketClient
from b3_selic_pre.infrastructure.market.bcb_client import (
    BcbFocusClient,
    BcbSgsClient,
)
from b3_selic_pre.infrastructure.market.gold_client import GoldUsdClient
from b3_selic_pre.infrastructure.market.precompute_cache import (
    MarketPrecomputeCache,
)
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache


@dataclass
class MarketServices:
    """Adaptadores e caches usados pela GUI, CLI e MCP."""

    config: MarketConfig
    sgs: object
    focus: object
    b3: object
    gold: object
    raw: MarketRawCache
    precompute: MarketPrecomputeCache


def build_market_services(
    cache_dir: str | Path | None = None,
    config: MarketConfig | None = None,
    *,
    sgs: object | None = None,
    focus: object | None = None,
    b3: object | None = None,
    gold: object | None = None,
    raw: MarketRawCache | None = None,
    precompute: MarketPrecomputeCache | None = None,
) -> MarketServices:
    """Build the market services, allowing fake adapters for tests."""
    market_config = config or MarketConfig()
    raw_cache = raw or MarketRawCache(cache_dir, market_config)
    precompute_cache = precompute or MarketPrecomputeCache(
        cache_dir, market_config
    )
    return MarketServices(
        config=market_config,
        sgs=sgs if sgs is not None else BcbSgsClient(),
        focus=focus if focus is not None else BcbFocusClient(),
        b3=b3 if b3 is not None else B3MarketClient(),
        gold=gold if gold is not None else GoldUsdClient(),
        raw=raw_cache,
        precompute=precompute_cache,
    )


__all__ = ["MarketServices", "build_market_services"]
