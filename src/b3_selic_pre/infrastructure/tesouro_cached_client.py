"""Cliente com cache para as vendas do Tesouro Direto."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import parse_vendas
from b3_selic_pre.domain.models import VendaTesouroDireto
from b3_selic_pre.infrastructure.tesouro_cache import SCHEMA_VERSION, TesouroCache
from b3_selic_pre.infrastructure.tesouro_client import (
    TesouroDownload,
    TesouroResource,
    TesouroSourceClient,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class TesouroDiretoClient:
    """Fetches Tesouro sales through the conditional cached source."""

    def __init__(
        self: TesouroDiretoClient,
        cache: TesouroCache | None = None,
        source: TesouroSourceClient | None = None,
    ) -> None:
        """Initialize the cached client."""
        self._cache = cache or TesouroCache()
        self._source = source or TesouroSourceClient()

    def fetch_vendas(
        self: TesouroDiretoClient,
        force: bool = False,
        source_callback: Callable[[str], None] | None = None,
    ) -> tuple[list[VendaTesouroDireto], dict[str, object], str]:
        """Return sales, metadata and origin, using the cache when valid."""
        cached = self._cache.read()
        if cached is not None and not force and self._cache.is_fresh(cached[1]):
            return self._from_cache(cached, source_callback)
        resource = self._source.discover()
        download = self._source.download(
            resource,
            etag=self._cached_value(cached, "etag"),
            last_modified=self._cached_value(cached, "last_modified"),
        )
        if download.status == 304:
            if cached is None:
                raise CommunicationError(
                    "Tesouro respondeu 304 sem cache local disponível."
                )
            metadata = self._cache.update_checked_at(cached[1], _now())
            return self._from_cache((cached[0], metadata), source_callback)
        if download.data is None:
            raise CommunicationError("Download do Tesouro sem conteúdo.")
        sales = parse_vendas(download.data)
        metadata = self._metadata(resource, download, sales)
        self._cache.save(download.data, metadata)
        if source_callback:
            source_callback("Tesouro Transparente")
        return sales, metadata, "Tesouro Transparente"

    @staticmethod
    def _cached_value(
        cached: tuple[bytes, dict[str, object]] | None, key: str
    ) -> str | None:
        if cached is None:
            return None
        value = cached[1].get(key)
        return value if isinstance(value, str) and value else None

    def _from_cache(
        self: TesouroDiretoClient,
        cached: tuple[bytes, dict[str, object]],
        source_callback: Callable[[str], None] | None,
    ) -> tuple[list[VendaTesouroDireto], dict[str, object], str]:
        sales = parse_vendas(cached[0])
        if source_callback:
            source_callback("Cache")
        return sales, cached[1], "cache"

    @staticmethod
    def _metadata(
        resource: TesouroResource,
        download: TesouroDownload,
        sales: list[VendaTesouroDireto],
    ) -> dict[str, object]:
        now = _now()
        data = download.data or b""
        dates = [sale.data_liquidacao for sale in sales]
        return {
            "schema_version": SCHEMA_VERSION,
            "dataset_name": resource.dataset_name,
            "dataset_id": resource.dataset_id,
            "resource_id": resource.resource_id,
            "resource_url": resource.resource_url,
            "etag": download.etag,
            "last_modified": download.last_modified or resource.last_modified,
            "downloaded_at": now,
            "checked_at": now,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "row_count": len(sales),
            "first_data_date": min(dates),
            "last_data_date": max(dates),
        }
