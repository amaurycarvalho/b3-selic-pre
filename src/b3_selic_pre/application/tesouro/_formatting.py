"""Formatação CSV e payloads JSON das vendas do Tesouro Direto."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from b3_selic_pre.application.tesouro._processamento import VendaAgregada
from b3_selic_pre.application.tesouro._processamento_estoque import (
    EstoqueAgregado,
)
from b3_selic_pre.application.tesouro._processamento_resgates import (
    ResgateAgregado,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)

_SALES_HEADER = [
    "TIPO_TITULO",
    "VENCIMENTO",
    "DATA_LIQUIDACAO",
    "PU",
    "QUANTIDADE",
    "VALOR",
]
_AGGREGATE_HEADER = ["TIPO_TITULO", "QUANTIDADE", "VALOR", "PU_MEDIO"]
_RESGATES_HEADER = [
    "TIPO_RESGATE",
    "TIPO_TITULO",
    "VENCIMENTO",
    "DATA_RESGATE",
    "PU",
    "QUANTIDADE",
    "VALOR",
]
_RESGATES_AGGREGATE_HEADER = [
    "TIPO_RESGATE",
    "TIPO_TITULO",
    "QUANTIDADE",
    "VALOR",
    "PU_MEDIO",
]
_ESTOQUE_HEADER = [
    "TIPO_TITULO",
    "VENCIMENTO",
    "MES",
    "PU",
    "QUANTIDADE",
    "VALOR_ESTOQUE",
]
_ESTOQUE_AGGREGATE_HEADER = [
    "TIPO_TITULO",
    "QUANTIDADE",
    "VALOR_ESTOQUE",
    "PU_MEDIO",
]
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
    date_field: str = "data_maxima_liquidacao",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "origem": origem,
        "dataset": dataset,
        "resource_id": metadata.get("resource_id"),
        "data_extracao": metadata.get("checked_at")
        or metadata.get("downloaded_at"),
        "publicado_em": metadata.get("last_modified"),
        date_field: metadata.get("last_data_date"),
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


def _optional_pu(value: Decimal | None) -> str:
    return "" if value is None else _decimal(value, _PU_PLACES)


def _write_csv(header: list[str], rows: list[list[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()


def format_resgates_csv(records: list[ResgateTesouroDireto]) -> str:
    """Format redemptions as the approved semicolon CSV."""
    rows = [
        [
            item.tipo_resgate,
            item.tipo_titulo,
            item.vencimento,
            item.data_resgate,
            _optional_pu(item.pu),
            _decimal(item.quantidade, _VALUE_PLACES),
            _decimal(item.valor, _VALUE_PLACES),
        ]
        for item in records
    ]
    return _write_csv(_RESGATES_HEADER, rows)


def format_resgates_agregados_csv(
    aggregates: list[ResgateAgregado],
) -> str:
    """Format aggregated redemptions as the approved semicolon CSV."""
    rows = [
        [
            item.tipo_resgate,
            item.tipo_titulo,
            _decimal(item.quantidade, _VALUE_PLACES),
            _decimal(item.valor, _VALUE_PLACES),
            _optional_pu(item.pu_medio),
        ]
        for item in aggregates
    ]
    return _write_csv(_RESGATES_AGGREGATE_HEADER, rows)


def format_estoque_csv(records: list[EstoqueTesouroDireto]) -> str:
    """Format monthly stock as the approved semicolon CSV."""
    rows = [
        [
            item.tipo_titulo,
            item.vencimento,
            item.mes,
            _decimal(item.pu, _PU_PLACES),
            _decimal(item.quantidade, _VALUE_PLACES),
            _decimal(item.valor_estoque, _VALUE_PLACES),
        ]
        for item in records
    ]
    return _write_csv(_ESTOQUE_HEADER, rows)


def format_estoque_agregados_csv(
    aggregates: list[EstoqueAgregado],
) -> str:
    """Format aggregated stock as the approved semicolon CSV."""
    rows = [
        [
            item.tipo_titulo,
            _decimal(item.quantidade, _VALUE_PLACES),
            _decimal(item.valor_estoque, _VALUE_PLACES),
            _decimal(item.pu_medio, _PU_PLACES),
        ]
        for item in aggregates
    ]
    return _write_csv(_ESTOQUE_AGGREGATE_HEADER, rows)


def resgate_item(item: ResgateTesouroDireto) -> dict[str, str | None]:
    """Convert one redemption to a JSON-safe item."""
    return {
        "tipo_resgate": item.tipo_resgate,
        "tipo_titulo": item.tipo_titulo,
        "vencimento": item.vencimento,
        "data_resgate": item.data_resgate,
        "pu": _optional_pu(item.pu) or None,
        "quantidade": _decimal(item.quantidade, _VALUE_PLACES),
        "valor": _decimal(item.valor, _VALUE_PLACES),
    }


def resgate_agregado_item(
    item: ResgateAgregado,
) -> dict[str, str]:
    """Convert one redemption aggregate to a JSON-safe item."""
    return {
        "tipo_resgate": item.tipo_resgate,
        "tipo_titulo": item.tipo_titulo,
        "quantidade": _decimal(item.quantidade, _VALUE_PLACES),
        "valor": _decimal(item.valor, _VALUE_PLACES),
        "pu_medio": _optional_pu(item.pu_medio),
    }


def estoque_item(item: EstoqueTesouroDireto) -> dict[str, str]:
    """Convert one stock snapshot to a JSON-safe item."""
    return {
        "tipo_titulo": item.tipo_titulo,
        "vencimento": item.vencimento,
        "mes": item.mes,
        "pu": _decimal(item.pu, _PU_PLACES),
        "quantidade": _decimal(item.quantidade, _VALUE_PLACES),
        "valor_estoque": _decimal(item.valor_estoque, _VALUE_PLACES),
    }


def estoque_agregado_item(item: EstoqueAgregado) -> dict[str, str]:
    """Convert one stock aggregate to a JSON-safe item."""
    return {
        "tipo_titulo": item.tipo_titulo,
        "quantidade": _decimal(item.quantidade, _VALUE_PLACES),
        "valor_estoque": _decimal(item.valor_estoque, _VALUE_PLACES),
        "pu_medio": _decimal(item.pu_medio, _PU_PLACES),
    }


def build_resgates_payload(
    records: list[ResgateTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    *,
    origem: str = "cache",
    include_fonte: bool = True,
) -> dict[str, object]:
    """Build the structured redemptions payload."""
    payload = _base_payload(
        metadata,
        periodo,
        dataset="resgates",
        origem=origem,
        include_fonte=include_fonte,
        date_field="data_maxima_resgate",
    )
    payload["total_registros"] = len(records)
    payload["registros"] = [resgate_item(item) for item in records]
    return payload


def build_resgates_agregados_payload(
    aggregates: list[ResgateAgregado],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    total_registros: int,
    *,
    origem: str = "cache",
    include_fonte: bool = True,
) -> dict[str, object]:
    """Build the structured aggregated redemptions payload."""
    payload = _base_payload(
        metadata,
        periodo,
        dataset="resgates",
        origem=origem,
        include_fonte=include_fonte,
        date_field="data_maxima_resgate",
    )
    payload["total_registros"] = total_registros
    payload["total_agregados"] = len(aggregates)
    payload["agregados"] = [resgate_agregado_item(item) for item in aggregates]
    return payload


def build_estoque_payload(
    records: list[EstoqueTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    *,
    origem: str = "cache",
    include_fonte: bool = True,
) -> dict[str, object]:
    """Build the structured stock payload."""
    payload = _base_payload(
        metadata,
        periodo,
        dataset="estoque",
        origem=origem,
        include_fonte=include_fonte,
        date_field="ultimo_mes",
    )
    payload["total_registros"] = len(records)
    payload["registros"] = [estoque_item(item) for item in records]
    return payload


def build_estoque_agregados_payload(
    aggregates: list[EstoqueAgregado],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
    total_registros: int,
    *,
    origem: str = "cache",
    include_fonte: bool = True,
) -> dict[str, object]:
    """Build the structured aggregated stock payload."""
    payload = _base_payload(
        metadata,
        periodo,
        dataset="estoque",
        origem=origem,
        include_fonte=include_fonte,
        date_field="ultimo_mes",
    )
    payload["total_registros"] = total_registros
    payload["total_agregados"] = len(aggregates)
    payload["agregados"] = [estoque_agregado_item(item) for item in aggregates]
    return payload
