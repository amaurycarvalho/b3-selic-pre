"""Renderizador matplotlib da evolução das reservas internacionais."""

from __future__ import annotations

import textwrap
from datetime import datetime
from typing import TYPE_CHECKING

from b3_selic_pre.presentation.chart_layout import apply_tight_layout
from b3_selic_pre.presentation.charts_hover import (
    HoverPoint,
    register_hover,
)
from b3_selic_pre.presentation.reserves_chart_data import ReservesChartData

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_LINE_COLOR = "#1f4e79"
_MA30_COLOR = "#e67e22"
_MA90_COLOR = "#8e44ad"


def _dates(values: tuple[str, ...]) -> list[datetime]:
    parsed: list[datetime] = []
    for value in values:
        try:
            parsed.append(datetime.fromisoformat(value))
        except ValueError:
            continue
    return parsed


def _empty(fig: Figure, message: str) -> None:
    fig.clf()
    ax = fig.add_subplot(111)
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=12,
        color="gray",
    )
    ax.set_axis_off()
    apply_tight_layout(fig, context="Reservas: vazio", pad=0.4)


def _draw_series(ax: object, data: ReservesChartData) -> None:
    dates = _dates(data.datas)
    values = list(data.valores)[: len(dates)]
    if not dates:
        return
    ax.plot(
        dates,
        values,
        color=_LINE_COLOR,
        linewidth=1.4,
        label="Reservas",
    )
    if values:
        ax.fill_between(
            dates,
            [min(values)] * len(dates),
            values,
            color=_LINE_COLOR,
            alpha=0.12,
        )
    for series, color, label in (
        (data.medias_30, _MA30_COLOR, "Média 30d"),
        (data.medias_90, _MA90_COLOR, "Média 90d"),
    ):
        if len(series) == len(dates):
            ax.plot(
                dates,
                list(series),
                color=color,
                linewidth=0.9,
                linestyle="--",
                label=label,
            )


def _draw_extremes(ax: object, data: ReservesChartData) -> None:
    for day, value, label in (
        (data.maximo_data, data.maximo, "Máx."),
        (data.minimo_data, data.minimo, "Mín."),
    ):
        if day is None or value is None:
            continue
        try:
            parsed = datetime.fromisoformat(day)
        except ValueError:
            continue
        ax.scatter([parsed], [value], color="#c0392b", s=18, zorder=5)
        ax.annotate(
            f"{label} {value:.1f}",
            xy=(parsed, value),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            color="#c0392b",
        )


def _footer(data: ReservesChartData) -> str:
    parts: list[str] = []
    if data.regime_label:
        parts.append(f"Regime: {data.regime_label}")
    if data.thresholds_text:
        parts.append(f"Limiares: {data.thresholds_text}")
    parts.append(
        "Sinal direcional, não é recomendação de investimento."
    )
    if data.defasado:
        parts.append(f"Dados defasados (último: {data.latest_data_date}).")
    return "\n".join(parts)



def _hover_points(data: ReservesChartData) -> list[HoverPoint]:
    from matplotlib.dates import date2num

    dates = _dates(data.datas)
    values = list(data.valores)[: len(dates)]
    raw_dates = list(data.datas)[: len(dates)]
    ma30 = list(data.medias_30)
    ma90 = list(data.medias_90)
    points: list[HoverPoint] = []
    for index, (day, value, raw_day) in enumerate(
        zip(dates, values, raw_dates)
    ):
        lines = [
            f"{day:%d/%m/%Y} — Reservas: {value:.1f} {data.unidade}"
        ]
        if index < len(ma30):
            lines.append(f"Média 30d: {ma30[index]:.1f}")
        if index < len(ma90):
            lines.append(f"Média 90d: {ma90[index]:.1f}")
        if data.maximo_data == raw_day:
            lines.append("Máximo da janela")
        if data.minimo_data == raw_day:
            lines.append("Mínimo da janela")
        points.append((date2num(day), value, "\n".join(lines)))
    return points


def _register_hover(ax: object, data: ReservesChartData) -> None:
    register_hover(ax, _hover_points(data))  # type: ignore[arg-type]


def render_reserves(fig: Figure, data: ReservesChartData) -> None:
    """Render the reserves line/area chart with averages and badges."""
    if data.vazio or not data.datas:
        _empty(fig, data.mensagem or "Sem dados para exibir.")
        return
    fig.clf()
    grid = fig.add_gridspec(2, 1, height_ratios=[4, 0.7])
    ax = fig.add_subplot(grid[0, 0])
    _draw_series(ax, data)
    _draw_extremes(ax, data)
    _register_hover(ax, data)
    ax.set_title("Reservas Internacionais", fontsize=10, loc="left")
    ax.set_ylabel(data.unidade, fontsize=8)
    ax.grid(True, alpha=0.25)
    ax.tick_params(axis="x", labelrotation=30, labelsize=7)
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="best", fontsize=7, frameon=False)
    footer = fig.add_subplot(grid[1, 0])
    footer.set_axis_off()
    footer.text(
        0.0,
        0.5,
        textwrap.fill(_footer(data), width=110),
        fontsize=7,
        va="center",
        transform=footer.transAxes,
    )
    apply_tight_layout(fig, context="Reservas: render_reserves", pad=0.4)


__all__ = ["render_reserves"]
