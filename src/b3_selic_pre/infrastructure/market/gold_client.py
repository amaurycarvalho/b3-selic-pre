"""Cliente XAU/USD do contrato futuro GC=F do Yahoo Finance."""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime

from b3_selic_pre.domain.market import METODO_OFICIAL, MarketQuote
from b3_selic_pre.infrastructure.b3_retry import (
    TRANSIENT_ERRORS,
    retry_transient,
)
from b3_selic_pre.infrastructure.market.types import (
    ATIVO_XAU_USD,
    FONTE_YAHOO,
    UNIDADE_XAU_USD,
)

YAHOO_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
    "?range=2y&interval=1d"
)
USER_AGENT = "Mozilla/5.0 (compatible; b3-selic-pre market adapter)"
DEFAULT_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _chart_result(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    chart = payload.get("chart")
    if not isinstance(chart, dict):
        return None
    results = chart.get("result")
    if not isinstance(results, list) or not results:
        return None
    return results[0] if isinstance(results[0], dict) else None


def _price_series(
    result: dict[str, object],
) -> tuple[list[object], list[object]] | None:
    timestamps = result.get("timestamp")
    indicators = result.get("indicators")
    if not isinstance(timestamps, list) or not isinstance(indicators, dict):
        return None
    quote_rows = indicators.get("quote")
    if not isinstance(quote_rows, list) or not quote_rows:
        return None
    row = quote_rows[0]
    closes = row.get("close") if isinstance(row, dict) else None
    if not isinstance(closes, list):
        return None
    return timestamps, closes


def _quote(stamp: object, close: object, extracted: str) -> MarketQuote | None:
    if close is None:
        return None
    try:
        day = datetime.fromtimestamp(int(stamp), UTC).date().isoformat()
        value = float(close)
    except (TypeError, ValueError, OSError):
        return None
    return MarketQuote(
        data=day,
        ativo=ATIVO_XAU_USD,
        valor=value,
        unidade=UNIDADE_XAU_USD,
        origem="Yahoo GC=F",
        metodo=METODO_OFICIAL,
        extraido_em=extracted,
    )


def _extract(payload: object) -> list[MarketQuote]:
    result = _chart_result(payload)
    if result is None:
        return []
    series = _price_series(result)
    if series is None:
        return []
    timestamps, closes = series
    extracted = _now_iso()
    quotes = [
        quote
        for quote in (
            _quote(stamp, close, extracted)
            for stamp, close in zip(timestamps, closes)
        )
        if quote is not None
    ]
    quotes.sort(key=lambda quote: quote.data)
    return quotes


def parse_yahoo(payload: bytes | str) -> list[MarketQuote]:
    """Parse a Yahoo GC=F chart fixture."""
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return []
    return _extract(data)


class GoldUsdClient:
    """Consulta XAU/USD sem derrubar a aplicação em falha de rede."""

    def __init__(
        self: GoldUsdClient,
        opener: Callable[..., object] | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        """Initialize the Yahoo GC=F client."""
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout
        self._sleep = sleep

    def fetch_series(self: GoldUsdClient) -> list[MarketQuote]:
        """Fetch the XAU/USD daily series, returning ``[]`` on failure."""
        request = urllib.request.Request(
            YAHOO_URL, headers={"User-Agent": USER_AGENT}
        )

        def operation() -> bytes:
            # semgrep note: URL fixa do Yahoo Finance.
            with self._opener(request, timeout=self._timeout) as response:  # type: ignore[attr-defined]
                return response.read()  # type: ignore[attr-defined]

        try:
            body = retry_transient(
                operation,
                source="Yahoo GC=F",
                retry_on=(*TRANSIENT_ERRORS, OSError),
                sleep=self._sleep,
            )
        except Exception as exc:
            logger.warning("Falha ao consultar XAU/USD no Yahoo: %s", exc)
            return []
        return parse_yahoo(body)


__all__ = ["FONTE_YAHOO", "GoldUsdClient", "parse_yahoo"]
