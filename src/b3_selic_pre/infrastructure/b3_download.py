"""Client and CSV parser for the B3 GetDownloadFile endpoint."""

from __future__ import annotations

import base64
import json
import time
import urllib.request
from collections.abc import Callable

from b3_selic_pre.domain.constants import B3_BASE_URL
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.b3_retry import retry_empty

DEFAULT_TIMEOUT = 30


def parse_csv(text: str) -> list[RateRecord]:
    """Parse the B3 CSV payload into rate records."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    records = []
    for line in lines[1:]:
        parts = [part.strip() for part in line.split(";")]
        if len(parts) < 4:
            raise ValueError("Linha do arquivo CSV da B3 tem formato inesperado.")
        try:
            records.append(
                RateRecord(
                    day252=int(parts[1]),
                    day360=int(parts[2]),
                    rate=parts[3],
                )
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Linha do arquivo CSV da B3 tem formato inesperado."
            ) from exc
    return records


def parse_download_payload(raw: bytes) -> list[RateRecord]:
    """Decode and parse a GetDownloadFile response body."""
    b64_text = raw.decode("latin-1").strip()
    if not b64_text:
        return []
    try:
        decoded = base64.b64decode(b64_text, validate=True)
        text = decoded.decode("latin-1")
    except ValueError as exc:
        raise ValueError("Arquivo CSV da B3 tem formato inesperado.") from exc
    return parse_csv(text)


def fetch_rates_download(
    date_str: str,
    opener: Callable[[str, int], object] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    sleep: Callable[[float], object] = time.sleep,
) -> list[RateRecord]:
    """Download historical reference rates for a given date."""
    if opener is None:
        opener = urllib.request.urlopen
    payload = {"language": "pt-br", "date": date_str, "id": "SLP"}
    compact = json.dumps(payload, separators=(",", ":"))
    encoded = base64.b64encode(compact.encode("utf-8")).decode("utf-8")
    url = f"{B3_BASE_URL}referenceRatesProxy/Search/GetDownloadFile/{encoded}"

    def fetch_once() -> list[RateRecord]:
        # semgrep note: em urllib a URL é construída a partir de constantes fixas,
        # não há controle de usuário sobre o esquema da URL nem sobre o host.
        with opener(url, timeout=timeout) as resp:  # nosemgrep
            raw = resp.read()
        return parse_download_payload(raw)

    return retry_empty(
        fetch_once,
        date=date_str,
        source="GetDownloadFile",
        result_is_empty=lambda records: not records,
        sleep=sleep,
    )
