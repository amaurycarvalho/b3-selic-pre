"""Sobreposição do estoque agregado do BTD sobre o estoque detalhado do CKAN."""

from __future__ import annotations

from collections.abc import Iterable

from b3_selic_pre.application.tesouro._series_contract import EstoqueRecord
from b3_selic_pre.domain.models import EstoqueMensalTitulo


def merge_estoque(
    ckan: Iterable[EstoqueRecord],
    btd: Iterable[EstoqueMensalTitulo],
) -> tuple[EstoqueRecord, ...]:
    """Add BTD months newer than the CKAN, never overlapping ones.

    The BTD titles are aggregates by indexer and cannot be matched one-to-one
    with the CKAN maturity titles. Adding overlapping months would therefore
    double-count the CKAN stock instead of filling only the newest gap.
    """
    records = list(ckan)
    latest = max((item.mes for item in records), default=None)
    existing = {(item.tipo_titulo, item.mes) for item in records}
    overlay: list[EstoqueMensalTitulo] = []
    for item in btd:
        if latest is not None and item.mes <= latest:
            continue
        key = (item.tipo_titulo, item.mes)
        if key in existing:
            continue
        existing.add(key)
        overlay.append(item)
    return tuple(records + overlay)


__all__ = ["merge_estoque"]
