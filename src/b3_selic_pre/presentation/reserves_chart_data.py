"""Dados de gráfico headless da sub-aba Reservas Internacionais."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from b3_selic_pre.application.reserves.config import meses_janela
from b3_selic_pre.application.reserves.series import shift_months
from b3_selic_pre.presentation.reserves_view_model import (
    EMPTY_MESSAGE,
    REGIME_LABELS,
    STALE_GAP_DAYS,
    ReservesOptions,
    last_business_day,
)

JANELA_LABELS = {"12m": "12 meses", "3a": "3 anos"}


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items(payload: Mapping[str, object]) -> list[dict[str, Any]]:
    serie = _as_dict(payload.get("serie"))
    items = serie.get("itens")
    return [
        _as_dict(item)
        for item in (items if isinstance(items, list) else [])
    ]


def _points(payload: Mapping[str, object]) -> list[tuple[str, float]]:
    points: list[tuple[str, float]] = []
    for item in _items(payload):
        day = item.get("data")
        value = item.get("valor")
        if not isinstance(day, str) or not isinstance(value, (int, float)):
            continue
        points.append((day, float(value)))
    return sorted(points)


def _slice_window(
    points: list[tuple[str, float]], months: int
) -> list[tuple[str, float]]:
    if not points:
        return []
    latest = date.fromisoformat(points[-1][0])
    start = shift_months(latest, -months)
    return [
        point
        for point in points
        if date.fromisoformat(point[0]) >= start
    ]


def moving_average(
    points: list[tuple[str, float]], days: int
) -> tuple[float, ...]:
    """Return a trailing calendar-day moving average in the same order."""
    values: list[float] = []
    for index, (day, _) in enumerate(points):
        current = date.fromisoformat(day)
        window = [
            value
            for other_day, value in points[: index + 1]
            if date.fromisoformat(other_day)
            > current - timedelta(days=days)
        ]
        values.append(sum(window) / len(window) if window else 0.0)
    return tuple(values)


def _extreme(
    points: list[tuple[str, float]], highest: bool
) -> tuple[float | None, str | None]:
    if not points:
        return None, None
    selected = (max if highest else min)(points, key=lambda item: item[1])
    return selected[1], selected[0]


def _is_stale(latest: str | None, reference: date) -> bool:
    if not latest:
        return False
    try:
        parsed = date.fromisoformat(latest)
    except ValueError:
        return False
    return (last_business_day(reference) - parsed).days > STALE_GAP_DAYS


@dataclass(frozen=True)
class ReservesChartData:
    """Chart payload consumed only by the matplotlib renderer."""

    datas: tuple[str, ...] = ()
    valores: tuple[float, ...] = ()
    medias_30: tuple[float, ...] = ()
    medias_90: tuple[float, ...] = ()
    minimo: float | None = None
    maximo: float | None = None
    minimo_data: str | None = None
    maximo_data: str | None = None
    regime: str | None = None
    regime_label: str = ""
    thresholds_text: str = ""
    unidade: str = "US$ bilhões"
    janela: str = "12m"
    latest_data_date: str | None = None
    defasado: bool = False
    vazio: bool = False
    mensagem: str = ""

    @property
    def amplitude(self: ReservesChartData) -> float | None:
        """Return the chart amplitude when both extremes exist."""
        if self.minimo is None or self.maximo is None:
            return None
        return self.maximo - self.minimo


def build_chart_data(
    payload: dict[str, Any],
    options: ReservesOptions | None = None,
    now: datetime | None = None,
) -> ReservesChartData:
    """Build the reserves chart data for the selected window."""
    options = options or ReservesOptions()
    points = _points(payload)
    if not points:
        return ReservesChartData(
            vazio=True,
            mensagem=EMPTY_MESSAGE,
            janela=options.janela,
        )
    windowed = _slice_window(points, meses_janela(options.janela))
    if not windowed:
        return ReservesChartData(
            vazio=True,
            mensagem=EMPTY_MESSAGE,
            janela=options.janela,
        )
    scaled = [(day, value / 1000) for day, value in windowed]
    latest = scaled[-1][0]
    reference = (now or datetime.now()).date()
    regime = payload.get("regime")
    regime_name = regime if isinstance(regime, str) else None
    minimo, minimo_data = _extreme(scaled, False)
    maximo, maximo_data = _extreme(scaled, True)
    return ReservesChartData(
        datas=tuple(day for day, _ in scaled),
        valores=tuple(value for _, value in scaled),
        medias_30=moving_average(scaled, 30),
        medias_90=moving_average(scaled, 90),
        minimo=minimo,
        maximo=maximo,
        minimo_data=minimo_data,
        maximo_data=maximo_data,
        regime=regime_name,
        regime_label=REGIME_LABELS.get(regime_name or "", ""),
        thresholds_text=_thresholds_text(payload.get("limiares")),
        latest_data_date=latest,
        defasado=_is_stale(latest, reference),
        janela=options.janela,
    )


def _thresholds_text(thresholds: object) -> str:
    values = _as_dict(thresholds)
    parts: list[str] = []
    for key, label in (
        ("var_aumento", "3m >"),
        ("var_deterioracao", "3m <"),
        ("drawdown", "drawdown <="),
    ):
        value = values.get(key)
        if isinstance(value, (int, float)):
            parts.append(f"{label} {value:.1f}%")
    return "; ".join(parts)


__all__ = [
    "JANELA_LABELS",
    "ReservesChartData",
    "build_chart_data",
    "moving_average",
]
