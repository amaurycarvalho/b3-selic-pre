"""Formatação CSV e payloads JSON das vendas do Tesouro Direto."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from b3_selic_pre.application.tesouro._processamento import VendaAgregada
from b3_selic_pre.domain.models import VendaTesouroDireto

_SALES_HEADER = [
    "TIPO_TITULO",
    "VENCIMENTO",
    "DATA_LIQUIDACAO",
    "PU",
    "QUANTIDADE",
    "VALOR",
]
_AGGREGATE_HEADER = ["TIPO_TITULO", "QUANTIDADE", "VALOR", "PU_MEDIO"]
_PU_PLACES = 6
_VALUE_PLACES = 2
TESOURO_FONTE = "Tesouro Transparente"
TESOURO_DATASET = "vendas-do-tesouro-direto"


def _decimal(value: Decimal, places: int) -> str:
    return f"{value:.{places}f}"


def format_vendas_csv(sales: list[VendaTesouroDireto]) -> str:
    """Format sales as the approved semicolon CSV."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(_SALES_HEADER)
    for sale in sales:
        writer.writerow([
            sale.tipo_titulo,
            sale.vencimento,
            sale.data_liquidacao,
            _decimal(sale.pu, _PU_PLACES),
            _decimal(sale.quantidade, _VALUE_PLACES),
            _decimal(sale.valor, _VALUE_PLACES),
        ])
    return output.getvalue()


def format_agregados_csv(aggregates: list[VendaAgregada]) -> str:
    """Format aggregated sales as the approved semicolon CSV."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(_AGGREGATE_HEADER)
    for item in aggregates:
        writer.writerow([
            item.tipo_titulo,
            _decimal(item.quantidade, _VALUE_PLACES),
            _decimal(item.valor, _VALUE_PLACES),
            _decimal(item.pu_medio, _PU_PLACES),
        ])
    return output.getvalue()


def sale_item(sale: VendaTesouroDireto) -> dict[str, str]:
    """Convert one sale to a JSON-safe item with string decimals."""
    return {
        "tipo_titulo": sale.tipo_titulo,
        "vencimento": sale.vencimento,
        "data_liquidacao": sale.data_liquidacao,
        "pu": _decimal(sale.pu, _PU_PLACES),
        "quantidade": _decimal(sale.quantidade, _VALUE_PLACES),
        "valor": _decimal(sale.valor, _VALUE_PLACES),
    }


def aggregate_item(item: VendaAgregada) -> dict[str, str]:
    """Convert one aggregate to a JSON-safe item with string decimals."""
    return {
        "tipo_titulo": item.tipo_titulo,
        "quantidade": _decimal(item.quantidade, _VALUE_PLACES),
        "valor": _decimal(item.valor, _VALUE_PLACES),
        "pu_medio": _decimal(item.pu_medio, _PU_PLACES),
    }


def _base_payload(
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    *,
    dataset: str,
    origem: str,
    include_fonte: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "origem": origem,
        "dataset": dataset,
        "resource_id": metadata.get("resource_id"),
        "data_extracao": metadata.get("checked_at")
        or metadata.get("downloaded_at"),
        "publicado_em": metadata.get("last_modified"),
        "data_maxima_liquidacao": metadata.get("last_data_date"),
        "periodo": periodo,
    }
    if include_fonte:
        payload["fonte"] = TESOURO_FONTE
    return payload


def build_vendas_payload(
    sales: list[VendaTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    *,
    dataset: str = TESOURO_DATASET,
    origem: str = "cache",
    include_fonte: bool = True,
) -> dict[str, object]:
    """Build the structured sales payload."""
    payload = _base_payload(
        metadata,
        periodo,
        dataset=dataset,
        origem=origem,
        include_fonte=include_fonte,
    )
    payload["total_registros"] = len(sales)
    payload["registros"] = [sale_item(sale) for sale in sales]
    return payload


def build_agregados_payload(
    aggregates: list[VendaAgregada],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    total_registros: int,
    *,
    dataset: str = TESOURO_DATASET,
    origem: str = "cache",
    include_fonte: bool = True,
) -> dict[str, object]:
    """Build the structured aggregated payload."""
    payload = _base_payload(
        metadata,
        periodo,
        dataset=dataset,
        origem=origem,
        include_fonte=include_fonte,
    )
    payload["total_registros"] = total_registros
    payload["total_agregados"] = len(aggregates)
    payload["agregados"] = [aggregate_item(item) for item in aggregates]
    return payload
