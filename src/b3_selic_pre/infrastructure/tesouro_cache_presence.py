"""Consultas baratas de presença de cache do Tesouro Direto."""

from __future__ import annotations

from b3_selic_pre.application.tesouro import RESGATE_KEYS
from b3_selic_pre.infrastructure.tesouro_cache import TesouroCache


class TesouroCachePresenceMixin:
    """Métodos de presença de cache usados pelo cliente do Tesouro."""

    _cache: TesouroCache

    def _resource_cache(self: TesouroCachePresenceMixin, key: str) -> TesouroCache:
        """Return the cache of a resource; provided by the concrete client."""
        raise NotImplementedError

    def has_cached_vendas(self: TesouroCachePresenceMixin) -> bool:
        """Return whether sales data exists in the local cache."""
        return self._cache.has_data()

    def has_cached_estoque(self: TesouroCachePresenceMixin) -> bool:
        """Return whether the stock resource exists in the local cache."""
        return self._resource_cache("estoque").has_data()

    def has_cached_resgates(self: TesouroCachePresenceMixin) -> bool:
        """Return whether any redemption resource exists in the local cache."""
        return any(
            self._resource_cache(key).has_data() for key in RESGATE_KEYS
        )
