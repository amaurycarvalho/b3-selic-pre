"""Cliente HTTP da página e do anexo da publicação BTD."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.domain.constants import (
    DEFAULT_B3_TIMEOUT_SECONDS,
    TESOURO_BTD_PUBLICATIONS_URL,
)
from b3_selic_pre.infrastructure.b3_retry import TRANSIENT_ERRORS
from b3_selic_pre.infrastructure.tesouro_btd_page import parse_btd_page
from b3_selic_pre.infrastructure.tesouro_btd_types import (
    BtdEdition,
    BtdResponse,
)

CHUNK_SIZE = 64 * 1024
_SPREADSHEET_TYPES = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/zip",
    "application/octet-stream",
    "binary/octet-stream",
)
_ZIP_SIGNATURE = b"PK\x03\x04"


def _header(headers: object, name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter(name)
    if value is None and name.lower() != name:
        value = getter(name.lower())
    return str(value) if value is not None else None


def _read_body(response: object) -> bytes:
    chunks: list[bytes] = []
    read = response.read
    while True:
        chunk = read(CHUNK_SIZE)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _validate_spreadsheet(headers: object, body: bytes) -> None:
    content_type = _header(headers, "Content-Type") or ""
    base = content_type.split(";", 1)[0].strip().casefold()
    if base and base not in _SPREADSHEET_TYPES:
        raise TesouroDataError(
            f"Anexo do BTD com Content-Type inesperado: {content_type}"
        )
    if not body.startswith(_ZIP_SIGNATURE):
        raise TesouroDataError("Anexo do BTD não é uma planilha XLSX válida.")


class BtdSourceClient:
    """Descobre a edição BTD e baixa o anexo XLSX com validação."""

    def __init__(
        self: BtdSourceClient,
        opener: Callable[[object, int], object] | None = None,
        timeout: int = DEFAULT_B3_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the injectable HTTP client."""
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout

    def discover(self: BtdSourceClient) -> BtdEdition:
        """Read the publications page and return its latest XLSX edition."""
        response = self._request(TESOURO_BTD_PUBLICATIONS_URL)
        if response.status != 200:
            raise CommunicationError(
                f"Página do BTD respondeu HTTP {response.status}."
            )
        return parse_btd_page(response.body, response.url)

    def download(self: BtdSourceClient, edition: BtdEdition) -> bytes:
        """Download and validate the XLSX attachment of an edition."""
        response = self._request(edition.attachment_url)
        if response.status != 200:
            raise CommunicationError(
                f"Anexo do BTD respondeu HTTP {response.status}."
            )
        _validate_spreadsheet(response.headers, response.body)
        return response.body

    def _request(self: BtdSourceClient, url: str) -> BtdResponse:
        request = urllib.request.Request(url)
        try:
            # semgrep note: URL fixa da publicação ou link XLSX restrito a ela.
            with self._opener(request, timeout=self._timeout) as response:  # nosemgrep
                status = int(getattr(response, "status", 200))
                headers = getattr(response, "headers", {})
                final_url = getattr(response, "geturl", lambda: url)()
                return BtdResponse(
                    status,
                    str(final_url or url),
                    headers,
                    _read_body(response),
                )
        except urllib.error.HTTPError as exc:
            raise CommunicationError(
                f"HTTP {exc.code} ao acessar o BTD."
            ) from exc
        except TRANSIENT_ERRORS as exc:
            raise CommunicationError(
                f"Falha ao acessar o BTD: {exc}"
            ) from exc


__all__ = ["BtdSourceClient"]
