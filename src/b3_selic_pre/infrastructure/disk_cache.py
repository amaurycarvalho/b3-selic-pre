"""Disk-backed JSON cache for historical B3 rate records."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.cache_payload import (
    SCHEMA_VERSION,
    CacheEntry,
    is_valid_entry,
    load_payload,
    parse_records,
    read_entry,
    write_atomic,
)
from b3_selic_pre.infrastructure.xdg import cache_base


def _xdg_cache_dir() -> Path:
    return cache_base() / "b3-selic-pre" / "rates"


class DiskCache:
    """Stores and retrieves rate records as JSON files keyed by date."""

    def __init__(self: DiskCache, cache_dir: str | Path | None = None) -> None:
        """Initialize the cache, defaulting to the platform cache directory."""
        self.cache_dir = Path(cache_dir) if cache_dir else _xdg_cache_dir()

    def _cache_path(self: DiskCache, date_str: str) -> Path:
        return self.cache_dir / f"{date_str}.json"

    def get(
        self: DiskCache,
        date_str: str,
        ttl_minutes: int | None = None,
        read_only: bool = False,
    ) -> list[RateRecord] | None:
        """Return cached records for ``date_str`` or ``None`` when missing/expired."""
        path = self._cache_path(date_str)
        data = load_payload(path, read_only=read_only)
        if data is None:
            return None
        if not is_valid_entry(data):
            if not read_only:
                path.unlink(missing_ok=True)
            return None
        if self._is_expired(data, ttl_minutes):
            if not read_only:
                path.unlink(missing_ok=True)
            return None
        try:
            return parse_records(data)
        except (KeyError, TypeError, ValueError):
            if not read_only:
                path.unlink(missing_ok=True)
            return None

    def put(
        self: DiskCache,
        date_str: str,
        records: list[RateRecord],
        ttl_minutes: int | None = None,
        *,
        complete: bool = True,
        expected_count: int | None = None,
        source: str | None = None,
    ) -> None:
        """Write ``records`` for ``date_str`` to the cache directory."""
        if not complete or not records:
            return
        expected = len(records) if expected_count is None else expected_count
        if expected != len(records):
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": SCHEMA_VERSION,
            "cached_at": datetime.now(UTC).isoformat(),
            "ttl_minutes": ttl_minutes,
            "complete": True,
            "expected_count": expected,
            "source": source,
            "records": [
                {"day252": r.day252, "day360": r.day360, "rate": r.rate}
                for r in records
            ],
        }
        write_atomic(
            self._cache_path(date_str),
            json.dumps(data, ensure_ascii=False),
        )

    def list_entries(self: DiskCache) -> list[CacheEntry]:
        """Return all valid cache entries without modifying the cache."""
        entries: list[CacheEntry] = []
        if not self.cache_dir.exists():
            return entries
        for path in sorted(self.cache_dir.glob("*.json")):
            try:
                date.fromisoformat(path.stem)
            except ValueError:
                continue
            entry = read_entry(path)
            if entry is not None:
                entries.append(entry)
        return entries

    def last_cached_date(self: DiskCache) -> str | None:
        """Return the most recent valid cache date, or ``None`` when empty."""
        entries = self.list_entries()
        if not entries:
            return None
        return max(entry.date for entry in entries)

    def _is_valid(self: DiskCache, cached_at: str, ttl_minutes: int | None) -> bool:
        if ttl_minutes is None or ttl_minutes <= 0:
            return True
        try:
            cached_dt = datetime.fromisoformat(cached_at)
        except (ValueError, TypeError):
            return False
        age = datetime.now(UTC) - cached_dt
        return age < timedelta(minutes=ttl_minutes)

    def _is_expired(self: DiskCache, data: dict, ttl_minutes: int | None) -> bool:
        """Return ``True`` when the payload is stale according to TTL settings."""
        cached_at = data.get("cached_at")
        stored_ttl = data.get("ttl_minutes")
        if (
            stored_ttl is not None
            and cached_at is not None
            and not self._is_valid(cached_at, stored_ttl)
        ):
            return True
        return ttl_minutes is not None and not self._is_valid(
            cached_at, ttl_minutes
        )

    def housekeeping(self: DiskCache, max_age_days: int = 365) -> None:
        """Delete cached files older than ``max_age_days``."""
        cutoff = datetime.now(UTC).date() - timedelta(days=max_age_days)
        for path in self.cache_dir.glob("*.json"):
            try:
                file_date = date.fromisoformat(path.stem)
            except ValueError:
                continue
            if file_date < cutoff:
                path.unlink(missing_ok=True)
