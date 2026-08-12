"""Disk-backed JSON cache for historical B3 rate records."""

from __future__ import annotations

import json
import os
import platform
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from b3_selic_pre.domain.models import RateRecord


def _xdg_cache_dir() -> Path:
    system = platform.system()
    if system == "Linux":
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path.home() / ".cache"
    return base / "b3-selic-pre" / "rates"


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
    ) -> list[RateRecord] | None:
        """Return cached records for ``date_str`` or ``None`` when missing/expired."""
        path = self._cache_path(date_str)
        data = self._load_payload(path)
        if data is None:
            return None
        if self._is_expired(data, ttl_minutes):
            path.unlink(missing_ok=True)
            return None
        try:
            return self._parse_records(data)
        except (KeyError, TypeError, ValueError):
            path.unlink(missing_ok=True)
            return None

    def _load_payload(self: DiskCache, path: Path) -> dict | None:
        """Load the JSON payload from ``path`` or ``None`` when missing/corrupt."""
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            path.unlink(missing_ok=True)
            return None

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

    @staticmethod
    def _parse_records(data: dict) -> list[RateRecord]:
        """Parse ``data["records"]`` into rate records, raising on invalid input."""
        raw_records = data.get("records")
        if not isinstance(raw_records, list):
            raise TypeError("invalid records payload")
        return [
            RateRecord(
                day252=int(r["day252"]),
                day360=int(r["day360"]),
                rate=str(r["rate"]),
            )
            for r in raw_records
        ]

    def put(
        self: DiskCache,
        date_str: str,
        records: list[RateRecord],
        ttl_minutes: int | None = None,
    ) -> None:
        """Write ``records`` for ``date_str`` to the cache directory."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_minutes": ttl_minutes,
            "records": [
                {"day252": r.day252, "day360": r.day360, "rate": r.rate}
                for r in records
            ],
        }
        path = self._cache_path(date_str)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def _is_valid(self: DiskCache, cached_at: str, ttl_minutes: int | None) -> bool:
        if ttl_minutes is None or ttl_minutes <= 0:
            return True
        try:
            cached_dt = datetime.fromisoformat(cached_at)
        except (ValueError, TypeError):
            return False
        age = datetime.now(timezone.utc) - cached_dt
        return age < timedelta(minutes=ttl_minutes)

    def housekeeping(self: DiskCache, max_age_days: int = 365) -> None:
        """Delete cached files older than ``max_age_days``."""
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=max_age_days)
        for path in self.cache_dir.glob("*.json"):
            date_str = path.stem
            try:
                file_date = date.fromisoformat(date_str)
            except ValueError:
                continue
            if file_date < cutoff:
                path.unlink(missing_ok=True)
