"""Loaders de cache e atualização da aba Tesouro Direto."""

from __future__ import annotations

from typing import Any

from b3_selic_pre.presentation.tesouro_analise_controller import AnaliseData
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
)

Client = Any
Loader = Any


def _metadata_time(metadata: dict[str, object]) -> str | None:
    for key in ("checked_at", "downloaded_at"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _metadata_date(metadata: dict[str, object]) -> str | None:
    value = metadata.get("last_data_date")
    return value if isinstance(value, str) and value else None


def _source(origin: str) -> str:
    return "Cache" if origin == "cache" else "Tesouro Transparente"


def _cache_data(client: Client, kind: str) -> AnaliseData | None:
    if kind == KIND_ESTOQUE:
        stock = client.read_cached_estoque()
        if stock is None:
            return None
        records, metadata, _origin = stock
        return AnaliseData(
            estoque=tuple(records),
            latest_data_date=_metadata_date(metadata),
            source="Cache",
            extracted_at=_metadata_time(metadata),
        )
    if kind == KIND_APETITE:
        sales = client.read_cached_vendas()
        if sales is None:
            return None
        sales_records, sales_meta, _origin = sales
        redemptions = client.read_cached_resgates()
        return AnaliseData(
            vendas=tuple(sales_records),
            resgates=tuple(redemptions[0] if redemptions else ()),
            latest_data_date=_metadata_date(sales_meta),
            source="Cache",
            extracted_at=_metadata_time(sales_meta),
        )
    stock = client.read_cached_estoque()
    if stock is None:
        return None
    sales = client.read_cached_vendas()
    if sales is None:
        return None
    stock_records, stock_meta, _origin = stock
    sales_records, sales_meta, _origin = sales
    metadata = stock_meta or sales_meta
    return AnaliseData(
        vendas=tuple(sales_records),
        estoque=tuple(stock_records),
        latest_data_date=_metadata_date(metadata),
        source="Cache",
        extracted_at=_metadata_time(metadata),
    )


def _refresh_data(client: Client, kind: str, force: bool) -> AnaliseData:
    if kind == KIND_ESTOQUE:
        records, metadata, origin = client.fetch_estoque(force=force)
        return AnaliseData(
            estoque=tuple(records),
            latest_data_date=_metadata_date(metadata),
            source=_source(origin),
            extracted_at=_metadata_time(metadata),
        )
    sales, sales_meta, sales_origin = client.fetch_vendas(force=force)
    if kind == KIND_APETITE:
        try:
            redemptions, _redemption_meta, redemption_origin = (
                client.fetch_resgates(force=force)
            )
        except Exception:
            redemptions, redemption_origin = [], "cache"
        return AnaliseData(
            vendas=tuple(sales),
            resgates=tuple(redemptions),
            latest_data_date=_metadata_date(sales_meta),
            source=(
                "Tesouro Transparente"
                if "cache" not in (sales_origin, redemption_origin)
                else "Cache"
            ),
            extracted_at=_metadata_time(sales_meta),
        )
    stock, stock_meta, stock_origin = client.fetch_estoque(force=force)
    return AnaliseData(
        vendas=tuple(sales),
        estoque=tuple(stock),
        latest_data_date=(
            _metadata_date(stock_meta) or _metadata_date(sales_meta)
        ),
        source=(
            "Tesouro Transparente"
            if sales_origin != "cache" or stock_origin != "cache"
            else "Cache"
        ),
        extracted_at=(
            _metadata_time(stock_meta) or _metadata_time(sales_meta)
        ),
    )


def _has(client: Client, name: str) -> bool:
    checker = getattr(client, name, None)
    return bool(checker()) if callable(checker) else False


def cache_available(client: Client, kind: str) -> bool:
    """Return whether the cache needed by a sub-tab exists on disk."""
    if client is None:
        return False
    if kind == KIND_ESTOQUE:
        return _has(client, "has_cached_estoque")
    if kind == KIND_APETITE:
        return _has(client, "has_cached_vendas")
    return _has(client, "has_cached_estoque") and _has(
        client, "has_cached_vendas"
    )


def make_loader(client: Client, kind: str) -> Loader:
    """Create a cache/refresh loader for a sub-tab kind."""

    def loader(cache_only: bool, force: bool) -> AnaliseData | None:
        if client is None:
            raise RuntimeError("Cliente do Tesouro não configurado.")
        if cache_only:
            return _cache_data(client, kind)
        return _refresh_data(client, kind, force)

    return loader
