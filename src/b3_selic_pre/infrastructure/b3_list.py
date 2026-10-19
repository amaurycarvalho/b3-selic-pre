"""Client and pagination for the B3 GetList endpoint."""

from __future__ import annotations

import base64
import json
import math
import time
import urllib.request
from collections.abc import Callable

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.use_cases import validate_reference_date
from b3_selic_pre.domain.constants import (
    B3_BASE_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_PAGES,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RATE_ID,
)
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.b3_retry import retry_empty


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


def _page_metadata(
    data: dict[str, object], page_size: int
) -> tuple[int | None, int | None]:
    """Extract total records and total pages from the B3 response."""
    page = data.get("page")
    total_records: int | None = None
    total_pages: int | None = None
    if isinstance(page, dict):
        raw_records = page.get("totalRecords")
        raw_pages = page.get("totalPages")
        if raw_records is not None:
            total_records = int(raw_records)
        if raw_pages is not None:
            total_pages = int(raw_pages)
    if total_records is None:
        raw_count = data.get("totalCount")
        if raw_count is not None:
            total_records = int(raw_count)
    if total_pages is None and total_records is not None and page_size > 0:
        total_pages = math.ceil(total_records / page_size)
    return total_records, total_pages


def fetch_reference_rates_page(
    reference_date: str,
    page_number: int = DEFAULT_PAGE_NUMBER,
    page_size: int = DEFAULT_PAGE_SIZE,
    opener: Callable[[str, int], object] | None = None,
    timeout: int = 30,
) -> tuple[list[RateRecord], int | None, int | None]:
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
    total_records, total_pages = _page_metadata(data, page_size)
    return records, total_records, total_pages


def _validate_page_args(page_size: int, max_pages: int) -> None:
    """Validate the pagination arguments."""
    if page_size <= 0:
        raise ValueError("Tamanho da página deve ser maior que zero.")
    if max_pages <= 0:
        raise ValueError("Quantidade máxima de páginas deve ser maior que zero.")


def _validate_total_pages(max_pages: int, total_pages: int | None) -> None:
    """Reject a response that exceeds the configured page limit."""
    if total_pages is not None and total_pages > max_pages:
        raise ValueError("Paginação da B3 excedeu o limite máximo de páginas.")


def _fetch_page(
    reference_date: str,
    page_number: int,
    page_size: int,
    opener: Callable[[str, int], object],
    timeout: int,
    sleep: Callable[[float], object],
) -> tuple[list[RateRecord], int | None, int | None]:
    """Fetch one page, retrying while it comes back empty."""
    return retry_empty(
        lambda: fetch_reference_rates_page(
            reference_date,
            page_number=page_number,
            page_size=page_size,
            opener=opener,
            timeout=timeout,
        ),
        date=reference_date,
        source="GetList",
        result_is_empty=lambda page: not page[0],
        sleep=sleep,
    )


def _is_last_page(
    page_number: int,
    total_pages: int | None,
    page_records: list[RateRecord],
    page_size: int,
) -> bool:
    """Return whether the current page is the last one to fetch."""
    if total_pages is not None:
        return page_number >= total_pages
    return len(page_records) < page_size


def _validate_collection(
    records: list[RateRecord],
    total_records: int | None,
    reference_date: str,
) -> list[RateRecord]:
    """Validate that the collected records match the expected total."""
    if total_records is not None and len(records) != total_records:
        raise CommunicationError(
            f"Resposta incompleta do GetList para {reference_date}: "
            f"esperados {total_records}, obtidos {len(records)}."
        )
    if not records:
        raise CommunicationError(
            f"GetList retornou resposta vazia para {reference_date}."
        )
    return records


def fetch_reference_rates(
    reference_date: str,
    opener: Callable[[str, int], object] | None = None,
    timeout: int = 30,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    progress_callback: Callable[[int, int | None], None] | None = None,
    sleep: Callable[[float], object] = time.sleep,
) -> list[RateRecord]:
    """Fetch reference rates across pages with progress reporting."""
    if opener is None:
        opener = urllib.request.urlopen
    _validate_page_args(page_size, max_pages)
    records: list[RateRecord] = []
    total_records: int | None = None
    total_pages: int | None = None
    for page_number in range(DEFAULT_PAGE_NUMBER, max_pages + 1):
        page_records, page_total_records, page_total_pages = _fetch_page(
            reference_date, page_number, page_size, opener, timeout, sleep
        )
        if page_number == DEFAULT_PAGE_NUMBER:
            total_records = page_total_records
            total_pages = page_total_pages
            _validate_total_pages(max_pages, total_pages)
        records.extend(page_records)
        if progress_callback:
            progress_callback(page_number, total_pages)
        if _is_last_page(page_number, total_pages, page_records, page_size):
            return _validate_collection(records, total_records, reference_date)
    raise ValueError("Paginação da B3 excedeu o limite máximo de páginas.")
