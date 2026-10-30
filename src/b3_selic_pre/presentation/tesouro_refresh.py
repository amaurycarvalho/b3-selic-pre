"""Atualização via rede das sub-abas do Tesouro Direto."""

from __future__ import annotations

import logging
from typing import Any

from b3_selic_pre.presentation.logging_utils import log_exception_once
from b3_selic_pre.presentation.tesouro_analise_data import AnaliseData
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
)
from b3_selic_pre.presentation.tesouro_loader_support import (
    emit,
    metadata_date,
    metadata_time,
    source,
)
from b3_selic_pre.presentation.tesouro_overlay import (
    BtdClient,
    cached_btd,
    overlay,
    refresh_btd,
)

Client = Any
StageCallback = Any

logger = logging.getLogger(__name__)


def _refresh_stock(
    client: Client, force: bool, btd_client: BtdClient
) -> AnaliseData:
    records, metadata, origin = client.fetch_estoque(force=force)
    btd, warning = refresh_btd(btd_client, force)
    merged, latest, note, kind = overlay(records, btd, warning)
    return AnaliseData(
        estoque=merged,
        latest_data_date=latest or metadata_date(metadata),
        source=source(origin),
        extracted_at=metadata_time(metadata),
        btd_note=note,
        btd_status_kind=kind,
    )


def _refresh_appetite(
    client: Client, force: bool, stage_callback: StageCallback | None
) -> AnaliseData:
    sales, sales_meta, sales_origin = client.fetch_vendas(force=force)
    emit(stage_callback, "resgates")
    try:
        redemptions, _redemption_meta, redemption_origin = (
            client.fetch_resgates(force=force)
        )
    except Exception as exc:
        log_exception_once(
            logger,
            exc,
            "Falha ao atualizar os resgates do Tesouro Direto",
        )
        redemptions, redemption_origin = [], "cache"
    return AnaliseData(
        vendas=tuple(sales),
        resgates=tuple(redemptions),
        latest_data_date=metadata_date(sales_meta),
        source=(
            "Tesouro Transparente"
            if "cache" not in (sales_origin, redemption_origin)
            else "Cache"
        ),
        extracted_at=metadata_time(sales_meta),
    )


def _refresh_general(
    client: Client,
    force: bool,
    stage_callback: StageCallback | None,
    btd_client: BtdClient,
) -> AnaliseData:
    emit(stage_callback, "vendas")
    sales, sales_meta, sales_origin = client.fetch_vendas(force=force)
    emit(stage_callback, "estoque")
    stock, stock_meta, stock_origin = client.fetch_estoque(force=force)
    btd, warning = cached_btd(btd_client)
    merged, latest, note, kind = overlay(stock, btd, warning)
    return AnaliseData(
        vendas=tuple(sales),
        estoque=merged,
        latest_data_date=(
            latest or metadata_date(stock_meta) or metadata_date(sales_meta)
        ),
        source=(
            "Tesouro Transparente"
            if sales_origin != "cache" or stock_origin != "cache"
            else "Cache"
        ),
        extracted_at=(
            metadata_time(stock_meta) or metadata_time(sales_meta)
        ),
        btd_note=note,
        btd_status_kind=kind,
    )


def refresh_data(
    client: Client,
    kind: str,
    force: bool,
    stage_callback: StageCallback | None = None,
    btd_client: BtdClient = None,
) -> AnaliseData:
    """Refresh one sub-tab, refreshing the BTD only for stock."""
    if kind == KIND_ESTOQUE:
        emit(stage_callback, "estoque")
        return _refresh_stock(client, force, btd_client)
    if kind == KIND_APETITE:
        emit(stage_callback, "vendas")
        return _refresh_appetite(client, force, stage_callback)
    return _refresh_general(client, force, stage_callback, btd_client)


__all__ = ["refresh_data"]
