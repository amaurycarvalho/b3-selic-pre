"""Cliente B3 para câmbio oficial (HistoricalExchange) e futuros DOL."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, date, datetime

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.domain.market import (
    ATIVO_USD,
    METODO_OFICIAL,
    UNIDADE_USD,
    MarketQuote,
)
from b3_selic_pre.infrastructure.b3_retry import (
    TRANSIENT_ERRORS,
    retry_transient,
)
from b3_selic_pre.infrastructure.market.types import (
    FONTE_B3,
    MarketSourceError,
)

HISTORICAL_EXCHANGE_URL = (
    "https://arquivos.b3.com.br/bdi/table/HistoricalExchange"
)
DOL_URL = "https://arquivos.b3.com.br/bdi/table/HistoricalPrice"
DOL_CONTRACT_SIZE = 1000.0
DEFAULT_TIMEOUT_SECONDS = 30

_DATE_KEYS = ("data", "date", "Data", "Date", "refdate", "referencia")
_VALUE_KEYS = ("valor", "value", "cotacao", "close", "vlr", "preco")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def normalize_dol(value: float) -> float:
    """Normalize a DOL quote from BRL per USD 1,000 to BRL/USD."""
    return value / DOL_CONTRACT_SIZE


def _normalize_date(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().split("T", 1)[0].split(" ", 1)[0]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        pass
    try:
        return datetime.strptime(text, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _rows(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("value", "items", "data", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _row_quote(
    row: dict[str, object], extraido_em: str
) -> MarketQuote | None:
    raw_date = next(
        (row[key] for key in _DATE_KEYS if key in row), None
    )
    raw_value = next(
        (row[key] for key in _VALUE_KEYS if key in row), None
    )
    day = _normalize_date(raw_date)
    value = _float(raw_value)
    if day is None or value is None:
        return None
    return MarketQuote(
        data=day,
        ativo=ATIVO_USD,
        valor=value,
        unidade=UNIDADE_USD,
        origem="B3 BDI",
        metodo=METODO_OFICIAL,
        extraido_em=extraido_em,
    )


def _parse(payload: bytes | str, extraido_em: str) -> list[MarketQuote]:
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return []
    quotes = [
        quote
        for quote in (_row_quote(row, extraido_em) for row in _rows(data))
        if quote is not None
    ]
    return sorted(quotes, key=lambda quote: quote.data)


def parse_historical_exchange(
    payload: bytes | str, extraido_em: str = ""
) -> list[MarketQuote]:
    """Parse a B3 HistoricalExchange fixture."""
    return _parse(payload, extraido_em)


def parse_dol(
    payload: bytes | str,
    vencimento: str | None = None,
    extraido_em: str = "",
) -> list[MarketQuote]:
    """Parse DOL fixtures, normalizing to BRL/USD."""
    quotes: list[MarketQuote] = []
    for quote in _parse(payload, extraido_em):
        if vencimento is not None and quote.data > vencimento:
            continue
        quotes.append(
            MarketQuote(
                data=quote.data,
                ativo=quote.ativo,
                valor=normalize_dol(quote.valor),
                unidade=quote.unidade,
                origem="B3 DOL",
                metodo=METODO_OFICIAL,
                extraido_em=quote.extraido_em,
            )
        )
    return quotes


class B3MarketClient:
    """Consulta câmbio oficial e futuros DOL no BDI da B3."""

    def __init__(
        self: B3MarketClient,
        opener: Callable[..., object] | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        """Initialize the B3 BDI client."""
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout
        self._sleep = sleep

    def _get(self: B3MarketClient, url: str) -> bytes:
        request = urllib.request.Request(url)

        def operation() -> bytes:
            # semgrep note: URL fixa da B3.
            with self._opener(request, timeout=self._timeout) as response:  # type: ignore[attr-defined]
                return response.read()  # type: ignore[attr-defined]

        try:
            return retry_transient(
                operation,
                source="B3 BDI",
                retry_on=(*TRANSIENT_ERRORS, OSError),
                sleep=self._sleep,
            )
        except CommunicationError:
            raise
        except urllib.error.HTTPError as exc:
            raise MarketSourceError(
                f"{FONTE_B3} respondeu HTTP {exc.code}."
            ) from exc

    def fetch_historical_exchange(
        self: B3MarketClient, inicio: str, fim: str
    ) -> list[MarketQuote]:
        """Fetch official USD/BRL quotes from HistoricalExchange."""
        query = urllib.parse.urlencode(
            {"dateStart": inicio, "dateEnd": fim}
        )
        return parse_historical_exchange(
            self._get(f"{HISTORICAL_EXCHANGE_URL}?{query}"),
            extraido_em=_now_iso(),
        )

    def fetch_dol(
        self: B3MarketClient, ticker: str, inicio: str, fim: str
    ) -> list[MarketQuote]:
        """Fetch DOL futures quotes normalized to BRL/USD."""
        query = urllib.parse.urlencode(
            {"ticker": ticker, "dateStart": inicio, "dateEnd": fim}
        )
        return parse_dol(
            self._get(f"{DOL_URL}?{query}"), extraido_em=_now_iso()
        )


__all__ = [
    "DOL_CONTRACT_SIZE",
    "B3MarketClient",
    "normalize_dol",
    "parse_dol",
    "parse_historical_exchange",
]
