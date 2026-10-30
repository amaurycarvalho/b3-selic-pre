"""Payloads estruturados de histórico, cenário e indicadores de mercado."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.application.market.forecast import (
    FocusExpectation,
    ForecastOutcome,
    forecast_usd,
    statistical_forecast,
)
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    ForecastPoint,
    MarketQuote,
    MarketSeries,
    PolicyIndicators,
    Resolution,
)

AVISO_CENARIO = (
    "Cenário ou projeção estatística; não é recomendação de investimento."
)


def quote_payload(quote: MarketQuote) -> dict[str, object]:
    """Serialize one quote with provenance and staleness."""
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


def series_payload(series: MarketSeries) -> dict[str, object]:
    """Serialize a series and its items."""
    return {
        "ativo": series.ativo,
        "unidade": series.unidade,
        "resolucao": str(series.resolucao),
        "origem": series.origem,
        "metodo": series.metodo,
        "extraido_em": series.extraido_em,
        "defasado": series.defasada,
        "itens": [quote_payload(point) for point in series.pontos],
    }


def forecast_point_payload(point: ForecastPoint) -> dict[str, object]:
    """Serialize one forecast point with its bands."""
    return {
        "data": point.data,
        "ativo": point.ativo,
        "cenario": point.cenario,
        "metodo": point.metodo,
        "centro": point.centro,
        "bandas": [
            {
                "nivel": band.nivel,
                "inferior": band.inferior,
                "superior": band.superior,
            }
            for band in point.bandas
        ],
    }


def forecast_payload(
    ativo: str, outcome: ForecastOutcome
) -> dict[str, object]:
    """Serialize a forecast outcome, including the non-recommendation label."""
    payload: dict[str, object] = {
        "ativo": ativo,
        "disponivel": outcome.disponivel,
        "aviso": AVISO_CENARIO,
        "itens": [
            forecast_point_payload(point) for point in outcome.pontos
        ],
    }
    if outcome.motivo is not None:
        payload["motivo"] = outcome.motivo
    if outcome.pontos:
        payload["cenario"] = outcome.pontos[0].cenario
        payload["metodo"] = outcome.pontos[0].metodo
    return payload


def indicators_payload(
    indicators: PolicyIndicators,
) -> dict[str, object]:
    """Serialize only the signals that were computed."""
    payload: dict[str, object] = {"aviso": AVISO_CENARIO}
    for name in (
        "premio_termo",
        "premio_dol",
        "gap_focus",
        "vol30",
        "vol90",
        "regime",
    ):
        value = getattr(indicators, name)
        if value is not None:
            payload[name] = value
    if indicators.limiar_regime is not None:
        payload["limiar_regime"] = indicators.limiar_regime
    if indicators.referencia is not None:
        payload["data_referencia"] = indicators.referencia
    return payload


def build_forecasts(
    usd_spot: MarketQuote | None,
    usd_history: Sequence[MarketQuote],
    gold_history: Sequence[MarketQuote],
    focus: Sequence[FocusExpectation],
    reference: date,
    config: MarketConfig,
) -> dict[str, ForecastOutcome]:
    """Build both forecast tracks, falling back to statistics without Focus."""
    outcomes: dict[str, ForecastOutcome] = {}
    if usd_spot is not None and focus:
        market = forecast_usd(usd_spot, focus, reference, config)
    else:
        market = ForecastOutcome(motivo="focus_ausente")
    if not market.disponivel:
        market = statistical_forecast(
            ATIVO_USD, usd_history, reference, config
        )
    outcomes[ATIVO_USD] = market
    outcomes[ATIVO_OURO] = statistical_forecast(
        ATIVO_OURO, gold_history, reference, config
    )
    return outcomes


def market_payload(
    janela: Mapping[str, str],
    series: Mapping[str, MarketSeries],
    forecasts: Mapping[str, ForecastOutcome],
    indicators: PolicyIndicators,
    origem: str,
    gerado_em: str,
) -> dict[str, object]:
    """Build the complete JSON payload shared by CLI and MCP."""
    return {
        "janela": dict(janela),
        "series": {
            ativo: series_payload(value)
            for ativo, value in series.items()
        },
        "previsao": {
            ativo: forecast_payload(ativo, outcome)
            for ativo, outcome in forecasts.items()
        },
        "indicadores": indicators_payload(indicators),
        "origem": origem,
        "gerado_em": gerado_em,
        "aviso": AVISO_CENARIO,
    }


def _market_assets(ativo: str) -> tuple[str, ...]:
    return ("usd", "ouro") if ativo == "ambos" else (ativo,)


def _item_in_window(
    item: object, inicio: str | None, fim: str | None
) -> bool:
    if not isinstance(item, dict):
        return False
    if inicio is not None and str(item.get("data")) < inicio:
        return False
    return not (fim is not None and str(item.get("data")) > fim)


def _series_items(
    data: dict[str, object], inicio: str | None, fim: str | None
) -> list[dict[str, object]]:
    raw = data.get("itens", []) or []
    return [
        item for item in raw if _item_in_window(item, inicio, fim)
    ]


def _filter_series(
    series: object,
    assets: tuple[str, ...],
    inicio: str | None,
    fim: str | None,
) -> dict[str, object]:
    filtered: dict[str, object] = {}
    source = series if isinstance(series, dict) else {}
    for asset in assets:
        data = source.get(asset)
        if not isinstance(data, dict):
            continue
        items = _series_items(data, inicio, fim)
        if items:
            filtered[asset] = {**data, "itens": items}
    return filtered


def _filter_forecast(
    previsao: object, assets: tuple[str, ...]
) -> dict[str, object]:
    source = previsao if isinstance(previsao, dict) else {}
    return {
        asset: source[asset] for asset in assets if asset in source
    }


def _filtered_window(
    payload: Mapping[str, object],
    inicio: str | None,
    fim: str | None,
) -> dict[str, object]:
    janela = dict(payload.get("janela") or {})
    if inicio is not None:
        janela["inicio"] = inicio
    if fim is not None:
        janela["fim"] = fim
    return janela


def filter_payload_window(
    payload: Mapping[str, object],
    ativo: str,
    inicio: str | None,
    fim: str | None,
) -> dict[str, object] | None:
    """Filter assets and dates from a serialized market payload."""
    assets = _market_assets(ativo)
    filtered_series = _filter_series(
        payload.get("series"), assets, inicio, fim
    )
    if not filtered_series:
        return None
    return {
        **payload,
        "janela": _filtered_window(payload, inicio, fim),
        "series": filtered_series,
        "previsao": _filter_forecast(payload.get("previsao"), assets),
    }


def resolution_name(resolution: Resolution | str) -> str:
    """Return the serialized resolution name."""
    return resolution.value if isinstance(resolution, Resolution) else resolution


__all__ = [
    "ATIVO_OURO",
    "ATIVO_USD",
    "AVISO_CENARIO",
    "build_forecasts",
    "forecast_payload",
    "forecast_point_payload",
    "indicators_payload",
    "market_payload",
    "quote_payload",
    "resolution_name",
    "series_payload",
]
