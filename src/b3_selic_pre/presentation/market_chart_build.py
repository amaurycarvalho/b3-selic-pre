"""Construção dos dados de gráfico de câmbio e ouro."""

from __future__ import annotations

from typing import Any

from b3_selic_pre.presentation.market_chart_types import (
    ASSET_LABELS,
    FIBONACCI_LEVELS,
    ChartBand,
    ChartPanelData,
    MarketChartData,
)
from b3_selic_pre.presentation.market_view_model import (
    EMPTY_MESSAGE,
    MarketOptions,
)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items(payload: dict[str, Any], ativo: str) -> list[dict[str, Any]]:
    series = _as_dict(_as_dict(payload.get("series")).get(ativo))
    items = series.get("itens")
    return [_as_dict(item) for item in (items if isinstance(items, list) else [])]


def _forecast(
    payload: dict[str, Any], ativo: str
) -> list[dict[str, Any]]:
    previsao = _as_dict(_as_dict(payload.get("previsao")).get(ativo))
    items = previsao.get("itens")
    return [_as_dict(item) for item in (items if isinstance(items, list) else [])]


def _fibonacci(
    minimos: tuple[float, ...], maximos: tuple[float, ...]
) -> dict[float, float] | None:
    if not minimos or not maximos:
        return None
    low = min(minimos)
    high = max(maximos)
    if high <= low:
        return None
    return {
        level: high - (high - low) * level / 100
        for level in FIBONACCI_LEVELS
    }


def _bands(
    forecast: list[dict[str, Any]],
) -> tuple[ChartBand, ...]:
    levels: dict[int, list[tuple[float, float]]] = {}
    for item in forecast:
        for band in item.get("bandas", []) or []:
            data = _as_dict(band)
            level = data.get("nivel")
            if not isinstance(level, int):
                continue
            levels.setdefault(level, []).append(
                (
                    float(data["inferior"]),
                    float(data["superior"]),
                )
            )
    return tuple(
        ChartBand(
            nivel=level,
            inferiores=tuple(pair[0] for pair in pairs),
            superiores=tuple(pair[1] for pair in pairs),
        )
        for level, pairs in sorted(levels.items())
    )


def _history_arrays(
    items: list[dict[str, Any]],
) -> tuple[
    tuple[str, ...], tuple[float, ...], tuple[float, ...], tuple[float, ...]
]:
    datas = tuple(str(item.get("data", "")) for item in items)
    valores = tuple(float(item.get("valor", 0.0)) for item in items)
    minimos = tuple(
        float(item.get("minimo", item.get("valor", 0.0)))
        for item in items
    )
    maximos = tuple(
        float(item.get("maximo", item.get("valor", 0.0)))
        for item in items
    )
    return datas, valores, minimos, maximos


def _forecast_arrays(
    payload: dict[str, Any], ativo: str
) -> tuple[tuple[str, ...], tuple[float, ...], tuple[ChartBand, ...]]:
    forecast = _forecast(payload, ativo)
    datas = tuple(str(item.get("data", "")) for item in forecast)
    centro = tuple(float(item.get("centro", 0.0)) for item in forecast)
    return datas, centro, _bands(forecast)


def _rescale_bands(
    bands: tuple[ChartBand, ...], factor: float
) -> tuple[ChartBand, ...]:
    return tuple(
        ChartBand(
            band.nivel,
            tuple(value * factor for value in band.inferiores),
            tuple(value * factor for value in band.superiores),
        )
        for band in bands
    )


def _base100_factor(valores: tuple[float, ...]) -> float:
    if not valores or valores[0] == 0:
        return 1.0
    return 100.0 / valores[0]


def _scale(
    valores: tuple[float, ...], minimos: tuple[float, ...],
    maximos: tuple[float, ...], centro: tuple[float, ...],
    bands: tuple[ChartBand, ...], factor: float,
) -> tuple[
    tuple[float, ...], tuple[float, ...], tuple[float, ...],
    tuple[float, ...], tuple[ChartBand, ...],
]:
    return (
        tuple(value * factor for value in valores),
        tuple(value * factor for value in minimos),
        tuple(value * factor for value in maximos),
        tuple(value * factor for value in centro),
        _rescale_bands(bands, factor),
    )


def _panel(
    payload: dict[str, Any],
    ativo: str,
    options: MarketOptions,
) -> ChartPanelData | None:
    items = _items(payload, ativo)
    if not items:
        return None
    datas, valores, minimos, maximos = _history_arrays(items)
    previsao_datas, previsao_centro, bands = _forecast_arrays(payload, ativo)
    factor = _base100_factor(valores) if options.base100 else 1.0
    if factor != 1.0:
        valores, minimos, maximos, previsao_centro, bands = _scale(
            valores, minimos, maximos, previsao_centro, bands, factor
        )
    series = _as_dict(_as_dict(payload.get("series")).get(ativo))
    return ChartPanelData(
        ativo=ativo,
        label=ASSET_LABELS[ativo],
        unidade=str(series.get("unidade", "")),
        datas=datas,
        valores=valores,
        minimos=minimos,
        maximos=maximos,
        previsao_datas=previsao_datas,
        previsao_centro=previsao_centro,
        bandas=bands,
        fibonacci=_fibonacci(minimos, maximos) if options.fibonacci else None,
    )


def _format_number(value: object, suffix: str = "") -> str:
    if not isinstance(value, (int, float)):
        return "-"
    return f"{value:.2f}{suffix}"


def indicators_text(payload: dict[str, Any]) -> str:
    """Render the policy signals as a compact one-line summary."""
    indicators = _as_dict(payload.get("indicadores"))
    parts = [
        f"Prêmio a termo: {_format_number(indicators.get('premio_termo'), '%')}",
        f"Prêmio DOL: {_format_number(indicators.get('premio_dol'), '%')}",
        f"Gap Focus: {_format_number(indicators.get('gap_focus'))}",
        f"Vol 30d: {_format_number(indicators.get('vol30'), '%')}",
        f"Vol 90d: {_format_number(indicators.get('vol90'), '%')}",
    ]
    regime = indicators.get("regime")
    parts.append(
        "Regime: "
        + ("ligado" if regime is True else "desligado" if regime is False else "-")
    )
    threshold = indicators.get("limiar_regime")
    if isinstance(threshold, (int, float)):
        parts.append(f"Limiar: {threshold:.2f}")
    return " • ".join(parts)


def build_chart_data(
    payload: dict[str, Any], options: MarketOptions | None = None
) -> MarketChartData:
    """Build stacked chart panels, base-100 values and Fibonacci levels."""
    options = options or MarketOptions()
    assets = (
        ("usd", "ouro") if options.ativo == "ambos" else (options.ativo,)
    )
    panels = tuple(
        panel
        for panel in (_panel(payload, ativo, options) for ativo in assets)
        if panel is not None
    )
    window = _as_dict(payload.get("janela"))
    today = str(window.get("fim", ""))
    if not panels:
        return MarketChartData(
            paineis=(),
            hoje=today,
            base100=options.base100,
            indicadores_texto=indicators_text(payload),
            vazio=True,
            mensagem=EMPTY_MESSAGE,
        )
    return MarketChartData(
        paineis=panels,
        hoje=today,
        base100=options.base100,
        indicadores_texto=indicators_text(payload),
    )


__all__ = [
    "ASSET_LABELS",
    "FIBONACCI_LEVELS",
    "ChartBand",
    "ChartPanelData",
    "MarketChartData",
    "build_chart_data",
    "indicators_text",
]
