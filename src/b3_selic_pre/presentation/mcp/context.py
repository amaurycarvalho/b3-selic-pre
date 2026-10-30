"""Contexto e porta de leitura de cache usados pelas tools MCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from b3_selic_pre.domain.models import RateRecord


class CacheReader(Protocol):
    """Contrato mínimo de leitura de cache usado pelas tools."""

    def get(
        self: CacheReader,
        date_str: str,
        ttl_minutes: int | None = None,
        read_only: bool = False,
    ) -> list[RateRecord] | None:
        """Return cached records or ``None``."""

    def list_entries(self: CacheReader) -> list[object]:
        """Return metadata for valid cache entries."""

    def last_cached_date(self: CacheReader) -> str | None:
        """Return the newest valid cache date."""


@dataclass
class ToolContext:
    """Dependências injetadas nas tools."""

    cache: CacheReader
    settings_factory: Callable[[], object]
    tesouro_cache: object | None = None
