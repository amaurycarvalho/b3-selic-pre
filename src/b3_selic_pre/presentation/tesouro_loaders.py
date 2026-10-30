"""Loaders de cache e atualização da aba Tesouro Direto."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from b3_selic_pre.presentation.tesouro_analise_data import AnaliseData
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
)
from b3_selic_pre.presentation.tesouro_loader_support import (
    metadata_date,
    metadata_time,
)
from b3_selic_pre.presentation.tesouro_overlay import (
    BtdClient,
    btd_present,
    cached_btd,
    overlay,
)
from b3_selic_pre.presentation.tesouro_refresh import refresh_data
from b3_selic_pre.presentation.tesouro_series_loader import (
    SeriesCache,
    series_data,
)

Client = Any
Loader = Any
StageCallback = Callable[[str], None]


def _stock_cache_data(
    client: Client, btd_client: BtdClient
) -> AnaliseData | None:
    stock = client.read_cached_estoque()
    btd, warning = cached_btd(btd_client)
    if stock is None and not btd:
        return None
    records, metadata = (
        (stock[0], stock[1]) if stock is not None else ((), {})
    )
    merged, latest, note, kind = overlay(records, btd, warning)
    return AnaliseData(
        estoque=merged,
        latest_data_date=latest or metadata_date(metadata),
        source="Cache",
        extracted_at=metadata_time(metadata),
        btd_note=note,
        btd_status_kind=kind,
    )


def _appetite_cache_data(client: Client) -> AnaliseData | None:
    sales = client.read_cached_vendas()
    if sales is None:
        return None
    sales_records, sales_meta, _origin = sales
    redemptions = client.read_cached_resgates()
    return AnaliseData(
        vendas=tuple(sales_records),
        resgates=tuple(redemptions[0] if redemptions else ()),
        latest_data_date=metadata_date(sales_meta),
        source="Cache",
        extracted_at=metadata_time(sales_meta),
    )


def _general_cache_data(
    client: Client, btd_client: BtdClient
) -> AnaliseData | None:
    stock = client.read_cached_estoque()
    sales = client.read_cached_vendas()
    if sales is None:
        return None
    sales_records, sales_meta, _origin = sales
    btd, warning = cached_btd(btd_client)
    if stock is None and not btd:
        return None
    stock_records, stock_meta = (
        (stock[0], stock[1]) if stock is not None else ((), {})
    )
    merged, latest, note, note_kind = overlay(stock_records, btd, warning)
    return AnaliseData(
        vendas=tuple(sales_records),
        estoque=merged,
        latest_data_date=(
            latest or metadata_date(stock_meta) or metadata_date(sales_meta)
        ),
        source="Cache",
        extracted_at=(
            metadata_time(stock_meta) or metadata_time(sales_meta)
        ),
        btd_note=note,
        btd_status_kind=note_kind,
    )


def _cache_data(
    client: Client, kind: str, btd_client: BtdClient = None
) -> AnaliseData | None:
    if kind == KIND_ESTOQUE:
        return _stock_cache_data(client, btd_client)
    if kind == KIND_APETITE:
        return _appetite_cache_data(client)
    return _general_cache_data(client, btd_client)


def _has(client: Client, name: str) -> bool:
    checker = getattr(client, name, None)
    return bool(checker()) if callable(checker) else False


def cache_available(
    client: Client, kind: str, btd_client: BtdClient = None
) -> bool:
    """Return whether the cache needed by a sub-tab exists on disk."""
    if client is None:
        return False
    if kind == KIND_ESTOQUE:
        return _has(client, "has_cached_estoque") or btd_present(btd_client)
    if kind == KIND_APETITE:
        return _has(client, "has_cached_vendas")
    return (
        _has(client, "has_cached_estoque") or btd_present(btd_client)
    ) and _has(client, "has_cached_vendas")


def make_loader(
    client: Client,
    kind: str,
    series_cache: SeriesCache | None = None,
    precompute: Callable[[str, AnaliseData], None] | None = None,
    btd_client: BtdClient = None,
) -> Loader:
    """Create a cache/refresh loader for a sub-tab kind."""

    def loader(
        cache_only: bool,
        force: bool,
        stage_callback: StageCallback | None = None,
    ) -> AnaliseData | None:
        if client is None:
            raise RuntimeError("Cliente do Tesouro não configurado.")
        if cache_only:
            data = series_data(series_cache, kind)
            if data is not None:
                return data
            data = _cache_data(client, kind, btd_client)
            if data is not None and precompute is not None:
                precompute(kind, data)
            return data
        return refresh_data(
            client, kind, force, stage_callback, btd_client
        )

    return loader
