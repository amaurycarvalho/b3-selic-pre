import json
import os
import platform
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from b3_selic_pre.domain.models import RateRecord


def _xdg_cache_dir():
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
    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else _xdg_cache_dir()

    def _cache_path(self, date_str):
        return self.cache_dir / f"{date_str}.json"

    def get(self, date_str, ttl_minutes=None):
        path = self._cache_path(date_str)
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            path.unlink(missing_ok=True)
            return None
        cached_at = data.get("cached_at")
        ttl = data.get("ttl_minutes")
        if ttl is not None and cached_at is not None:
            if not self._is_valid(cached_at, ttl):
                path.unlink(missing_ok=True)
                return None
        if ttl_minutes is not None:
            if not self._is_valid(cached_at, ttl_minutes):
                path.unlink(missing_ok=True)
                return None
        raw_records = data.get("records")
        if not isinstance(raw_records, list):
            path.unlink(missing_ok=True)
            return None
        try:
            return [
                RateRecord(
                    day252=int(r["day252"]),
                    day360=int(r["day360"]),
                    rate=str(r["rate"]),
                )
                for r in raw_records
            ]
        except (KeyError, TypeError, ValueError):
            path.unlink(missing_ok=True)
            return None

    def put(self, date_str, records, ttl_minutes=None):
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

    def _is_valid(self, cached_at, ttl_minutes):
        if ttl_minutes is None or ttl_minutes <= 0:
            return True
        try:
            cached_dt = datetime.fromisoformat(cached_at)
        except (ValueError, TypeError):
            return False
        age = datetime.now(timezone.utc) - cached_dt
        return age < timedelta(minutes=ttl_minutes)

    def housekeeping(self, max_age_days=365):
        cutoff = date.today() - timedelta(days=max_age_days)
        for path in self.cache_dir.glob("*.json"):
            date_str = path.stem
            try:
                file_date = date.fromisoformat(date_str)
            except ValueError:
                continue
            if file_date < cutoff:
                path.unlink(missing_ok=True)
