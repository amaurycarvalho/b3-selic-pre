"""Clientes BCB SGS 1 (dólar) e BCB Focus (expectativas de câmbio)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.market.forecast import FocusExpectation
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
    FONTE_BCB_FOCUS,
    FONTE_BCB_SGS,
    MarketSourceError,
)

SGS_URL_TEMPLATE = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
)
FOCUS_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoAnuais"
)
DEFAULT_TIMEOUT_SECONDS = 30


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _br_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return parsed.strftime("%d/%m/%Y")


def _parse_br(value: str) -> str:
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


def _read(opener: Callable[..., object], url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url)
    with opener(request, timeout=timeout) as response:  # type: ignore[attr-defined]
        return response.read()  # type: ignore[attr-defined]


class _JsonClient:
    def __init__(
        self: _JsonClient,
        opener: Callable[..., object] | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout
        self._sleep = sleep

    def _get(self: _JsonClient, url: str, source: str) -> bytes:
        def operation() -> bytes:
            return _read(self._opener, url, self._timeout)

        try:
            return retry_transient(
                operation,
                source=source,
                retry_on=(*TRANSIENT_ERRORS, OSError),
                sleep=self._sleep,
            )
        except CommunicationError:
            raise
        except urllib.error.HTTPError as exc:
            raise MarketSourceError(
                f"{source} respondeu HTTP {exc.code}."
            ) from exc


class BcbSgsClient(_JsonClient):
    """Consulta uma série oficial do SGS do BCB."""

    def __init__(
        self: BcbSgsClient,
        opener: Callable[..., object] | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        sleep: Callable[[float], object] = time.sleep,
        codigo: int = 1,
    ) -> None:
        """Initialize the SGS client for a series code (default: USD/BRL)."""
        super().__init__(opener=opener, timeout=timeout, sleep=sleep)
        self.codigo = codigo

    def fetch_payload(self: BcbSgsClient, inicio: str, fim: str) -> bytes:
        """Fetch the raw SGS payload between two ISO dates."""
        query = urllib.parse.urlencode(
            {
                "formato": "json",
                "dataInicial": _br_date(inicio),
                "dataFinal": _br_date(fim),
            }
        )
        url = SGS_URL_TEMPLATE.format(codigo=self.codigo)
        return self._get(f"{url}?{query}", f"BCB SGS {self.codigo}")

    def fetch_series(
        self: BcbSgsClient, inicio: str, fim: str
    ) -> list[MarketQuote]:
        """Fetch SGS quotes between two ISO dates."""
        return parse_sgs(
            self.fetch_payload(inicio, fim), extraido_em=_now_iso()
        )


def _value(row: dict[str, object]) -> float | None:
    raw = row.get("valor")
    if raw is None:
        return None
    try:
        return float(str(raw).replace(",", "."))
    except ValueError:
        return None


def parse_sgs(
    payload: bytes | str, extraido_em: str = ""
) -> list[MarketQuote]:
    """Parse an SGS JSON fixture into USD/BRL quotes."""
    try:
        rows = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return []
    if not isinstance(rows, list):
        return []
    quotes: list[MarketQuote] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        data = row.get("data")
        value = _value(row)
        if not isinstance(data, str) or value is None:
            continue
        try:
            day = _parse_br(data)
        except ValueError:
            continue
        quotes.append(
            MarketQuote(
                data=day,
                ativo=ATIVO_USD,
                valor=value,
                unidade=UNIDADE_USD,
                origem="BCB SGS 1",
                metodo=METODO_OFICIAL,
                extraido_em=extraido_em,
            )
        )
    return sorted(quotes, key=lambda quote: quote.data)


class BcbFocusClient(_JsonClient):
    """Consulta as medianas anuais de câmbio do Focus."""

    def fetch_expectations(
        self: BcbFocusClient, indicator: str = "Câmbio"
    ) -> list[FocusExpectation]:
        """Fetch the annual Focus medians for ``indicator``."""
        encoded = urllib.parse.quote(indicator)
        query = (
            f"$filter=Indicador%20eq%20'{encoded}'"
            "&$orderby=Data%20desc&$top=100&$format=json"
        )
        body = self._get(f"{FOCUS_URL}?{query}", "BCB Focus")
        return parse_focus(body)


_YEAR_KEYS = ("Ano", "ano", "DataReferencia", "dataReferencia")
_STAMP_KEYS = ("Data", "data")


def _first_value(row: dict[str, object], keys: tuple[str, ...]) -> object:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _year(row: dict[str, object]) -> int | None:
    try:
        return int(str(_first_value(row, _YEAR_KEYS)))
    except (TypeError, ValueError):
        return None


def _stamp(row: dict[str, object]) -> str:
    return str(_first_value(row, _STAMP_KEYS) or "")


def _latest_by_year(
    rows: Sequence[dict[str, object]],
) -> dict[int, dict[str, object]]:
    latest: dict[int, dict[str, object]] = {}
    for row in rows:
        year = _year(row)
        if year is None:
            continue
        current = latest.get(year)
        if current is None or _stamp(row) >= _stamp(current):
            latest[year] = row
    return latest


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def parse_focus(payload: bytes | str) -> list[FocusExpectation]:
    """Parse a Focus JSON fixture into annual expectations."""
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return []
    rows = data.get("value") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    expectations: list[FocusExpectation] = []
    for year, row in sorted(_latest_by_year(rows).items()):
        median = _float(row.get("Mediana") or row.get("mediana"))
        if median is None:
            continue
        expectations.append(
            FocusExpectation(
                ano=year,
                mediana=median,
                minimo=_float(row.get("Minimo") or row.get("minimo")),
                maximo=_float(row.get("Maximo") or row.get("maximo")),
            )
        )
    return expectations


__all__ = [
    "FONTE_BCB_FOCUS",
    "FONTE_BCB_SGS",
    "BcbFocusClient",
    "BcbSgsClient",
    "parse_focus",
    "parse_sgs",
]
