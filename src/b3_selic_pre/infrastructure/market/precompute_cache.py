"""Cache derivado e pré-cálculo de mercado invalidados por hash."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.infrastructure.action_lock import ActionLock, action_lock
from b3_selic_pre.infrastructure.cache_payload import write_atomic
from b3_selic_pre.infrastructure.market.raw_cache import market_cache_root

PRECOMPUTE_SCHEMA_VERSION = 1
MANIFEST_NAME = "manifest.json"
_LOCK_NAME = "market.lock"

logger = logging.getLogger(__name__)

PayloadBuilder = Callable[[], dict[str, object] | None]


def _empty_manifest() -> dict[str, object]:
    return {
        "schema_version": PRECOMPUTE_SCHEMA_VERSION,
        "latest_data_date": None,
        "keys": {},
    }


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


class MarketPrecomputeCache:
    """Persist derived series and precomputed artifacts keyed by hash."""

    def __init__(
        self: MarketPrecomputeCache,
        cache_dir: str | Path | None = None,
        config: MarketConfig | None = None,
        lock_path: str | Path | None = None,
    ) -> None:
        """Initialize the precompute cache and its lock path."""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else market_cache_root()
        )
        self.config = config or MarketConfig()
        self.manifest_path = self.cache_dir / MANIFEST_NAME
        self.lock_path = lock_path or self.cache_dir / "locks" / _LOCK_NAME

    def lock(self: MarketPrecomputeCache) -> ActionLock:
        """Return the dedicated market lock."""
        return action_lock(path=self.lock_path)

    def derived_path(self: MarketPrecomputeCache, key: str) -> Path:
        """Return the derived series path for ``key``."""
        return self.cache_dir / "derived" / key / "series.json"

    def artifact_path(self: MarketPrecomputeCache, key: str) -> Path:
        """Return the precomputed artifact path for ``key``."""
        return self.cache_dir / "precomputed" / key / "artifact.json"

    def load_manifest(self: MarketPrecomputeCache) -> dict[str, object] | None:
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
        if data.get("schema_version") != PRECOMPUTE_SCHEMA_VERSION:
            return None
        return data

    def _entries(self: MarketPrecomputeCache) -> dict[str, object]:
        manifest = self.load_manifest() or _empty_manifest()
        return dict(_as_dict(manifest.get("keys")))

    def _read_payload(self: MarketPrecomputeCache, path: Path, key: str) -> dict[str, object] | None:
        if not path.exists() or key not in self._entries():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return data if isinstance(data, dict) else None

    def read_derived(self: MarketPrecomputeCache, key: str) -> dict[str, object] | None:
        """Read a derived series for ``key`` when present."""
        return self._read_payload(self.derived_path(key), key)

    def read_artifact(self: MarketPrecomputeCache, key: str) -> dict[str, object] | None:
        """Read a precomputed artifact for ``key`` when present."""
        return self._read_payload(self.artifact_path(key), key)

    def _write_json(self: MarketPrecomputeCache, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(path, json.dumps(payload, ensure_ascii=False))

    def write_manifest(self: MarketPrecomputeCache, manifest: dict[str, object]) -> None:
        """Write the manifest atomically."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(
            self.manifest_path,
            json.dumps(manifest, ensure_ascii=False),
        )

    def _update_manifest(
        self: MarketPrecomputeCache,
        key: str,
        sources: Mapping[str, str],
        latest_data_date: str,
    ) -> None:
        manifest = self.load_manifest() or _empty_manifest()
        entries = dict(_as_dict(manifest.get("keys")))
        entries[key] = {
            "sources": dict(sources),
            "latest_data_date": latest_data_date,
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        manifest["keys"] = entries
        current = manifest.get("latest_data_date")
        if current is None or latest_data_date > str(current):
            manifest["latest_data_date"] = latest_data_date
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(
            self.manifest_path,
            json.dumps(manifest, ensure_ascii=False),
        )

    def write_derived(
        self: MarketPrecomputeCache,
        key: str,
        payload: dict[str, object],
        sources: Mapping[str, str],
        latest_data_date: str,
    ) -> None:
        """Write a derived series atomically and update the manifest."""
        self._write_json(self.derived_path(key), payload)
        self._update_manifest(key, sources, latest_data_date)

    def write_artifact(
        self: MarketPrecomputeCache,
        key: str,
        payload: dict[str, object],
        sources: Mapping[str, str],
        latest_data_date: str,
    ) -> None:
        """Write a precomputed artifact atomically and update the manifest."""
        self._write_json(self.artifact_path(key), payload)
        self._update_manifest(key, sources, latest_data_date)

    def update_if_changed(
        self: MarketPrecomputeCache,
        key: str,
        sources: Mapping[str, str],
        latest_data_date: str,
        build: PayloadBuilder,
    ) -> bool:
        """Build and persist only when ``key`` is absent, isolating failures."""
        if self.read_artifact(key) is not None:
            return False
        try:
            with self.lock():
                if self.read_artifact(key) is not None:
                    return False
                payload = build()
                if payload is None:
                    return False
                self.write_artifact(
                    key, payload, sources, latest_data_date
                )
                return True
        except Exception as exc:
            logger.warning("Falha no pré-cálculo de mercado: %s", exc)
            return False

    def housekeeping(self: MarketPrecomputeCache, latest_data_date: str) -> list[str]:
        """Remove artifacts older than the three-year retention window."""
        from b3_selic_pre.infrastructure.market.housekeeping import (
            run_precompute_housekeeping,
        )

        return run_precompute_housekeeping(self, latest_data_date)

    def stale_keys(
        self: MarketPrecomputeCache, key: str, sources: Mapping[str, str] | None = None
    ) -> list[str]:
        """Return manifest keys invalidated by a different composite key."""
        return [
            name
            for name in self._entries()
            if name != key
            and (
                sources is None
                or _as_dict(self._entries()[name]).get("sources")
                != dict(sources)
            )
        ]


__all__ = [
    "MANIFEST_NAME",
    "PRECOMPUTE_SCHEMA_VERSION",
    "MarketPrecomputeCache",
]
