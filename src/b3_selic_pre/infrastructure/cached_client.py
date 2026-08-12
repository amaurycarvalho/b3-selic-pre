"""Cached facade over the B3 client with disk-backed rate caching."""

from __future__ import annotations

import concurrent.futures
from collections.abc import Callable
from datetime import datetime, timezone

from b3_selic_pre.application.use_cases import _days_ago
from b3_selic_pre.domain.constants import EVOLUTION_DAYS
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure import b3_client
from b3_selic_pre.infrastructure.disk_cache import DiskCache


class CachedB3Client:
    """B3 client that caches fetched rates on disk to avoid re-fetching."""

    def __init__(
        self: CachedB3Client,
        cache_dir: str | None = None,
        ttl_minutes: int = 30,
        max_age_days: int = 365,
    ) -> None:
        """Initialize the client with the given cache settings."""
        self._cache = DiskCache(cache_dir)
        self._ttl_minutes = ttl_minutes
        self._max_age_days = max_age_days

    def fetch_reference_rates(
        self: CachedB3Client,
        date_str: str,
        force: bool = False,
        source_callback: Callable[[str], None] | None = None,
        **kwargs: object,
    ) -> list[RateRecord]:
        """Return reference rates for ``date_str``, using the cache unless ``force``."""
        if not force:
            cached = self._cache.get(date_str, ttl_minutes=None)
            if cached is not None:
                if source_callback:
                    source_callback(f"Cache ({date_str})")
                return cached
        records = b3_client.fetch_reference_rates(date_str, **kwargs)
        today = datetime.now(timezone.utc).date().isoformat()
        ttl = self._ttl_minutes if date_str == today else None
        self._cache.put(date_str, records, ttl_minutes=ttl)
        self._cache.housekeeping(max_age_days=self._max_age_days)
        if source_callback:
            source_callback("API B3")
        return records

    def fetch_rates_download(
        self: CachedB3Client,
        date_str: str,
        force: bool = False,
        source_callback: Callable[[str], None] | None = None,
    ) -> list[RateRecord]:
        """Return download rates for ``date_str``, using the cache unless ``force``."""
        if not force:
            cached = self._cache.get(date_str, ttl_minutes=None)
            if cached is not None:
                if source_callback:
                    source_callback(f"Cache ({date_str})")
                return cached
        records = b3_client.fetch_rates_download(date_str)
        self._cache.put(date_str, records, ttl_minutes=None)
        self._cache.housekeeping(max_age_days=self._max_age_days)
        if source_callback:
            source_callback("Arquivo oficial B3")
        return records

    def fetch_historical_rates(
        self: CachedB3Client,
        base_date: str,
        force: bool = False,
        source_callback: Callable[[str], None] | None = None,
        **kwargs: object,
    ) -> dict[str, list[RateRecord]]:
        """Return historical rates for the evolution window ending at ``base_date``."""
        today = datetime.now(timezone.utc).date().isoformat()
        dates = [_days_ago(base_date, d) for d in EVOLUTION_DAYS]
        results: dict[str, list[RateRecord]] = {}
        cached_count = 0
        progress_callback: Callable[[int, int], None] | None = kwargs.get(
            "progress_callback"
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._fetch_one, d, force, today): d for d in dates
            }
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                date_str, records, from_cache = future.result()
                results[date_str] = records
                if from_cache:
                    cached_count += 1
                if progress_callback:
                    progress_callback(i + 1, len(dates))

        self._cache.housekeeping(max_age_days=self._max_age_days)
        self._notify_source(source_callback, cached_count, len(dates))
        return results

    def _fetch_one(
        self: CachedB3Client,
        date_str: str,
        force: bool,
        today: str,
    ) -> tuple[str, list[RateRecord], bool]:
        """Fetch a single date from cache when possible, otherwise from the API."""
        if not force:
            ttl = self._ttl_minutes if date_str == today else None
            cached = self._cache.get(date_str, ttl_minutes=ttl)
            if cached is not None:
                return date_str, cached, True
        records = self._fetch_from_api(date_str, today)
        ttl = self._ttl_minutes if date_str == today else None
        self._cache.put(date_str, records, ttl_minutes=ttl)
        return date_str, records, False

    @staticmethod
    def _fetch_from_api(date_str: str, today: str) -> list[RateRecord]:
        """Fetch a date's rates from B3, falling back to reference rates."""
        if date_str == today:
            return b3_client.fetch_reference_rates(date_str, page_size=100)
        records = b3_client.fetch_rates_download(date_str)
        if not records:
            records = b3_client.fetch_reference_rates(date_str, page_size=100)
        return records

    @staticmethod
    def _notify_source(
        source_callback: Callable[[str], None] | None,
        cached_count: int,
        total: int,
    ) -> None:
        """Report the data provenance summary through ``source_callback``."""
        if not source_callback:
            return
        if cached_count == total:
            source_callback(f"Cache ({total} datas)")
        elif cached_count > 0:
            source_callback(f"Cache ({cached_count}/{total} datas) + B3")
        else:
            source_callback("Histórico B3")
