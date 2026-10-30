"""Combinação fail-soft do estoque CKAN com a sobreposição BTD."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from b3_selic_pre.application.tesouro import EstoqueRecord, merge_estoque
from b3_selic_pre.domain.models import EstoqueMensalTitulo

logger = logging.getLogger(__name__)

BtdClient = Any
Overlay = tuple[
    tuple[EstoqueRecord, ...], str | None, str | None, str | None
]


def btd_records(entry: object) -> tuple[EstoqueMensalTitulo, ...]:
    """Return the normalized records of a BTD cache entry."""
    records = getattr(entry, "records", ()) if entry is not None else ()
    return tuple(records or ())


def cached_btd(
    btd_client: BtdClient,
) -> tuple[tuple[EstoqueMensalTitulo, ...], str | None]:
    """Read the BTD cache without network, reporting a non-fatal failure."""
    if btd_client is None:
        return (), None
    try:
        entry = btd_client.read_cached()
    except Exception as exc:
        logger.warning("Falha ao ler o cache BTD: %s", exc)
        return (), f"Complemento BTD indisponível: {exc}"
    return btd_records(entry), None


def refresh_btd(
    btd_client: BtdClient, force: bool
) -> tuple[tuple[EstoqueMensalTitulo, ...], str | None]:
    """Refresh the BTD overlay, falling back to the previous cache."""
    if btd_client is None:
        return (), None
    try:
        entry = btd_client.refresh(force=force)
    except Exception as exc:
        logger.warning("Falha ao atualizar o BTD: %s", exc)
        records, _previous_error = cached_btd(btd_client)
        return records, f"Complemento BTD não atualizado: {exc}"
    return btd_records(entry), None


def overlay(
    records: Sequence[EstoqueRecord],
    btd: Sequence[EstoqueMensalTitulo],
    warning: str | None,
) -> Overlay:
    """Merge the overlay and derive latest month and status note."""
    merged = merge_estoque(records, btd)
    latest_ckan = max((item.mes for item in records), default=None)
    latest_btd = max((item.mes for item in btd), default=None)
    latest = max(
        (value for value in (latest_ckan, latest_btd) if value),
        default=None,
    )
    added = len(merged) > len(records)
    contributed = (
        added
        and latest_btd is not None
        and (latest_ckan is None or latest_btd > latest_ckan)
    )
    if warning:
        return merged, latest, warning, "warning"
    if contributed:
        return merged, latest, f"Complemento BTD: {latest_btd}", "info"
    return merged, latest, None, None


def btd_present(btd_client: BtdClient) -> bool:
    """Return whether a readable BTD cache exists on disk."""
    if btd_client is None:
        return False
    try:
        return btd_client.read_cached() is not None
    except Exception:
        return False


__all__ = [
    "BtdClient",
    "Overlay",
    "btd_present",
    "btd_records",
    "cached_btd",
    "overlay",
    "refresh_btd",
]
