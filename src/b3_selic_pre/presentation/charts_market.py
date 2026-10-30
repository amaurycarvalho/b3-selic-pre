"""Renderizador matplotlib dos painéis de câmbio e ouro."""

from __future__ import annotations

import textwrap
from datetime import datetime
from typing import TYPE_CHECKING

from b3_selic_pre.presentation.charts_hover import HoverPoint, register_hover
from b3_selic_pre.presentation.market_chart_data import (
    ChartPanelData,
    MarketChartData,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_FORECAST_COLOR = "#c0392b"
_FIB_COLOR = "#7f8c8d"


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
        0.5, 0.5, message, ha="center", va="center",
        transform=ax.transAxes, fontsize=12, color="gray",
    )
    ax.set_axis_off()
    fig.tight_layout(pad=0.4)


def _draw_history(ax: object, panel: ChartPanelData) -> None:
    dates = _dates(panel.datas)
    values = list(panel.valores)[: len(dates)]
    if not dates:
        return
    ax.plot(dates, values, color="#1f4e79", linewidth=1.2, label="Histórico")
    lows = list(panel.minimos)[: len(dates)]
    highs = list(panel.maximos)[: len(dates)]
    if len(lows) == len(dates) and len(highs) == len(dates):
        ax.fill_between(
            dates, lows, highs, color="#1f4e79", alpha=0.15,
            label="Faixa mín-máx",
        )


def _draw_forecast(ax: object, panel: ChartPanelData) -> datetime | None:
    dates = _dates(panel.previsao_datas)
    if not dates:
        return None
    center = list(panel.previsao_centro)[: len(dates)]
    ax.plot(
        dates, center, linestyle="--", color=_FORECAST_COLOR,
        linewidth=1.2, label="Cenário",
    )
    colors = {80: "#f5b7b1", 95: "#fadbd8"}
    for band in panel.bandas:
        lows = list(band.inferiores)[: len(dates)]
        highs = list(band.superiores)[: len(dates)]
        if len(lows) != len(dates) or len(highs) != len(dates):
            continue
        ax.fill_between(
            dates, lows, highs, color=colors.get(band.nivel, "#eeeeee"),
            alpha=0.5, label=f"Banda {band.nivel}%",
        )
    return dates[-1]


def _asset_name(panel: ChartPanelData) -> str:
    return "Dólar" if panel.ativo == "usd" else "Ouro"


def _unit_label(panel: ChartPanelData, base100: bool) -> str:
    return "base 100" if base100 else panel.unidade


def _history_hover(
    panel: ChartPanelData, base100: bool
) -> list[HoverPoint]:
    from matplotlib.dates import date2num

    unit = _unit_label(panel, base100)
    asset = _asset_name(panel)
    dates = _dates(panel.datas)
    values = list(panel.valores)[: len(dates)]
    lows = list(panel.minimos)[: len(dates)]
    highs = list(panel.maximos)[: len(dates)]
    points: list[HoverPoint] = []
    for index, (day, value) in enumerate(zip(dates, values)):
        text = f"{day:%d/%m/%Y} — {asset}: {value:.2f} {unit}"
        if (
            index < len(lows)
            and index < len(highs)
            and lows[index] != highs[index]
        ):
            text += (
                f"\nFaixa: {lows[index]:.2f}–{highs[index]:.2f} {unit}"
            )
        points.append((date2num(day), value, text))
    return points


def _forecast_hover(
    panel: ChartPanelData, base100: bool
) -> list[HoverPoint]:
    from matplotlib.dates import date2num

    unit = _unit_label(panel, base100)
    asset = _asset_name(panel)
    dates = _dates(panel.previsao_datas)
    centers = list(panel.previsao_centro)[: len(dates)]
    points: list[HoverPoint] = []
    for index, (day, value) in enumerate(zip(dates, centers)):
        lines = [
            f"{day:%d/%m/%Y} — {asset} (cenário): {value:.2f} {unit}"
        ]
        for band in panel.bandas:
            if index < len(band.inferiores) and index < len(band.superiores):
                lines.append(
                    f"Banda {band.nivel}%: "
                    f"{band.inferiores[index]:.2f}–"
                    f"{band.superiores[index]:.2f} {unit}"
                )
        points.append((date2num(day), value, "\n".join(lines)))
    return points


def _register_hover(
    ax: object, panel: ChartPanelData, base100: bool
) -> None:
    points = _history_hover(panel, base100)
    points.extend(_forecast_hover(panel, base100))
    register_hover(ax, points)  # type: ignore[arg-type]


def _draw_fibonacci(ax: object, panel: ChartPanelData) -> None:
    if not panel.fibonacci:
        return
    for level, value in sorted(panel.fibonacci.items()):
        ax.axhline(value, color=_FIB_COLOR, linewidth=0.7, linestyle=":")
        ax.annotate(
            f"Fib {level:g}%", xy=(0.01, value),
            xycoords=("axes fraction", "data"), fontsize=7,
            color=_FIB_COLOR, va="bottom",
        )


def _decorate(ax: object, panel: ChartPanelData, base100: bool) -> None:
    ax.set_title(panel.label, fontsize=10, loc="left")
    label = panel.unidade + (" (base 100)" if base100 else "")
    ax.set_ylabel(label, fontsize=8)
    ax.grid(True, alpha=0.25)
    ax.tick_params(axis="x", labelrotation=30, labelsize=7)


def _draw_today(
    ax: object, today: datetime | None, end: datetime | None
) -> None:
    if today is None:
        return
    ax.axvline(today, color="black", linewidth=0.8)
    if end is not None and end > today:
        ax.axvspan(today, end, color="gray", alpha=0.08)


def _legend_handles(
    axes: list[object],
) -> tuple[list[object], list[str]]:
    handles: dict[str, object] = {}
    for ax in axes:
        for handle, label in zip(*ax.get_legend_handles_labels()):  # type: ignore[attr-defined]
            handles.setdefault(label, handle)
    return list(handles.values()), list(handles)


def render_market(fig: Figure, data: MarketChartData) -> None:
    """Render stacked dollar/gold panels plus the policy signal strip."""
    if data.vazio or not data.paineis:
        _empty(fig, data.mensagem or "Sem dados para exibir.")
        return
    fig.clf()
    rows = len(data.paineis) + 2
    heights = [3] * len(data.paineis) + [0.4, 0.6]
    grid = fig.add_gridspec(rows, 1, height_ratios=heights)
    axes = [
        fig.add_subplot(grid[index, 0], sharex=None)
        for index in range(len(data.paineis))
    ]
    for index in range(1, len(axes)):
        axes[index].sharex(axes[0])
    try:
        today = datetime.fromisoformat(data.hoje)
    except ValueError:
        today = None
    for ax, panel in zip(axes, data.paineis):
        _draw_history(ax, panel)
        end = _draw_forecast(ax, panel)
        _draw_fibonacci(ax, panel)
        _draw_today(ax, today, end)
        _decorate(ax, panel, data.base100)
        _register_hover(ax, panel, data.base100)
    legend_ax = fig.add_subplot(grid[rows - 2, 0])
    legend_ax.set_axis_off()
    handles, labels = _legend_handles(axes)
    if handles:
        legend_ax.legend(
            handles,
            labels,
            loc="center",
            ncol=len(handles),
            fontsize=7,
            frameon=False,
        )
    policy = fig.add_subplot(grid[rows - 1, 0])
    policy.set_axis_off()
    policy.text(
        0.0, 0.5,
        textwrap.fill(data.indicadores_texto, width=110),
        fontsize=7, va="center", transform=policy.transAxes,
    )
    fig.tight_layout(pad=0.4)


__all__ = ["render_market"]
