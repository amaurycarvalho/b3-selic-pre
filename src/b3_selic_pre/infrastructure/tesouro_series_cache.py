"""Snapshots das séries pré-calculadas do Tesouro Direto."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path

from b3_selic_pre.application.tesouro import SeriesSourceSnapshot
from b3_selic_pre.infrastructure.tesouro_analytics_cache import (
    TesouroAnalyticsCache,
    analytics_lock,
)
from b3_selic_pre.infrastructure.tesouro_cache import tesouro_cache_dir
from b3_selic_pre.infrastructure.tesouro_series_payload import (
    SERIES_SCHEMA_VERSION,
    StoredSeries,
    payload_from_snapshot,
    stored_from_payload,
)

SERIES_PREFIX = "series"
SERIES_PERIOD = "series"

SOURCE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "estoque": ("estoque", "estoque-btd"),
    "demanda": ("vendas",),
    "fluxo": ("vendas", "recompras"),
}
RAW_FILES: dict[str, str] = {
    "estoque": "estoque.csv",
    "estoque-btd": "estoque-btd.json",
    "vendas": "vendastesourodireto.csv",
    "recompras": "recompras.csv",
}
OPTIONAL_SOURCES = frozenset({"estoque-btd"})
ABSENT_SENTINEL = "<absent>"


def composite_hash(hashes: Mapping[str, str]) -> str:
    """Return a stable hash for a snapshot's source hashes."""
    content = "\n".join(
        f"{name}={value}" for name, value in sorted(hashes.items())
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def source_hashes(
    raw_dir: str | Path | None,
    names: tuple[str, ...],
) -> dict[str, str] | None:
    """Read the hashes of the requested raw sources."""
    directory = Path(raw_dir) if raw_dir else tesouro_cache_dir()
    result: dict[str, str] = {}
    for name in names:
        value = _file_hash(directory / RAW_FILES[name])
        if value is None:
            if name in OPTIONAL_SOURCES:
                result[name] = ABSENT_SENTINEL
                continue
            return None
        result[name] = value
    return result


class TesouroSeriesCache:
    """Persist and invalidate precomputed series snapshots."""

    def __init__(
        self: TesouroSeriesCache,
        cache: TesouroAnalyticsCache | None = None,
        raw_dir: str | Path | None = None,
        lock_path: str | Path | None = None,
    ) -> None:
        """Initialize the adapter."""
        self.cache = cache or TesouroAnalyticsCache()
        self.raw_dir = Path(raw_dir) if raw_dir else tesouro_cache_dir()
        self.lock_path = lock_path

    def _partition(self: TesouroSeriesCache, name: str) -> str:
        return f"{SERIES_PREFIX}/{name}"

    def expected_hashes(
        self: TesouroSeriesCache,
        name: str,
    ) -> dict[str, str] | None:
        """Return the current hashes of a snapshot's raw sources."""
        return source_hashes(self.raw_dir, SOURCE_DEPENDENCIES[name])

    def read(
        self: TesouroSeriesCache,
        name: str,
        expected_hashes: Mapping[str, str] | None = None,
    ) -> StoredSeries | None:
        """Read a snapshot when its schema and source hashes match."""
        digest = (
            composite_hash(expected_hashes)
            if expected_hashes is not None
            else None
        )
        content = self.cache.read_partition(
            self._partition(name),
            source_sha256=digest,
        )
        if content is None:
            return None
        try:
            payload = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        stored = stored_from_payload(payload)
        if stored is None or stored.name != name:
            return None
        if (
            expected_hashes is not None
            and stored.source_hashes != dict(expected_hashes)
        ):
            return None
        return stored

    def write(
        self: TesouroSeriesCache,
        snapshot: SeriesSourceSnapshot,
        *,
        source: str,
        extracted_at: str | None,
        expected_hashes: Mapping[str, str],
    ) -> None:
        """Write a snapshot atomically and update the manifest last."""
        payload = payload_from_snapshot(
            snapshot,
            source=source,
            extracted_at=extracted_at,
            hashes=expected_hashes,
        )
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.cache.write_partition(
            self._partition(snapshot.name),
            content,
            source_sha256=composite_hash(expected_hashes),
            latest_data_date=snapshot.latest_data_date,
            period=SERIES_PERIOD,
        )

    def has(self: TesouroSeriesCache, name: str) -> bool:
        """Return whether a snapshot can be read without hash validation."""
        return self.read(name) is not None

    def update_if_changed(
        self: TesouroSeriesCache,
        name: str,
        expected_hashes: Mapping[str, str] | None,
        build: Callable[[], SeriesSourceSnapshot | None],
        *,
        source: str,
        extracted_at: str | None,
    ) -> bool:
        """Build and persist a snapshot only when its source changed."""
        if expected_hashes is None:
            return False
        if self.read(name, expected_hashes) is not None:
            return False
        with analytics_lock(path=self.lock_path):
            current = self.expected_hashes(name)
            if current is None or current != dict(expected_hashes):
                return False
            if self.read(name, expected_hashes) is not None:
                return False
            snapshot = build()
            if snapshot is None:
                return False
            self.write(
                snapshot,
                source=source,
                extracted_at=extracted_at,
                expected_hashes=expected_hashes,
            )
            return True


__all__ = [
    "ABSENT_SENTINEL",
    "OPTIONAL_SOURCES",
    "RAW_FILES",
    "SERIES_PREFIX",
    "SERIES_SCHEMA_VERSION",
    "SOURCE_DEPENDENCIES",
    "StoredSeries",
    "TesouroSeriesCache",
    "composite_hash",
    "source_hashes",
]
