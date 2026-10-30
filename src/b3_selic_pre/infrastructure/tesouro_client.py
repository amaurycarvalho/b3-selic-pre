"""Cliente CKAN e download dos CSVs do Tesouro Direto."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.domain.constants import DEFAULT_B3_TIMEOUT_SECONDS
from b3_selic_pre.infrastructure.b3_retry import (
    TRANSIENT_ERRORS,
    retry_transient,
)
from b3_selic_pre.infrastructure.tesouro_discovery import (
    TesouroDiscoveryMixin,
)
from b3_selic_pre.infrastructure.tesouro_types import (
    TesouroDownload,
    TesouroResource,
)

__all__ = ["TesouroDownload", "TesouroResource", "TesouroSourceClient"]

CHUNK_SIZE = 64 * 1024
_CONTENT_RANGE = re.compile(r"bytes\s+(\d+)-(\d+)/(\d+)")


class _TransientTesouroError(Exception):
    """Falha transitória que deve ser repetida."""


def _header(headers: object, name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter(name)
    if value is None and name.lower() != name:
        value = getter(name.lower())
    return str(value) if value is not None else None


class TesouroSourceClient(TesouroDiscoveryMixin):
    """Talks to the CKAN API and downloads resource CSVs."""

    def __init__(
        self: TesouroSourceClient,
        opener: Callable[[object, int], object] | None = None,
        timeout: int = DEFAULT_B3_TIMEOUT_SECONDS,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        """Initialize the CKAN/CSV source client."""
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout
        self._sleep = sleep

    def _fetch_json(
        self: TesouroSourceClient, url: str
    ) -> dict[str, object]:
        def operation() -> dict[str, object]:
            status, _headers, body = self._request(
                urllib.request.Request(url)
            )
            if status != 200:
                raise CommunicationError(
                    f"CKAN respondeu HTTP {status} para o dataset do Tesouro."
                )
            try:
                payload = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise TesouroDataError("Resposta CKAN inválida.") from exc
            if not isinstance(payload, dict):
                raise TesouroDataError("Resposta CKAN não é um objeto JSON.")
            if payload.get("success") is not True:
                raise TesouroDataError("CKAN retornou success diferente de true.")
            return payload

        return retry_transient(
            operation,
            source="CKAN do Tesouro",
            retry_on=(_TransientTesouroError, *TRANSIENT_ERRORS),
            sleep=self._sleep,
        )

    def download(
        self: TesouroSourceClient,
        resource: TesouroResource,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> TesouroDownload:
        """Download the CSV using conditional headers and transient retries."""
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        def operation() -> TesouroDownload:
            request = urllib.request.Request(
                resource.resource_url, headers=headers
            )
            status, response_headers, body = self._request(request)
            if status == 304:
                return TesouroDownload(
                    304,
                    None,
                    _header(response_headers, "ETag"),
                    _header(response_headers, "Last-Modified"),
                )
            if status != 200:
                raise CommunicationError(
                    f"Download do Tesouro respondeu HTTP {status}."
                )
            self._validate_body(response_headers, body)
            return TesouroDownload(
                200,
                body,
                _header(response_headers, "ETag"),
                _header(response_headers, "Last-Modified"),
            )

        return retry_transient(
            operation,
            source="Tesouro Transparente",
            retry_on=(_TransientTesouroError, *TRANSIENT_ERRORS),
            sleep=self._sleep,
        )

    def _request(
        self: TesouroSourceClient, request: urllib.request.Request
    ) -> tuple[int, object, bytes]:
        try:
            # semgrep note: a URL vem da API CKAN do Tesouro ou de constantes
            # fixas; não há entrada de usuário para host ou esquema.
            with self._opener(request, timeout=self._timeout) as response:  # nosemgrep
                status = int(getattr(response, "status", 200))
                headers = getattr(response, "headers", {})
                return status, headers, self._read_body(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return 304, exc.headers, b""
            if exc.code == 429 or 500 <= exc.code < 600:
                raise _TransientTesouroError(
                    f"HTTP transitório {exc.code} no Tesouro."
                ) from exc
            raise CommunicationError(
                f"HTTP {exc.code} ao acessar o Tesouro."
            ) from exc
        except TRANSIENT_ERRORS as exc:
            raise _TransientTesouroError(str(exc)) from exc

    @staticmethod
    def _read_body(response: object) -> bytes:
        chunks: list[bytes] = []
        read = response.read
        while True:
            chunk = read(CHUNK_SIZE)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    @staticmethod
    def _validate_body(headers: object, body: bytes) -> None:
        content_type = _header(headers, "Content-Type") or ""
        if not content_type.startswith("text/csv"):
            raise _TransientTesouroError(
                f"Tesouro respondeu Content-Type inesperado: {content_type}"
            )
        if not body:
            raise _TransientTesouroError("Tesouro respondeu corpo vazio.")
        content_range = _header(headers, "Content-Range")
        if content_range is None:
            return
        match = _CONTENT_RANGE.search(content_range)
        if match is None:
            return
        start, end, total = (int(value) for value in match.groups())
        if start != 0 or end - start + 1 != len(body) or total != len(body):
            raise _TransientTesouroError(
                "Tesouro respondeu corpo parcial."
            )
