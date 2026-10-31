"""Renderizadores dos gráficos analíticos do Tesouro Direto."""

from __future__ import annotations

from typing import TYPE_CHECKING

from b3_selic_pre.presentation.chart_layout import apply_tight_layout
from b3_selic_pre.presentation.charts_hover import HoverPoint, register_hover
from b3_selic_pre.presentation.tesouro_analise_view_model import (
    ComparisonChart,
    EvolutionChart,
    GapChart,
    ShareChart,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_YMAX = 100.0


def _empty(fig: Figure, title: str, message: str, ylabel: str = "%") -> None:
    """Draw a centered message on an empty chart."""
    fig.clf()
    ax = fig.add_subplot(111)
    ax.text(
        0.5, 0.5, message, ha="center", va="center",
        transform=ax.transAxes, fontsize=12, color="gray",
    )
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, _YMAX)
    apply_tight_layout(fig, context=f"Tesouro: vazio ({title})")


def render_current_share(fig: Figure, chart: ShareChart) -> None:
    """Render a 100% stacked bar chart with title segments per family."""
    if not chart.families:
        _empty(fig, chart.title, "Sem dados para a janela selecionada.")
        return
    import numpy as np

    fig.clf()
    ax = fig.add_subplot(111)
    positions = np.arange(len(chart.families))
    bottom = np.zeros(len(chart.families))
    hover: list[HoverPoint] = []
    titles: list[str] = []
    for family in chart.families:
        for title in chart.segments.get(family, {}):
            if title not in titles:
                titles.append(title)
    for title in titles:
        values = np.array(
            [
                chart.segments.get(family, {}).get(title, 0.0)
                for family in chart.families
            ]
        )
        ax.bar(positions, values, bottom=bottom, label=title)
        for index, value in enumerate(values):
            if value:
                hover.append(
                    (
                        float(positions[index]),
                        float(bottom[index] + value),
                        f"{chart.families[index]} — {title}: {value:.1f}%",
                    )
                )
        bottom += values
    _categorical_x(ax, chart.families)
    ax.set_ylim(0, _YMAX)
    ax.set_ylabel("%")
    ax.set_title(chart.title)
    ax.grid(True, axis="y", alpha=0.3)
    if titles:
        ax.legend(fontsize=7, loc="upper right", ncol=2)
    register_hover(ax, hover)
    apply_tight_layout(
        fig, context=f"render_current_share: {chart.title}"
    )


def render_current_comparison(fig: Figure, chart: ComparisonChart) -> None:
    """Render grouped stock-versus-appetite bars per family."""
    if not chart.families:
        _empty(fig, chart.title, "Sem dados para a janela selecionada.")
        return
    import numpy as np

    fig.clf()
    ax = fig.add_subplot(111)
    positions = np.arange(len(chart.families))
    width = 0.38
    ax.bar(
        positions - width / 2, chart.estoque, width,
        label="Estoque", color="#2a6fdb",
    )
    ax.bar(
        positions + width / 2, chart.apetite, width,
        label="Apetite do mercado", color="#e08a1e",
    )
    hover: list[HoverPoint] = []
    for index, family in enumerate(chart.families):
        hover.append(
            (
                float(positions[index] - width / 2),
                chart.estoque[index],
                f"{family} — Estoque: {chart.estoque[index]:.1f}%",
            )
        )
        hover.append(
            (
                float(positions[index] + width / 2),
                chart.apetite[index],
                f"{family} — Apetite: {chart.apetite[index]:.1f}%",
            )
        )
    _categorical_x(ax, chart.families)
    ax.set_ylim(0, _YMAX)
    ax.set_ylabel("%")
    ax.set_title(chart.title)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    register_hover(ax, hover)
    apply_tight_layout(
        fig, context=f"render_current_comparison: {chart.title}"
    )


def render_evolution(fig: Figure, chart: EvolutionChart) -> None:
    """Render a 100% stacked area chart of family shares over time."""
    if not chart.periods or not chart.series:
        _empty(fig, chart.title, "Sem dados para a janela selecionada.")
        return
    import numpy as np

    fig.clf()
    ax = fig.add_subplot(111)
    families = list(chart.series)
    values = np.array([list(chart.series[family]) for family in families])
    positions = np.arange(len(chart.periods))
    ax.stackplot(positions, *values, labels=families, alpha=0.85)
    hover: list[HoverPoint] = []
    cumulative = np.zeros(len(chart.periods))
    for row, family in enumerate(families):
        cumulative = cumulative + values[row]
        for index, value in enumerate(values[row]):
            if value:
                hover.append(
                    (
                        float(positions[index]),
                        float(cumulative[index]),
                        f"{family} — {chart.periods[index]}: {value:.1f}%",
                    )
                )
    ax.set_xticks(positions)
    ax.set_xticklabels(chart.periods)
    ax.set_ylim(0, _YMAX)
    ax.set_ylabel("%")
    ax.set_title(chart.title)
    ax.grid(True, axis="y", alpha=0.3)
    if chart.vertical_grid:
        ax.grid(True, axis="x", alpha=0.3)
    ax.legend(fontsize=7, loc="upper left", ncol=len(families) or 1)
    _rotate_labels(ax)
    register_hover(ax, hover)
    apply_tight_layout(
        fig, context=f"render_evolution: {chart.title}"
    )


def render_gap(fig: Figure, chart: GapChart) -> None:
    """Render the appetite-minus-stock gap as lines per family."""
    if not chart.periods or not chart.series:
        _empty(
            fig, chart.title, "Sem dados para a janela selecionada.",
            ylabel="p.p.",
        )
        return
    fig.clf()
    ax = fig.add_subplot(111)
    positions = list(range(len(chart.periods)))
    hover: list[HoverPoint] = []
    for family, values in chart.series.items():
        ax.plot(positions, list(values), marker="o", label=family)
        for index, value in enumerate(values):
            hover.append(
                (
                    float(positions[index]),
                    value,
                    f"{family} — {chart.periods[index]}: {value:.1f} p.p.",
                )
            )
    ax.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks(positions)
    ax.set_xticklabels(chart.periods)
    ax.set_ylabel("p.p.")
    ax.set_title(chart.title)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=7, loc="upper left")
    _rotate_labels(ax)
    register_hover(ax, hover)
    apply_tight_layout(fig, context=f"render_gap: {chart.title}")


def _categorical_x(ax: object, families: tuple[str, ...]) -> None:
    ax.set_xticks(range(len(families)))  # type: ignore[attr-defined]
    ax.set_xticklabels(families)  # type: ignore[attr-defined]


def _rotate_labels(ax: object) -> None:
    for label in ax.get_xticklabels():  # type: ignore[attr-defined]
        label.set_rotation(35)
        label.set_horizontalalignment("right")
