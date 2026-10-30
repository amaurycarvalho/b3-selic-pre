"""Controlador headless da sub-aba Dólar e Ouro (sem Tkinter)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.presentation.market_payload import PayloadMixin
from b3_selic_pre.presentation.market_refresh import RefreshMixin
from b3_selic_pre.presentation.market_sources import (
    B3_SOURCE,
    DOL_SOURCE,
    FOCUS_SOURCE,
    GOLD_SOURCE,
    SGS_SOURCE,
    YAHOO_SOURCE,
    derive_gold_series,
    dol_ticker,
)
from b3_selic_pre.presentation.market_view_model import MarketOptions


class MarketTabController(PayloadMixin, RefreshMixin):
    """Loads cache, refreshes sources and builds the shared market payload."""

    def __init__(
        self: MarketTabController,
        services: object,
        config: MarketConfig | None = None,
        options: MarketOptions | None = None,
        now: Any | None = None,
    ) -> None:
        """Store the injected services and visualization options."""
        self.services = services
        self.config = config or getattr(services, "config", None) or MarketConfig()
        self.options = options or MarketOptions()
        self._now = now or (lambda: datetime.now(UTC))

    def _today(self: MarketTabController) -> str:
        return self._now().date().isoformat()

    def _raw(self: MarketTabController) -> object:
        return self.services.raw  # type: ignore[attr-defined]

    def _precompute(self: MarketTabController) -> object:
        return self.services.precompute  # type: ignore[attr-defined]


__all__ = [
    "B3_SOURCE",
    "DOL_SOURCE",
    "FOCUS_SOURCE",
    "GOLD_SOURCE",
    "SGS_SOURCE",
    "YAHOO_SOURCE",
    "MarketTabController",
    "derive_gold_series",
    "dol_ticker",
]
