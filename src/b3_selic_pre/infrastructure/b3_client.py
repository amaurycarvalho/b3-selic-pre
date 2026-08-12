"""Client for fetching SELIC reference rates from the B3 website."""

from __future__ import annotations

import base64
import concurrent.futures
import json
import math
import urllib.request
from collections.abc import Callable

from b3_selic_pre.application.use_cases import _days_ago, validate_reference_date
from b3_selic_pre.domain.constants import (
    B3_BASE_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_PAGES,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RATE_ID,
    EVOLUTION_DAYS,
)
from b3_selic_pre.domain.models import RateRecord


def build_payload(
    reference_date: str,
    language: str = DEFAULT_LANGUAGE,
    rate_id: str = DEFAULT_RATE_ID,
    page_number: int = DEFAULT_PAGE_NUMBER,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, str | int]:
    """Build the payload used to query B3 reference rates."""
    return {
        "language": language,
        "id": rate_id,
        "pageNumber": page_number,
        "pageSize": page_size,
        "date": validate_reference_date(reference_date),
    }


def encode_payload(payload: dict[str, str | int]) -> str:
    """Encode a payload dictionary as compact base64 JSON."""
    return base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8")


def build_url(payload: dict[str, str | int]) -> str:
    """Build the B3 URL for the given encoded payload."""
    return f"{B3_BASE_URL}referenceRatesProxy/Search/GetList/{encode_payload(payload)}"


def normalize_records(data: dict[str, object]) -> list[RateRecord]:
    """Normalize raw B3 results into RateRecord instances."""
    results = data.get("results")
    if results is None:
        raise ValueError("Resposta da B3 não contém o campo 'results'.")
    if not isinstance(results, list):
        raise TypeError("Campo 'results' da B3 não é uma lista.")
    records = []
    for item in results:
        try:
            records.append(
                RateRecord(
                    day252=int(item["day252"]),
                    day360=int(item["day360"]),
                    rate=str(item["rate"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Registro de taxa da B3 tem formato inesperado.") from exc
    return records


def fetch_reference_rates_page(
    reference_date: str,
    page_number: int = DEFAULT_PAGE_NUMBER,
    page_size: int = DEFAULT_PAGE_SIZE,
    opener: Callable[[str, int], object] | None = None,
    timeout: int = 30,
) -> tuple[list[RateRecord], int | None]:
    """Fetch a single page of reference rates from B3."""
    if opener is None:
        opener = urllib.request.urlopen
    payload = build_payload(
        reference_date,
        page_number=page_number,
        page_size=page_size,
    )
    url = build_url(payload)
    with opener(url, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    records = normalize_records(data)
    total_count = data.get("totalCount")
    return records, total_count


def fetch_reference_rates(
    reference_date: str,
    opener: Callable[[str, int], object] | None = None,
    timeout: int = 30,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> list[RateRecord]:
    """Fetch reference rates across pages with progress reporting."""
    if opener is None:
        opener = urllib.request.urlopen
    if page_size <= 0:
        raise ValueError("Tamanho da página deve ser maior que zero.")
    if max_pages <= 0:
        raise ValueError("Quantidade máxima de páginas deve ser maior que zero.")
    records = []
    total_pages = None
    for page_number in range(DEFAULT_PAGE_NUMBER, max_pages + 1):
        page_records, total_count = fetch_reference_rates_page(
            reference_date,
            page_number=page_number,
            page_size=page_size,
            opener=opener,
            timeout=timeout,
        )
        records.extend(page_records)
        if total_pages is None and total_count is not None and page_size > 0:
            total_pages = math.ceil(total_count / page_size)
        if progress_callback:
            progress_callback(page_number, total_pages)
        if len(page_records) < page_size:
            return records
    raise ValueError("Paginação da B3 excedeu o limite máximo de páginas.")


def fetch_rates_download(date_str: str) -> list[RateRecord]:
    """Download historical reference rates for a given date."""
    payload = {"language": "pt-br", "date": date_str, "id": "SLP"}
    compact = json.dumps(payload, separators=(",", ":"))
    encoded = base64.b64encode(compact.encode("utf-8")).decode("utf-8")
    url = f"{B3_BASE_URL}referenceRatesProxy/Search/GetDownloadFile/{encoded}"
    # semgrep note: em urllib a URL é construída a partir de constantes fixas,
    # não há controle de usuário sobre o esquema da URL nem sobre o host.
    with urllib.request.urlopen(url, timeout=30) as resp:  # nosemgrep
        raw = resp.read()
    b64_text = raw.decode("latin-1").strip()
    if not b64_text:
        return []
    decoded = base64.b64decode(b64_text)
    text = decoded.decode("latin-1")
    lines = text.strip().split("\n")
    records = []
    for line in lines[1:]:
        parts = line.split(";")
        if len(parts) >= 4:
            records.append(RateRecord(
                day252=int(parts[1]),
                day360=int(parts[2]),
                rate=parts[3],
            ))
    return records


def fetch_historical_rates(
    base_date: str, progress_callback: Callable[[int, int], None] | None = None
) -> dict[str, list[RateRecord]]:
    """Fetch historical reference rates for the configured evolution days."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    dates = [_days_ago(base_date, d) for d in EVOLUTION_DAYS]

    def fetch_one(date_str: str) -> tuple[str, list[RateRecord]]:
        if date_str == today:
            records = fetch_reference_rates(date_str, page_size=100)
        else:
            records = fetch_rates_download(date_str)
            if not records:
                records = fetch_reference_rates(date_str, page_size=100)
        return date_str, records

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_one, d): d for d in dates}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            date_str, records = future.result()
            results[date_str] = records
            if progress_callback:
                progress_callback(i + 1, len(dates))
    return results
