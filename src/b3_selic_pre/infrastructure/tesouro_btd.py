"""Atualização do estoque complementar do Balanço do Tesouro Direto."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime

from b3_selic_pre.infrastructure.tesouro_btd_cache import TesouroBtdCache
from b3_selic_pre.infrastructure.tesouro_btd_source import BtdSourceClient
from b3_selic_pre.infrastructure.tesouro_btd_types import (
    BtdCacheEntry,
    BtdEdition,
)
from b3_selic_pre.infrastructure.tesouro_btd_xlsx import parse_btd_xlsx


def _now() -> datetime:
    return datetime.now(UTC)


class TesouroBtdClient:
    """Coordinates discovery, download, XLSX parsing and the BTD cache."""

    def __init__(
        self: TesouroBtdClient,
        cache: TesouroBtdCache | None = None,
        source: BtdSourceClient | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize the adapter with injectable cache, source and clock."""
        self._cache = cache or TesouroBtdCache()
        self._source = source or BtdSourceClient()
        self._now = now or _now

    def read_cached(self: TesouroBtdClient) -> BtdCacheEntry | None:
        """Return the normalized overlay cache without touching the network."""
        return self._cache.read()

    def refresh(self: TesouroBtdClient, force: bool = False) -> BtdCacheEntry:
        """Return a fresh cache or update it after a successful download."""
        cached = self._cache.read()
        if (
            cached is not None
            and not force
            and self._cache.is_fresh(cached.metadata, self._now())
        ):
            return cached
        edition = self._source.discover()
        data = self._source.download(edition)
        records = tuple(parse_btd_xlsx(data))
        metadata = self._metadata(edition, data)
        self._cache.save(records, metadata)
        return BtdCacheEntry(records, metadata)

    def _metadata(
        self: TesouroBtdClient, edition: BtdEdition, data: bytes
    ) -> dict[str, object]:
        return {
            "reference_month": edition.reference_month,
            "published_at": edition.published_at,
            "page_url": edition.page_url,
            "attachment_url": edition.attachment_url,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "checked_at": self._now().isoformat(),
        }


__all__ = ["TesouroBtdClient"]
