"""Cache em disco por recurso do Tesouro Direto."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from b3_selic_pre.application.tesouro import (
    TesouroResourceSpec,
    resource_spec,
)
from b3_selic_pre.application.tesouro._resources import TTL_DAILY
from b3_selic_pre.infrastructure.cache_payload import (
    write_atomic,
    write_atomic_bytes,
)
from b3_selic_pre.infrastructure.xdg import cache_base

SCHEMA_VERSION = 1
CSV_NAME = "vendastesourodireto.csv"
METADATA_NAME = "metadata.json"
CURRENT_TTL = timedelta(hours=1)
HISTORICAL_TTL = timedelta(hours=6)
DAILY_TTL = timedelta(hours=24)
_REQUIRED_METADATA = (
    "schema_version",
    "dataset_name",
    "dataset_id",
    "resource_id",
    "resource_url",
    "downloaded_at",
    "checked_at",
    "size_bytes",
    "row_count",
)


def tesouro_cache_dir() -> Path:
    """Return the default Tesouro cache directory."""
    return cache_base() / "b3-selic-pre" / "tesouro"


def default_tesouro_lock_path() -> Path:
    """Return the dedicated lock path for Tesouro downloads."""
    return tesouro_cache_dir() / "tesouro.lock"


def _last_business_day(today: date) -> date:
    current = today
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def is_current(metadata: dict[str, object], today: date | None = None) -> bool:
    """Return whether the cached dataset reaches the current/last business day."""
    raw = metadata.get("last_data_date")
    if not isinstance(raw, str):
        return False
    try:
        latest = date.fromisoformat(raw)
    except ValueError:
        return False
    today = today or datetime.now(UTC).date()
    return latest >= _last_business_day(today)


def ttl_for(
    metadata: dict[str, object],
    today: date | None = None,
    resource: str = "vendas",
) -> timedelta:
    """Return the TTL for a cached resource metadata."""
    if resource_spec(resource).ttl_policy == TTL_DAILY:
        return DAILY_TTL
    return CURRENT_TTL if is_current(metadata, today) else HISTORICAL_TTL


def _valid_metadata(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("schema_version") != SCHEMA_VERSION:
        return False
    if any(key not in data for key in _REQUIRED_METADATA):
        return False
    row_count = data.get("row_count")
    size_bytes = data.get("size_bytes")
    return (
        isinstance(row_count, int)
        and row_count > 0
        and isinstance(size_bytes, int)
        and size_bytes > 0
    )


class TesouroCache:
    """Stores one resource CSV and its metadata atomically."""

    def __init__(
        self: TesouroCache,
        cache_dir: str | Path | None = None,
        resource: str = "vendas",
    ) -> None:
        """Initialize the cache directory for a logical resource."""
        self.cache_dir = Path(cache_dir) if cache_dir else tesouro_cache_dir()
        self.spec: TesouroResourceSpec = resource_spec(resource)

    @property
    def csv_path(self: TesouroCache) -> Path:
        """Return the resource CSV path."""
        return self.cache_dir / self.spec.csv_filename

    @property
    def metadata_path(self: TesouroCache) -> Path:
        """Return the resource metadata JSON path."""
        return self.cache_dir / self.spec.metadata_filename

    def read(self: TesouroCache, read_only: bool = True) -> tuple[bytes, dict[str, object]] | None:
        """Read a valid cached CSV and metadata without modifying anything."""
        metadata = self._read_metadata()
        if metadata is None:
            return None
        try:
            data = self.csv_path.read_bytes()
        except OSError:
            return None
        if not data:
            return None
        return data, metadata

    def _read_metadata(self: TesouroCache) -> dict[str, object] | None:
        if not self.metadata_path.exists():
            return None
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not _valid_metadata(data):
            return None
        return data

    def has_data(self: TesouroCache) -> bool:
        """Return whether a valid CSV and metadata exist on disk."""
        if self._read_metadata() is None:
            return False
        try:
            return self.csv_path.stat().st_size > 0
        except OSError:
            return False

    def is_fresh(
        self: TesouroCache, metadata: dict[str, object], now: datetime | None = None
    ) -> bool:
        """Return whether ``checked_at`` is still inside the conditional TTL."""
        raw = metadata.get("checked_at")
        if not isinstance(raw, str):
            return False
        try:
            checked = datetime.fromisoformat(raw)
        except ValueError:
            return False
        now = now or datetime.now(UTC)
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=UTC)
        return now - checked < ttl_for(
            metadata, now.date(), self.spec.key
        )

    def save(self: TesouroCache, data: bytes, metadata: dict[str, object]) -> None:
        """Write the CSV bytes and metadata atomically."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        write_atomic_bytes(self.csv_path, data)
        write_atomic(
            self.metadata_path,
            json.dumps(metadata, ensure_ascii=False),
        )

    def update_checked_at(
        self: TesouroCache,
        metadata: dict[str, object],
        checked_at: str | None = None,
    ) -> dict[str, object]:
        """Update only ``checked_at`` and rewrite the metadata atomically."""
        updated = dict(metadata)
        updated["checked_at"] = checked_at or datetime.now(UTC).isoformat()
        write_atomic(
            self.metadata_path,
            json.dumps(updated, ensure_ascii=False),
        )
        return updated
