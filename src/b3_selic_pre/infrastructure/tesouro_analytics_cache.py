"""Cache analítico derivado dos datasets do Tesouro Direto."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from b3_selic_pre.infrastructure.action_lock import ActionLock, action_lock
from b3_selic_pre.infrastructure.cache_payload import (
    write_atomic,
    write_atomic_bytes,
)
from b3_selic_pre.infrastructure.tesouro_analytics_housekeeping import (
    run_housekeeping,
)
from b3_selic_pre.infrastructure.tesouro_cache import tesouro_cache_dir

SCHEMA_VERSION = 2
MANIFEST_NAME = "manifest.json"
_LOCK_NAME = "analytics.lock"


def analytics_cache_dir() -> Path:
    """Return the default analytics cache directory."""
    return tesouro_cache_dir() / "analytics"


def default_analytics_lock_path() -> Path:
    """Return the dedicated analytics lock path."""
    return tesouro_cache_dir() / "locks" / _LOCK_NAME


def analytics_lock(
    path: str | Path | None = None,
    timeout: float = 300.0,
    poll: float = 0.1,
) -> ActionLock:
    """Return the dedicated lock used by CLI/GUI analytics composition."""
    return action_lock(
        path=path or default_analytics_lock_path(),
        timeout=timeout,
        poll=poll,
    )


def _empty_manifest() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "latest_data_date": None,
        "sources": {},
        "partitions": {},
    }


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _partitions(manifest: dict[str, object]) -> dict[str, object]:
    return _as_dict(manifest.get("partitions"))


def _entry(manifest: dict[str, object], name: str) -> dict[str, object]:
    return _as_dict(_partitions(manifest).get(name))


class TesouroAnalyticsCache:
    """Stores derived partitions and an atomic manifest entry point."""

    def __init__(
        self: TesouroAnalyticsCache,
        cache_dir: str | Path | None = None,
    ) -> None:
        """Initialize the analytics cache under ``cache_dir``."""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else analytics_cache_dir()
        )
        self.manifest_path = self.cache_dir / MANIFEST_NAME

    def load_manifest(self: TesouroAnalyticsCache) -> dict[str, object] | None:
        """Read the manifest without modifying any file."""
        if not self.manifest_path.exists():
            return None
        try:
            data = json.loads(
                self.manifest_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict):
            return None
        if data.get("schema_version") != SCHEMA_VERSION:
            return None
        return data

    def partition_path(
        self: TesouroAnalyticsCache, name: str
    ) -> Path:
        """Return the path of a named partition."""
        return self.cache_dir / f"{name}.json"

    def write_partition(
        self: TesouroAnalyticsCache,
        name: str,
        content: bytes,
        *,
        source_sha256: str,
        latest_data_date: str,
        period: str | None = None,
    ) -> None:
        """Write a partition atomically and update the manifest last."""
        target = self.partition_path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        write_atomic_bytes(target, content)
        manifest = self.load_manifest() or _empty_manifest()
        manifest["latest_data_date"] = latest_data_date
        partitions = dict(_partitions(manifest))
        partitions[name] = {
            "source_sha256": source_sha256,
            "latest_data_date": latest_data_date,
            "period": period or name.rsplit("/", 1)[-1],
        }
        manifest["partitions"] = partitions
        write_atomic(
            self.manifest_path,
            json.dumps(manifest, ensure_ascii=False),
        )

    def read_partition(
        self: TesouroAnalyticsCache,
        name: str,
        *,
        source_sha256: str | None = None,
        latest_data_date: str | None = None,
    ) -> bytes | None:
        """Read a partition when its source metadata still matches."""
        manifest = self.load_manifest()
        if manifest is None:
            return None
        entry = _entry(manifest, name)
        if not entry:
            return None
        if (
            source_sha256 is not None
            and entry.get("source_sha256") != source_sha256
        ):
            return None
        if (
            latest_data_date is not None
            and entry.get("latest_data_date") != latest_data_date
        ):
            return None
        try:
            return self.partition_path(name).read_bytes()
        except OSError:
            return None

    def read_or_compute(
        self: TesouroAnalyticsCache,
        name: str,
        compute: Callable[[], bytes],
        *,
        source_sha256: str,
        latest_data_date: str,
        period: str | None = None,
    ) -> tuple[bytes, bool]:
        """Return a valid partition or recompute and store an invalid one."""
        cached = self.read_partition(
            name,
            source_sha256=source_sha256,
            latest_data_date=latest_data_date,
        )
        if cached is not None:
            return cached, False
        content = compute()
        self.write_partition(
            name,
            content,
            source_sha256=source_sha256,
            latest_data_date=latest_data_date,
            period=period,
        )
        return content, True

    def stale_partitions(
        self: TesouroAnalyticsCache,
        *,
        source_sha256: str | None = None,
        latest_data_date: str | None = None,
    ) -> list[str]:
        """Return partition names invalidated by a source change."""
        manifest = self.load_manifest()
        if manifest is None:
            return []
        stale: list[str] = []
        for name, raw in sorted(_partitions(manifest).items()):
            entry = _as_dict(raw)
            changed_hash = (
                source_sha256 is not None
                and entry.get("source_sha256") != source_sha256
            )
            changed_date = (
                latest_data_date is not None
                and entry.get("latest_data_date") != latest_data_date
            )
            if changed_hash or changed_date:
                stale.append(name)
        return stale

    def housekeeping(
        self: TesouroAnalyticsCache,
        latest_data_date: str,
    ) -> list[str]:
        """Remove partitions older than the three-year retention window."""
        return run_housekeeping(self, latest_data_date)

    def write_manifest(
        self: TesouroAnalyticsCache,
        manifest: dict[str, object],
    ) -> None:
        """Write the manifest atomically."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(
            self.manifest_path,
            json.dumps(manifest, ensure_ascii=False),
        )
