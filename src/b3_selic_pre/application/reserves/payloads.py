"""Payloads estruturados da série e dos indicadores de reservas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any

from b3_selic_pre.application.reserves.series import sort_points
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import (
    ATIVO_RESERVAS,
    FONTE_RESERVAS,
    METODO_RESERVAS,
    UNIDADE_RESERVAS,
    ReservesIndicators,
)

AVISO_REGIME = (
    "Sinal direcional; não é recomendação de investimento."
)


def quote_payload(quote: MarketQuote) -> dict[str, object]:
    """Serialize one reserves point with its provenance."""
    return {
        "data": quote.data,
        "ativo": quote.ativo,
        "valor": quote.valor,
        "unidade": quote.unidade,
        "origem": quote.origem,
        "metodo": quote.metodo,
        "extraido_em": quote.extraido_em,
        "defasado": quote.defasado,
        "defasagem_horas": quote.defasagem_horas,
    }


def series_payload(
    points: Sequence[MarketQuote],
    janela: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Serialize the reserves series, preserving the raw US$ million value."""
    ordered = sort_points(points)
    window = dict(janela or {})
    if not window and ordered:
        window = {"inicio": ordered[0].data, "fim": ordered[-1].data}
    latest = ordered[-1] if ordered else None
    return {
        "ativo": ATIVO_RESERVAS,
        "unidade": UNIDADE_RESERVAS,
        "origem": FONTE_RESERVAS,
        "metodo": METODO_RESERVAS,
        "extraido_em": latest.extraido_em if latest else "",
        "janela": window,
        "itens": [quote_payload(point) for point in ordered],
    }


def indicators_payload(
    indicators: ReservesIndicators,
) -> dict[str, object]:
    """Serialize only the metrics and thresholds that were computed."""
    payload: dict[str, object] = {"unidade": indicators.unidade}
    for name in (
        "nivel_atual",
        "var_1m",
        "var_3m",
        "var_12m",
        "tendencia_90d",
        "drawdown_12m",
        "posicao_faixa_12m",
        "media_90d",
        "max_12m",
        "min_12m",
    ):
        value = getattr(indicators, name)
        if value is not None:
            payload[name] = value
    if indicators.regime is not None:
        payload["regime"] = indicators.regime.value
        payload["aviso"] = AVISO_REGIME
    if indicators.thresholds is not None:
        payload["limiares"] = indicators.thresholds.as_dict()
    if indicators.referencia is not None:
        payload["data_referencia"] = indicators.referencia
    return payload


def reserves_payload(
    points: Sequence[MarketQuote],
    indicators: ReservesIndicators,
    janela: Mapping[str, str],
    origem: str,
    gerado_em: str,
    latest_data_date: str | None = None,
) -> dict[str, Any]:
    """Build the complete payload shared by GUI, CLI and MCP."""
    ordered = sort_points(points)
    serie = series_payload(ordered, janela)
    latest = latest_data_date or (
        ordered[-1].data if ordered else None
    )
    return {
        "janela": dict(janela),
        "serie": serie,
        "series": {ATIVO_RESERVAS: serie},
        "indicadores": indicators_payload(indicators),
        "regime": (
            indicators.regime.value
            if indicators.regime is not None
            else None
        ),
        "limiares": (
            indicators.thresholds.as_dict()
            if indicators.thresholds is not None
            else {}
        ),
        "origem": origem,
        "gerado_em": gerado_em,
        "latest_data_date": latest,
        "aviso": AVISO_REGIME,
    }


def empty_payload(janela: Mapping[str, str]) -> dict[str, Any]:
    """Build the empty state that guides the user to update the cache."""
    return {
        "janela": dict(janela),
        "serie": series_payload([], janela),
        "series": {ATIVO_RESERVAS: series_payload([], janela)},
        "indicadores": {},
        "regime": None,
        "limiares": {},
        "origem": "Cache",
        "gerado_em": "",
        "latest_data_date": None,
        "aviso": AVISO_REGIME,
    }


def _items(serie: object) -> list[dict[str, object]]:
    items = serie.get("itens") if isinstance(serie, dict) else None
    return [
        item for item in (items if isinstance(items, list) else [])
        if isinstance(item, dict)
    ]


def _in_window(
    item: dict[str, object], inicio: str | None, fim: str | None
) -> bool:
    day = str(item.get("data"))
    if inicio is not None and day < inicio:
        return False
    return not (fim is not None and day > fim)


def _window(
    payload: Mapping[str, object],
    items: list[dict[str, object]],
    inicio: str | None,
    fim: str | None,
) -> dict[str, str]:
    window = dict(payload.get("janela") or {})
    window["inicio"] = inicio or str(items[0].get("data"))
    window["fim"] = fim or str(items[-1].get("data"))
    return window


def _filtered_serie(
    serie: object, items: list[dict[str, object]], window: dict[str, str]
) -> dict[str, object]:
    if isinstance(serie, dict):
        return {**serie, "itens": items, "janela": window}
    return series_payload([], window)


def filter_payload_window(
    payload: Mapping[str, object],
    inicio: str | None = None,
    fim: str | None = None,
) -> dict[str, Any] | None:
    """Filter the serialized series by an inclusive date window."""
    serie = payload.get("serie")
    items = [
        item for item in _items(serie) if _in_window(item, inicio, fim)
    ]
    if not items:
        return None
    window = _window(payload, items, inicio, fim)
    filtered_serie = _filtered_serie(serie, items, window)
    return {
        **payload,
        "janela": window,
        "serie": filtered_serie,
        "series": {ATIVO_RESERVAS: filtered_serie},
    }


def missing_dates(
    payload: Mapping[str, object], inicio: str, fim: str
) -> list[str]:
    """List business days without data between two ISO dates."""
    present = {str(item.get("data")) for item in _items(payload.get("serie"))}
    try:
        current = date.fromisoformat(inicio)
        end = date.fromisoformat(fim)
    except (TypeError, ValueError):
        return []
    missing: list[str] = []
    while current <= end:
        if current.weekday() < 5 and current.isoformat() not in present:
            missing.append(current.isoformat())
        current += timedelta(days=1)
    return missing


__all__ = [
    "AVISO_REGIME",
    "empty_payload",
    "filter_payload_window",
    "indicators_payload",
    "missing_dates",
    "quote_payload",
    "reserves_payload",
    "series_payload",
]
