"""Facade for fetching SELIC reference rates from the B3 website."""

from __future__ import annotations

import concurrent.futures
import http.client
import socket
import ssl
import time
import urllib.error
from collections.abc import Callable
from datetime import datetime, timezone

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.use_cases import evolution_dates
from b3_selic_pre.domain.constants import DEFAULT_MAX_PAGES, DEFAULT_PAGE_SIZE
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.b3_download import fetch_rates_download
from b3_selic_pre.infrastructure.b3_list import (
    build_payload,
    build_url,
    encode_payload,
    fetch_reference_rates,
    fetch_reference_rates_page,
    normalize_records,
)

__all__ = [
    "COMMUNICATION_EXCEPTIONS",
    "build_payload",
    "build_url",
    "encode_payload",
    "fetch_historical_rates",
    "fetch_rates_download",
    "fetch_rates_for_date",
    "fetch_reference_rates",
    "fetch_reference_rates_page",
    "normalize_records",
]

COMMUNICATION_EXCEPTIONS = (
    urllib.error.URLError,
    http.client.HTTPException,
    TimeoutError,
    ConnectionError,
    ssl.SSLError,
    socket.gaierror,
)

_PER_DATE_FAILURES = (CommunicationError, *COMMUNICATION_EXCEPTIONS)


def fetch_rates_for_date(
    date_str: str,
    today: str | None = None,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    opener: Callable[[str, int], object] | None = None,
    timeout: int = 30,
    sleep: Callable[[float], object] = time.sleep,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> tuple[list[RateRecord], str]:
    """Fetch rates using GetList for today and GetDownloadFile for past dates."""
    if today is None:
        today = datetime.now(timezone.utc).date().isoformat()
    if date_str == today:
        records = fetch_reference_rates(
            date_str,
            opener=opener,
            timeout=timeout,
            page_size=page_size,
            max_pages=max_pages,
            progress_callback=progress_callback,
            sleep=sleep,
        )
        return records, "GetList"
    try:
        records = fetch_rates_download(
            date_str, opener=opener, timeout=timeout, sleep=sleep
        )
    except CommunicationError:
        records = []
    if records:
        return records, "GetDownloadFile"
    records = fetch_reference_rates(
        date_str,
        opener=opener,
        timeout=timeout,
        page_size=page_size,
        max_pages=max_pages,
        progress_callback=progress_callback,
        sleep=sleep,
    )
    return records, "GetList"


def fetch_historical_rates(
    base_date: str,
    progress_callback: Callable[[int, int], None] | None = None,
    *,
    today: str | None = None,
    sleep: Callable[[float], object] = time.sleep,
    **kwargs: object,
) -> dict[str, list[RateRecord]]:
    """Fetch historical reference rates for the configured evolution days."""
    if today is None:
        today = datetime.now(timezone.utc).date().isoformat()
    dates = evolution_dates(base_date)

    def fetch_one(date_str: str) -> tuple[str, list[RateRecord]]:
        try:
            records, _ = fetch_rates_for_date(
                date_str, today=today, sleep=sleep, **kwargs
            )
        except _PER_DATE_FAILURES:
            records = []
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
