"""Cache em disco dos feriados por ano, com lock e escrita atômica."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from b3_selic_pre.application.calendar.config import CalendarConfig
from b3_selic_pre.application.calendar.ports import YearHolidays
from b3_selic_pre.infrastructure.action_lock import action_lock
from b3_selic_pre.infrastructure.cache_payload import write_atomic
from b3_selic_pre.infrastructure.calendar.housekeeping import run_housekeeping
from b3_selic_pre.infrastructure.calendar.storage import (
    SCHEMA_VERSION,
    decode_year,
    encode_year,
)
from b3_selic_pre.infrastructure.xdg import cache_base


def calendar_cache_dir() -> Path:
    """Return the default calendar cache directory."""
    return cache_base() / "b3-selic-pre" / "calendar"


def default_calendar_lock_path() -> Path:
    """Return the dedicated calendar lock path."""
    return calendar_cache_dir() / "locks" / "calendar.lock"


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class HolidayCache:
    """Stores one JSON file per year with TTL and provenance metadata."""

    def __init__(
        self: HolidayCache,
        cache_dir: str | Path | None = None,
        config: CalendarConfig | None = None,
    ) -> None:
        """Initialize the cache directory and TTL configuration."""
        self.cache_dir = Path(cache_dir) if cache_dir else calendar_cache_dir()
        self.config = config or CalendarConfig()
        self.holidays_dir = self.cache_dir / "holidays"
        self.lock_path = self.cache_dir / "locks" / "calendar.lock"

    def path(self: HolidayCache, year: int) -> Path:
        """Return the JSON path of ``year``."""
        return self.holidays_dir / f"{year}.json"

    def read(self: HolidayCache, year: int) -> YearHolidays | None:
        """Read one year without creating or changing any file."""
        target = self.path(year)
        if not target.exists():
            return None
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return decode_year(data, year)

    def years(self: HolidayCache) -> list[int]:
        """Return years with valid, published holiday data."""
        if not self.holidays_dir.exists():
            return []
        years: list[int] = []
        for path in sorted(self.holidays_dir.glob("*.json")):
            try:
                year = int(path.stem)
            except ValueError:
                continue
            data = self.read(year)
            if data is not None and data.published and data.holidays:
                years.append(year)
        return sorted(years)

    def is_fresh(
        self: HolidayCache, year: int, now: datetime | None = None
    ) -> bool:
        """Return whether the cached year is inside its recency TTL."""
        data = self.read(year)
        if data is None:
            return False
        current = now or datetime.now(UTC)
        if data.published and year < current.year:
            return True
        fetched = _parse_datetime(data.fetched_at)
        if fetched is None:
            return False
        return (current - fetched).total_seconds() < self._ttl(data, current)

    def _ttl(self: HolidayCache, data: YearHolidays, now: datetime) -> int:
        if data.ttl_seconds is not None:
            return data.ttl_seconds
        if data.published:
            return self._ttl_for(data.year, now)
        return self.config.ttl_negativo_segundos

    def _ttl_for(self: HolidayCache, year: int, now: datetime) -> int:
        if year > now.year:
            return self.config.ttl_futuro_segundos
        return self.config.ttl_corrente_segundos

    def write(self: HolidayCache, data: YearHolidays) -> None:
        """Write one year atomically under the dedicated calendar lock."""
        with action_lock(path=self.lock_path):
            self.holidays_dir.mkdir(parents=True, exist_ok=True)
            ttl = data.ttl_seconds or self._ttl(data, datetime.now(UTC))
            payload = encode_year(data, ttl)
            write_atomic(
                self.path(data.year),
                json.dumps(payload, ensure_ascii=False),
            )

    def housekeeping(self: HolidayCache, reference_year: int) -> None:
        """Remove files outside the retention window under the same lock."""
        with action_lock(path=self.lock_path):
            run_housekeeping(self.holidays_dir, reference_year)


__all__ = [
    "SCHEMA_VERSION",
    "HolidayCache",
    "calendar_cache_dir",
    "default_calendar_lock_path",
]
