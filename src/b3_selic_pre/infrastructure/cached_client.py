import concurrent.futures
from datetime import date as _today_date

from b3_selic_pre.domain.constants import EVOLUTION_DAYS
from b3_selic_pre.application.use_cases import _days_ago
from b3_selic_pre.infrastructure import b3_client
from b3_selic_pre.infrastructure.disk_cache import DiskCache


class CachedB3Client:
    def __init__(self, cache_dir=None, ttl_minutes=30, max_age_days=365):
        self._cache = DiskCache(cache_dir)
        self._ttl_minutes = ttl_minutes
        self._max_age_days = max_age_days

    def fetch_reference_rates(self, date_str, force=False, **kwargs):
        if not force:
            cached = self._cache.get(date_str, ttl_minutes=None)
            if cached is not None:
                return cached
        records = b3_client.fetch_reference_rates(date_str, **kwargs)
        today = _today_date.today().isoformat()
        ttl = self._ttl_minutes if date_str == today else None
        self._cache.put(date_str, records, ttl_minutes=ttl)
        self._cache.housekeeping(max_age_days=self._max_age_days)
        return records

    def fetch_rates_download(self, date_str, force=False):
        if not force:
            cached = self._cache.get(date_str, ttl_minutes=None)
            if cached is not None:
                return cached
        records = b3_client.fetch_rates_download(date_str)
        self._cache.put(date_str, records, ttl_minutes=None)
        self._cache.housekeeping(max_age_days=self._max_age_days)
        return records

    def fetch_historical_rates(self, base_date, force=False, **kwargs):
        today = _today_date.today().isoformat()
        dates = [_days_ago(base_date, d) for d in EVOLUTION_DAYS]

        def fetch_one(date_str):
            if not force:
                ttl = self._ttl_minutes if date_str == today else None
                cached = self._cache.get(date_str, ttl_minutes=ttl)
                if cached is not None:
                    return date_str, cached
            if date_str == today:
                records = b3_client.fetch_reference_rates(date_str, page_size=100)
            else:
                records = b3_client.fetch_rates_download(date_str)
                if not records:
                    records = b3_client.fetch_reference_rates(date_str, page_size=100)
            ttl = self._ttl_minutes if date_str == today else None
            self._cache.put(date_str, records, ttl_minutes=ttl)
            return date_str, records

        results = {}
        progress_callback = kwargs.get("progress_callback")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_one, d): d for d in dates}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                date_str, records = future.result()
                results[date_str] = records
                if progress_callback:
                    progress_callback(i + 1, len(dates))

        self._cache.housekeeping(max_age_days=self._max_age_days)
        return results
