"""Tipos compartilhados pelo adaptador da publicação BTD."""

from __future__ import annotations

from dataclasses import dataclass

from b3_selic_pre.domain.models import EstoqueMensalTitulo


@dataclass(frozen=True)
class BtdEdition:
    """Edição identificada do Balanço do Tesouro Direto."""

    reference_month: str
    published_at: str | None
    page_url: str
    attachment_url: str


@dataclass(frozen=True)
class BtdResponse:
    """Resposta HTTP bruta usada por descoberta e download."""

    status: int
    url: str
    headers: object
    body: bytes


@dataclass(frozen=True)
class BtdCacheEntry:
    """Conteúdo normalizado e metadados de proveniência do BTD."""

    records: tuple[EstoqueMensalTitulo, ...]
    metadata: dict[str, object]


__all__ = ["BtdCacheEntry", "BtdEdition", "BtdResponse"]
