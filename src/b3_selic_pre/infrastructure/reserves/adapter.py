"""Adaptador BCB SGS 13621 das reservas internacionais."""

from __future__ import annotations

import time
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime

from b3_selic_pre.application.reserves.series import parse_reserves_sgs
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.infrastructure.market.bcb_client import BcbSgsClient

CODIGO_RESERVAS = 13621


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class BcbReservesClient(BcbSgsClient):
    """Fetch the official daily reserves series from BCB SGS 13621."""

    def __init__(
        self: BcbReservesClient,
        opener: Callable[..., object] | None = None,
        timeout: int = 30,
        sleep: Callable[[float], object] = time.sleep,
        codigo: int = CODIGO_RESERVAS,
    ) -> None:
        """Initialize the reserves client with timeout and transient retry."""
        super().__init__(
            opener=opener or urllib.request.urlopen,
            timeout=timeout,
            sleep=sleep,
            codigo=codigo,
        )

    def fetch_series(
        self: BcbReservesClient, inicio: str, fim: str
    ) -> list[MarketQuote]:
        """Fetch reserves points in US$ millions between two ISO dates."""
        return parse_reserves_sgs(
            self.fetch_payload(inicio, fim), extraido_em=_now_iso()
        )


__all__ = ["CODIGO_RESERVAS", "BcbReservesClient"]
