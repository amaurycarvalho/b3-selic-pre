"""Cliente com cache por recurso para os datasets do Tesouro Direto."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import (
    RESGATE_KEYS,
    TesouroDataError,
    combine_metadata,
    parse_estoque,
    parse_resgates,
    parse_vendas,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)
from b3_selic_pre.infrastructure.tesouro_cache import SCHEMA_VERSION, TesouroCache
from b3_selic_pre.infrastructure.tesouro_cache_presence import (
    TesouroCachePresenceMixin,
)
from b3_selic_pre.infrastructure.tesouro_client import (
    TesouroDownload,
    TesouroResource,
    TesouroSourceClient,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class TesouroDiretoClient(TesouroCachePresenceMixin):
    """Fetches Tesouro datasets through the conditional cached source."""

    def __init__(
        self: TesouroDiretoClient,
        cache: TesouroCache | None = None,
        source: TesouroSourceClient | None = None,
    ) -> None:
        """Initialize the cached client."""
        self._cache = cache or TesouroCache()
        self._source = source or TesouroSourceClient()

    @property
    def cache_dir(self: TesouroDiretoClient) -> object:
        """Expose the base cache directory for resource caches."""
        return self._cache.cache_dir

    def _resource_cache(self: TesouroDiretoClient, key: str) -> TesouroCache:
        return TesouroCache(self._cache.cache_dir, resource=key)

    def read_cached_vendas(
        self: TesouroDiretoClient,
    ) -> tuple[list[VendaTesouroDireto], dict[str, object], str] | None:
        """Read sales from disk without any network access."""
        cached = self._cache.read()
        if cached is None:
            return None
        return parse_vendas(cached[0]), cached[1], "cache"

    def read_cached_estoque(
        self: TesouroDiretoClient,
    ) -> tuple[list[EstoqueTesouroDireto], dict[str, object], str] | None:
        """Read the stock resource from disk without any network access."""
        cached = self._resource_cache("estoque").read()
        if cached is None:
            return None
        return parse_estoque(cached[0]), cached[1], "cache"

    def read_cached_resgates(
        self: TesouroDiretoClient,
    ) -> tuple[list[ResgateTesouroDireto], dict[str, object], str] | None:
        """Read every redemption resource from disk without network access."""
        records: list[ResgateTesouroDireto] = []
        metadata: dict[str, dict[str, object]] = {}
        for key in RESGATE_KEYS:
            cached = self._resource_cache(key).read()
            if cached is None:
                continue
            try:
                records.extend(parse_resgates(cached[0], key))
            except TesouroDataError:
                continue
            metadata[key] = cached[1]
        if not metadata:
            return None
        return records, combine_metadata(metadata), "cache"

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

    def fetch_resgates(
        self: TesouroDiretoClient,
        force: bool = False,
        source_callback: Callable[[str], None] | None = None,
    ) -> tuple[list[ResgateTesouroDireto], dict[str, object], str]:
        """Return all redemption resources, isolating per-resource failures."""
        resources = self._source.discover_resgates()
        records: list[ResgateTesouroDireto] = []
        metadata: dict[str, dict[str, object]] = {}
        errors: list[Exception] = []
        downloaded = False
        for key in RESGATE_KEYS:
            cache = self._resource_cache(key)
            try:
                parsed, meta, origin = self._fetch_one(
                    cache,
                    resources[key],
                    lambda data, key=key: parse_resgates(data, key),
                    lambda items: _redemption_dates(items),
                    force,
                )
                records.extend(parsed)
                metadata[key] = meta
                downloaded = downloaded or origin != "cache"
            except (CommunicationError, TesouroDataError) as exc:
                errors.append(exc)
                fallback = self._fallback(cache, key, exc)
                if fallback is not None:
                    records.extend(fallback[0])
                    metadata[key] = fallback[1]
        if not metadata:
            raise errors[0] if errors else CommunicationError(
                "Nenhum recurso de resgate disponível."
            )
        if source_callback:
            source_callback(
                "Tesouro Transparente" if downloaded else "Cache"
            )
        return records, combine_metadata(metadata), (
            "Tesouro Transparente" if downloaded else "cache"
        )

    def fetch_estoque(
        self: TesouroDiretoClient,
        force: bool = False,
        source_callback: Callable[[str], None] | None = None,
    ) -> tuple[list[EstoqueTesouroDireto], dict[str, object], str]:
        """Return the monthly stock resource, preserving a valid cache."""
        cache = self._resource_cache("estoque")
        resource = self._source.discover_estoque()
        records, metadata, origem = self._fetch_one(
            cache,
            resource,
            parse_estoque,
            _stock_month_range,
            force,
        )
        if source_callback:
            source_callback(
                "Tesouro Transparente" if origem != "cache" else "Cache"
            )
        return records, metadata, origem

    def _fetch_one(
        self: TesouroDiretoClient,
        cache: TesouroCache,
        resource: TesouroResource,
        parser: Callable[[bytes], list[object]],
        date_range: Callable[[list[object]], tuple[str, str]],
        force: bool,
    ) -> tuple[list[object], dict[str, object], str]:
        cached = cache.read()
        if cached is not None and not force and cache.is_fresh(cached[1]):
            return parser(cached[0]), cached[1], "cache"
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
            metadata = cache.update_checked_at(cached[1], _now())
            return parser(cached[0]), metadata, "cache"
        if download.data is None:
            raise CommunicationError("Download do Tesouro sem conteúdo.")
        records = parser(download.data)
        metadata = self._resource_metadata(
            resource, download, records, date_range(records)
        )
        cache.save(download.data, metadata)
        return records, metadata, "Tesouro Transparente"

    @staticmethod
    def _fallback(
        cache: TesouroCache, key: str, exc: Exception
    ) -> tuple[list[object], dict[str, object]] | None:
        cached = cache.read()
        if cached is None:
            return None
        try:
            records = parse_resgates(cached[0], key)
        except TesouroDataError:
            return None
        logger.warning(
            "Recurso %s do Tesouro falhou; reutilizando cache: %s", key, exc
        )
        return records, cached[1]

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
    def _resource_metadata(
        resource: TesouroResource,
        download: TesouroDownload,
        records: list[object],
        date_range: tuple[str, str],
    ) -> dict[str, object]:
        now = _now()
        data = download.data or b""
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
            "row_count": len(records),
            "first_data_date": date_range[0],
            "last_data_date": date_range[1],
        }

    @staticmethod
    def _metadata(
        resource: TesouroResource,
        download: TesouroDownload,
        sales: list[VendaTesouroDireto],
    ) -> dict[str, object]:
        dates = [sale.data_liquidacao for sale in sales]
        return TesouroDiretoClient._resource_metadata(
            resource, download, list(sales), (min(dates), max(dates))
        )


def _redemption_dates(records: list[object]) -> tuple[str, str]:
    dates = [item.data_resgate for item in records]  # type: ignore[attr-defined]
    return min(dates), max(dates)


def _stock_month_range(records: list[object]) -> tuple[str, str]:
    months = [item.mes for item in records]  # type: ignore[attr-defined]
    return min(months), max(months)
