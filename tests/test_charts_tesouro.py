import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure

from b3_selic_pre.presentation.charts_tesouro import (
    render_current_comparison,
    render_current_share,
    render_evolution,
    render_gap,
)
from b3_selic_pre.presentation.tesouro_analise_view_model import (
    ComparisonChart,
    EvolutionChart,
    GapChart,
    ShareChart,
)


def test_render_current_share_draws_stacked_bars():
    figure = Figure()
    chart = ShareChart(
        title="Estoque",
        families=("SELIC", "IPCA"),
        totals={"SELIC": 70.0, "IPCA": 30.0},
        segments={
            "SELIC": {"Tesouro Selic 2029": 70.0},
            "IPCA": {"Tesouro IPCA+ 2035": 30.0},
        },
    )

    render_current_share(figure, chart)

    axis = figure.gca()
    assert len(axis.patches) == 4
    assert axis.get_ylim() == (0.0, 100.0)


def test_render_current_comparison_draws_grouped_bars():
    figure = Figure()
    chart = ComparisonChart(
        title="Comparação",
        families=("SELIC", "IPCA"),
        estoque=(70.0, 30.0),
        apetite=(60.0, 40.0),
    )

    render_current_comparison(figure, chart)

    assert len(figure.gca().patches) == 4


def test_render_evolution_draws_stackplot():
    figure = Figure()
    chart = EvolutionChart(
        title="Evolução",
        periods=("2026-09", "2026-10"),
        series={"SELIC": (60.0, 70.0), "IPCA": (40.0, 30.0)},
    )

    render_evolution(figure, chart)

    assert len(figure.gca().collections) >= 1
    assert figure.gca().get_ylim() == (0.0, 100.0)


def test_render_gap_draws_one_line_per_family():
    figure = Figure()
    chart = GapChart(
        title="Gap",
        periods=("2026-09", "2026-10"),
        series={"SELIC": (-10.0, 0.0), "IPCA": (10.0, 5.0)},
    )

    render_gap(figure, chart)

    assert len(figure.gca().lines) == 3


def test_renderers_draw_empty_state_without_error():
    figure = Figure()
    render_current_share(
        figure, ShareChart("vazio", (), {}, {})
    )
    assert "Sem dados" in figure.gca().texts[0].get_text()

    render_evolution(
        figure, EvolutionChart("vazio", (), {})
    )
    assert "Sem dados" in figure.gca().texts[0].get_text()

    render_gap(figure, GapChart("vazio", (), {}))
    assert "Sem dados" in figure.gca().texts[0].get_text()


def test_current_share_registers_hover_points():
    figure = Figure()
    chart = ShareChart(
        title="Estoque",
        families=("SELIC", "IPCA"),
        totals={"SELIC": 70.0, "IPCA": 30.0},
        segments={
            "SELIC": {"Tesouro Selic 2029": 70.0},
            "IPCA": {"Tesouro IPCA+ 2035": 30.0},
        },
    )

    render_current_share(figure, chart)

    points = figure.gca()._hover_points
    assert len(points) == 2
    assert "Tesouro Selic 2029" in points[0][2]


def test_evolution_vertical_grid_sets_one_tick_per_period():
    figure = Figure()
    chart = EvolutionChart(
        title="Evolução",
        periods=("2026-09", "2026-10"),
        series={"SELIC": (60.0, 70.0), "IPCA": (40.0, 30.0)},
        vertical_grid=True,
    )

    render_evolution(figure, chart)

    axis = figure.gca()
    assert len(axis.get_xticks()) == 2
    assert len(axis._hover_points) == 4
