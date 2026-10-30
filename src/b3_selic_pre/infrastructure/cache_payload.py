"""Pure helpers for reading and writing rate cache payloads."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from b3_selic_pre.domain.models import RateRecord

SCHEMA_VERSION = 2


@dataclass(frozen=True)
class CacheEntry:
    """Metadata and records for one valid cache entry."""

    date: str
    count: int
    cached_at: str | None
    source: str | None
    records: list[RateRecord]


def load_payload(path: Path, read_only: bool = False) -> dict | None:
    """Load a JSON object from ``path`` or return ``None`` when missing/invalid."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        if not read_only:
            path.unlink(missing_ok=True)
        return None
    if not isinstance(data, dict):
        if not read_only:
            path.unlink(missing_ok=True)
        return None
    return data


def is_valid_entry(data: dict) -> bool:
    """Return whether the payload has the current schema and complete data."""
    if data.get("schema_version") != SCHEMA_VERSION:
        return False
    if data.get("complete") is not True:
        return False
    raw_records = data.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        return False
    expected_count = data.get("expected_count")
    if not isinstance(expected_count, int):
        return False
    return len(raw_records) == expected_count


def parse_records(data: dict) -> list[RateRecord]:
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


def write_atomic(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically using a same-dir temp file."""
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def write_atomic_bytes(path: Path, content: bytes) -> None:
    """Write ``content`` bytes atomically using a same-dir temp file."""
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def read_entry(path: Path) -> CacheEntry | None:
    """Read one valid cache entry without modifying the file."""
    data = load_payload(path, read_only=True)
    if data is None or not is_valid_entry(data):
        return None
    try:
        records = parse_records(data)
    except (KeyError, TypeError, ValueError):
        return None
    return CacheEntry(
        date=path.stem,
        count=len(records),
        cached_at=data.get("cached_at"),
        source=data.get("source"),
        records=records,
    )
