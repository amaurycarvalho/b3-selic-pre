import unittest
from unittest import mock

import numpy as np

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation.charts import (
    _draw_evolution_arrows,
    _plot_3d_consolidated_lines,
    _plot_3d_daily_lines,
    _render_empty,
    _setup_xy_grid,
    render_3d_evolution,
    render_chart,
    render_curve_evolution,
    render_detailed_evolution,
)


def _records(*pairs):
    return [
        RateRecord(day252=d, day360=d, rate=str(r).replace(".", ","))
        for d, r in pairs
    ]


class RecordingAx:
    """Records matplotlib Axes method calls for assertion."""

    def __init__(self):
        self.calls = {"plot": [], "quiver": [], "text": [], "set_xlim": []}
        self.texts = []
        self.transAxes = "transAxes"
        self._xlabel = None
        self._ylabel = None
        self._zlabel = None
        self._legend_kwargs = None
        self._view_init = None
        self._surface_kwargs = None
        self._yticklabels_kwargs = None

    def plot(self, *args, **kwargs):
        self.calls["plot"].append((args, kwargs))

    def plot_surface(self, *args, **kwargs):
        self._surface_kwargs = kwargs
        return mock.Mock()

    def quiver(self, *args, **kwargs):
        self.calls["quiver"].append((args, kwargs))

    def text(self, *args, **kwargs):
        self.calls.setdefault("text", []).append((args, kwargs))
        self.texts.append(args[1] if len(args) > 1 else None)

    def set_xlim(self, *args):
        self.calls["set_xlim"].append(args)

    def set_xlabel(self, label, *args, **kwargs):
        self._xlabel = label

    def set_ylabel(self, label, *args, **kwargs):
        self._ylabel = label

    def set_zlabel(self, label, *args, **kwargs):
        self._zlabel = label

    def set_yticks(self, *args, **kwargs):
        pass

    def set_yticklabels(self, *args, **kwargs):
        self._yticklabels_kwargs = kwargs

    def set_xticks(self, ticks, *args, **kwargs):
        self.calls.setdefault("set_xticks", []).append((ticks, args, kwargs))

    def grid(self, *args, **kwargs):
        self.calls.setdefault("grid", []).append((args, kwargs))

    def legend(self, *args, **kwargs):
        self._legend_kwargs = kwargs

    def view_init(self, *args, **kwargs):
        self._view_init = kwargs


class RecordingFig:
    def __init__(self):
        self.axes = []
        self._colorbar_kwargs = None
        self._subplots_adjust = None

    def add_subplot(self, *args, **kwargs):
        ax = RecordingAx()
        self.axes.append(ax)
        return ax

    def clf(self):
        pass

    def tight_layout(self):
        pass

    def subplots_adjust(self, **kwargs):
        self._subplots_adjust = kwargs

    def colorbar(self, *args, **kwargs):
        self._colorbar_kwargs = kwargs
        return mock.Mock()

    def gca(self):
        if not self.axes:
            self.axes.append(RecordingAx())
        return self.axes[-1]


class RenderEmptyTest(unittest.TestCase):
    def test_render_empty_sets_labels(self):
        fig = RecordingFig()
        _render_empty(fig, "mensagem", "xlabel", "ylabel")
        self.assertEqual(len(fig.axes), 1)

    def test_render_empty_text_kwargs(self):
        fig = RecordingFig()
        _render_empty(fig, "mensagem", "xlabel", "ylabel")
        args, kwargs = fig.axes[0].calls["text"][0]
        self.assertEqual(args, (0.5, 0.5, "mensagem"))
        self.assertEqual(kwargs["ha"], "center")
        self.assertEqual(kwargs["va"], "center")
        self.assertEqual(kwargs["fontsize"], 14)
        self.assertEqual(kwargs["color"], "gray")
        self.assertEqual(kwargs["transform"], "transAxes")


class SetupXyGridTest(unittest.TestCase):
    def test_grid_sets_major_and_minor(self):
        ax = RecordingAx()
        _setup_xy_grid(ax, "Ano", 20, [3, 6], [1, 2, 4])
        self.assertEqual(ax.calls["set_xlim"], [(0, 20)])

    def test_grid_calls(self):
        ax = RecordingAx()
        _setup_xy_grid(ax, "Ano", 20, [3, 6], [1, 2, 4])
        major = [g for g in ax.calls["grid"] if g[1].get("which") == "major"]
        minor = [g for g in ax.calls["grid"] if g[1].get("which") == "minor"]
        self.assertEqual(len(major), 1)
        self.assertEqual(len(minor), 1)
        self.assertEqual(major[0][0], (True,))
        self.assertEqual(major[0][1]["alpha"], 0.3)
        self.assertEqual(minor[0][0], (True,))
        self.assertEqual(minor[0][1]["alpha"], 0.15)
        self.assertEqual(minor[0][1]["linestyle"], "--")

    def test_grid_ylabel(self):
        ax = RecordingAx()
        _setup_xy_grid(ax, "Ano", 20, [3], [1])
        self.assertEqual(ax._ylabel, "TAXA (%)")

    def test_grid_custom_ylabel(self):
        ax = RecordingAx()
        _setup_xy_grid(ax, "Ano", 20, [3], [1], ylabel="CUSTOM")
        self.assertEqual(ax._ylabel, "CUSTOM")


class DrawEvolutionArrowsTest(unittest.TestCase):
    def _sample(self):
        dates = ["2026-01-01", "2026-01-02", "2026-01-03"]

        def sample(date_str, tick):
            rates = {1: 14.0, 2: 15.0, 3: 16.0}
            return rates.get(tick)

        return dates, [1, 2, 3], sample

    def test_draws_quiver_for_transitions(self):
        ax = RecordingAx()
        dates, ticks, sample = self._sample()
        _draw_evolution_arrows(ax, dates, ticks, lambda c: ["c"] * 10, sample)
        self.assertGreater(len(ax.calls["quiver"]), 0)

    def test_skips_ticks_without_two_rates(self):
        ax = RecordingAx()
        dates = ["2026-01-01"]

        def sample(date_str, tick):
            return None

        _draw_evolution_arrows(ax, dates, [1, 2], lambda c: ["c"] * 10, sample)
        self.assertEqual(ax.calls["quiver"], [])

    def test_quiver_positions_use_original_ticks(self):
        ax = RecordingAx()
        dates, ticks, sample = self._sample()
        _draw_evolution_arrows(ax, dates, ticks, lambda c: ["c"] * 10, sample)
        for args, _ in ax.calls["quiver"]:
            self.assertIsInstance(args[0], list)

    def test_quiver_exact_calls(self):
        ax = RecordingAx()
        dates = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]

        def sample(date_str, tick):
            rates = {1: 14.0, 2: 15.0, 3: 16.0, 4: 17.0}
            return rates.get(tick)

        def fake_cmap(vals):
            return [f"c{i}" for i in range(len(vals))]

        _draw_evolution_arrows(ax, dates, [1, 2, 3, 4], fake_cmap, sample)
        self.assertEqual(len(ax.calls["quiver"]), 3)
        self.assertEqual(ax.calls["quiver"][0][0], ([2.0], [15.0], [0.06], [0.0]))
        self.assertEqual(ax.calls["quiver"][1][0], ([3.06], [16.0], [0.06], [0.0]))
        self.assertEqual(ax.calls["quiver"][2][0], ([4.12], [17.0], [0.06], [0.0]))
        for _, kwargs in ax.calls["quiver"]:
            self.assertEqual(kwargs["angles"], "xy")
            self.assertEqual(kwargs["scale_units"], "xy")
            self.assertEqual(kwargs["scale"], 1)
            self.assertEqual(kwargs["width"], 0.004)
            self.assertEqual(kwargs["zorder"], 5)
            self.assertIn(kwargs["color"], ["c0", "c1", "c2"])

    def test_quiver_skips_tick_without_transition(self):
        ax = RecordingAx()
        dates = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]

        def sample(date_str, tick):
            # only one rate across all dates for tick 2
            if tick == 2:
                return 15.0 if date_str == dates[0] else None
            return {1: 14.0, 2: 15.0, 3: 16.0, 4: 17.0}[tick]

        _draw_evolution_arrows(ax, dates, [1, 2, 3], lambda c: ["c"] * 10, sample)
        self.assertEqual(len(ax.calls["quiver"]), 1)
        self.assertEqual(ax.calls["quiver"][0][0][0][0], 3.06)

    def test_quiver_five_dates_color_progression(self):
        ax = RecordingAx()
        dates = ["d0", "d1", "d2", "d3", "d4"]

        def sample(date_str, tick):
            idx = dates.index(date_str)
            return {1: 14.0, 2: 15.0, 3: 16.0, 4: 17.0, 5: 18.0}[tick] + idx

        _draw_evolution_arrows(ax, dates, [1, 2, 3, 4, 5], list, sample)
        self.assertEqual(len(ax.calls["quiver"]), 4)
        colors = [float(kwargs["color"]) for _, kwargs in ax.calls["quiver"]]
        self.assertAlmostEqual(colors[0], 0.3)
        self.assertAlmostEqual(colors[1], 0.5)
        self.assertAlmostEqual(colors[2], 0.7)
        self.assertAlmostEqual(colors[3], 0.9)
        positions = [args[0][0] for args, _ in ax.calls["quiver"]]
        self.assertEqual(positions, [2.0, 3.06, 4.12, 5.18])
        # arrow dy uses next rate minus current (rates increase by 1.0 per date)
        dys = [args[3][0] for args, _ in ax.calls["quiver"]]
        self.assertEqual(dys, [1.0, 1.0, 1.0, 1.0])
        # from-rates are the rates at trans_idx (2,3,4,5) over increasing dates
        froms = [args[1][0] for args, _ in ax.calls["quiver"]]
        self.assertEqual(froms, [15.0, 17.0, 19.0, 21.0])


class Plot3dConsolidatedLinesTest(unittest.TestCase):
    def _rates(self):
        return [
            {0: 14.0, 1: 15.0, 2: 16.0},
            {0: 14.5, 1: 15.5, 2: 16.5},
            {0: 15.0, 1: 16.0, 2: 17.0},
        ]

    def test_plots_one_line_per_date(self):
        ax = RecordingAx()
        _plot_3d_consolidated_lines(ax, self._rates(), [0, 1, 2])
        self.assertEqual(len(ax.calls["plot"]), 3)

    def test_plots_line_for_each_z_index(self):
        ax = RecordingAx()
        _plot_3d_consolidated_lines(ax, self._rates(), [0, 1, 2])
        z_values = [args[1][0] for args, _ in ax.calls["plot"]]
        self.assertIn(0, z_values)
        self.assertIn(2, z_values)

    def test_filters_years_outside_0_20(self):
        ax = RecordingAx()
        rates = [{0: 14.0, 5: 15.0, 21: 16.0}]
        _plot_3d_consolidated_lines(ax, rates, [0])
        x_vals = ax.calls["plot"][0][0][0]
        self.assertNotIn(21, x_vals)

    def test_filters_years_at_20_included(self):
        ax = RecordingAx()
        rates = [{0: 14.0, 20: 15.0}]
        _plot_3d_consolidated_lines(ax, rates, [0])
        x_vals = ax.calls["plot"][0][0][0]
        self.assertIn(20, x_vals)

    def test_year_zero_included(self):
        ax = RecordingAx()
        rates = [{0: 14.0, 1: 15.0}]
        _plot_3d_consolidated_lines(ax, rates, [0])
        x_vals = ax.calls["plot"][0][0][0]
        self.assertIn(0, x_vals)

    def test_plot_exact_args(self):
        ax = RecordingAx()
        rates = [{0: 14.0, 1: 15.0, 2: 16.0}]
        _plot_3d_consolidated_lines(ax, rates, [0])
        args, kwargs = ax.calls["plot"][0]
        self.assertEqual(args[0], [0, 1, 2])
        self.assertEqual(args[1], [0, 0, 0])
        self.assertEqual(args[2], [14.0, 15.0, 16.0])
        self.assertEqual(kwargs["color"], "black")
        self.assertEqual(kwargs["linewidth"], 0.8)
        self.assertEqual(kwargs["alpha"], 0.7)

    def test_plot_reversed_z_order(self):
        ax = RecordingAx()
        rates = [
            {0: 14.0, 1: 15.0},
            {0: 14.5, 1: 15.5},
            {0: 15.0, 1: 16.0},
        ]
        _plot_3d_consolidated_lines(ax, rates, [0, 1, 2])
        z_first = ax.calls["plot"][0][0][1][0]
        z_last = ax.calls["plot"][-1][0][1][0]
        self.assertEqual(z_first, 2)
        self.assertEqual(z_last, 0)
        self.assertEqual(ax.calls["plot"][0][0][2], [15.0, 16.0])
        self.assertEqual(ax.calls["plot"][-1][0][2], [14.0, 15.0])

    def test_plot_linewidths(self):
        ax = RecordingAx()
        rates = [
            {0: 14.0, 1: 15.0},
            {0: 14.5, 1: 15.5},
            {0: 15.0, 1: 16.0},
        ]
        _plot_3d_consolidated_lines(ax, rates, [0, 1, 2])
        widths = [kwargs["linewidth"] for _, kwargs in ax.calls["plot"]]
        self.assertAlmostEqual(widths[0], 0.8)
        self.assertAlmostEqual(widths[1], 1.225)
        self.assertAlmostEqual(widths[2], 1.65)


class Plot3dDailyLinesTest(unittest.TestCase):
    def _data(self):
        return [
            ([1, 2], [14.0, 15.0]),
            ([1, 2], [14.5, 15.5]),
            ([1, 2], [15.0, 16.0]),
        ]

    def test_plots_one_line_per_date(self):
        ax = RecordingAx()
        _plot_3d_daily_lines(ax, self._data(), [0, 1, 2])
        self.assertEqual(len(ax.calls["plot"]), 3)

    def test_plots_rates_as_z(self):
        ax = RecordingAx()
        _plot_3d_daily_lines(ax, self._data(), [0, 1, 2])
        for args, _ in ax.calls["plot"]:
            self.assertIsNotNone(args[2])

    def test_plot_exact_args(self):
        ax = RecordingAx()
        _plot_3d_daily_lines(ax, [([1, 2], [14.0, 15.0])], [0])
        args, kwargs = ax.calls["plot"][0]
        self.assertEqual(args[0], [1, 2])
        self.assertEqual(args[1], [0, 0])
        self.assertEqual(args[2], [14.0, 15.0])
        self.assertEqual(kwargs["color"], "black")
        self.assertEqual(kwargs["linewidth"], 0.8)
        self.assertEqual(kwargs["alpha"], 0.7)

    def test_plot_linewidths(self):
        ax = RecordingAx()
        _plot_3d_daily_lines(
            ax,
            [([1, 2], [14.0, 15.0]), ([1, 2], [14.5, 15.5]), ([1, 2], [15.0, 16.0])],
            [0, 1, 2],
        )
        widths = [kwargs["linewidth"] for _, kwargs in ax.calls["plot"]]
        self.assertAlmostEqual(widths[0], 0.8)
        self.assertAlmostEqual(widths[1], 1.225)
        self.assertAlmostEqual(widths[2], 1.65)

    def test_plot_iterates_reversed(self):
        ax = RecordingAx()
        _plot_3d_daily_lines(
            ax,
            [([1, 2], [14.0, 15.0]), ([1, 2], [14.5, 15.5]), ([1, 2], [15.0, 16.0])],
            [0, 1, 2],
        )
        z_first = ax.calls["plot"][0][0][1][0]
        self.assertEqual(z_first, 2)
        z_last = ax.calls["plot"][-1][0][1][0]
        self.assertEqual(z_last, 0)

    def test_plot_skips_empty_days(self):
        ax = RecordingAx()
        _plot_3d_daily_lines(
            ax,
            [([1, 2], [14.0, 15.0]), ([1, 2], [14.5, 15.5]), ([], [])],
            [0, 1, 2],
        )
        self.assertEqual(len(ax.calls["plot"]), 2)


class Render3dEvolutionTest(unittest.TestCase):
    def _date_rates(self):
        return {
            "2026-01-01": _records((1, 14.0), (365, 15.0)),
            "2026-01-02": _records((1, 14.5), (365, 15.5)),
        }

    def test_empty_sets_labels(self):
        fig = RecordingFig()
        render_3d_evolution(fig, {})
        self.assertEqual(len(fig.axes), 1)
        self.assertEqual(fig.axes[0]._ylabel, "Taxa")

    def test_empty_consolidated_xlabel(self):
        fig = RecordingFig()
        render_3d_evolution(fig, {}, consolidated=True)
        self.assertEqual(fig.axes[0]._xlabel, "Ano")

    def test_consolidated_xlim(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates(), consolidated=True)
        ax = fig.axes[0]
        self.assertIn((0, 20), ax.calls["set_xlim"])

    def test_consolidated_xlabel_ano(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates(), consolidated=True)
        self.assertEqual(fig.axes[0]._xlabel, "Ano")

    def test_daily_xlim(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates(), consolidated=False)
        ax = fig.axes[0]
        self.assertIn((0, 756), ax.calls["set_xlim"])

    def test_zlabel(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._zlabel, "Taxa %")

    def test_ylabel_periodo(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._ylabel, "Período")

    def test_view_init(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._view_init, {"elev": 25, "azim": -60})

    def test_surface_kwargs(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertIsNotNone(fig.axes[0]._surface_kwargs)
        self.assertEqual(fig.axes[0]._surface_kwargs["linewidth"], 0)

    def test_surface_cmap(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._surface_kwargs["cmap"], "RdYlGn_r")

    def test_colorbar_label_and_shrink(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(fig._colorbar_kwargs["label"], "Taxa %")
        self.assertEqual(fig._colorbar_kwargs["shrink"], 0.6)

    def test_subplots_adjust(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(
            fig._subplots_adjust,
            {"left": 0.1, "right": 0.8, "top": 0.9, "bottom": 0.1},
        )

    def test_yticklabels_fontsize(self):
        fig = RecordingFig()
        render_3d_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._yticklabels_kwargs["fontsize"], 8)


class RenderChartTest(unittest.TestCase):
    def test_consolidated_label_maior(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (365, 15.0), (730, 16.0)), consolidated=True)
        ax = fig.axes[0]
        labels = [kwargs.get("label") for _, kwargs in ax.calls["plot"]]
        self.assertIn("Maior taxa", labels)
        self.assertIn("Menor taxa", labels)

    def test_consolidated_xlabel_ano(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (365, 15.0)), consolidated=True)
        self.assertEqual(fig.axes[0]._xlabel, "Ano")

    def test_consolidated_xlim(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (365, 15.0)), consolidated=True)
        self.assertIn((0, 20), fig.axes[0].calls["set_xlim"])

    def test_consolidated_ticks(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (66, 15.0), (132, 16.0), (365, 14.5)), consolidated=True)
        ax = fig.axes[0]
        major = ax.calls["set_xticks"][0][0]
        minor = ax.calls["set_xticks"][1][0]
        self.assertEqual(major, [0])
        self.assertEqual(minor, [1])

    def test_raw_ticks(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (66, 15.0), (132, 16.0), (200, 14.5)), consolidated=False)
        ax = fig.axes[0]
        major = ax.calls["set_xticks"][0][0]
        minor = ax.calls["set_xticks"][1][0]
        self.assertEqual(major, [66, 132, 200])
        self.assertEqual(minor, [1])

    def test_raw_xlabel_dias_uteis(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (60, 15.0)), consolidated=False)
        self.assertEqual(fig.axes[0]._xlabel, "Dias úteis")

    def test_raw_xlim(self):
        fig = RecordingFig()
        render_chart(fig, _records((1, 14.0), (60, 15.0)), consolidated=False)
        self.assertIn((0, 756), fig.axes[0].calls["set_xlim"])

    def test_empty_xlabel_dc365(self):
        fig = RecordingFig()
        render_chart(fig, [])
        self.assertEqual(fig.axes[0]._xlabel, "DC365")
        self.assertEqual(fig.axes[0]._ylabel, "TAXA")

    def test_empty_calls_render_empty(self):
        fig = RecordingFig()
        render_chart(fig, [])
        self.assertEqual(len(fig.axes), 1)


class RenderCurveEvolutionTest(unittest.TestCase):
    def _date_rates(self):
        return {
            "2026-01-01": _records((1, 14.0), (365, 15.0)),
            "2026-01-02": _records((1, 14.5), (365, 15.5)),
        }

    def test_plots_two_dates(self):
        fig = RecordingFig()
        render_curve_evolution(fig, self._date_rates())
        ax = fig.axes[0]
        self.assertEqual(len(ax.calls["plot"]), 2)

    def test_empty_shows_message(self):
        fig = RecordingFig()
        render_curve_evolution(fig, {})
        self.assertEqual(len(fig.axes), 1)

    def test_plots_years_and_values(self):
        fig = RecordingFig()
        render_curve_evolution(fig, self._date_rates())
        ax = fig.axes[0]
        for args, _ in ax.calls["plot"]:
            self.assertEqual(len(args), 2)

    def test_xlabel_ano(self):
        fig = RecordingFig()
        render_curve_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._xlabel, "Ano")

    def test_plot_has_color(self):
        fig = RecordingFig()
        render_curve_evolution(fig, self._date_rates())
        for _, kwargs in fig.axes[0].calls["plot"]:
            self.assertIn("color", kwargs)
            self.assertIn("alpha", kwargs)
            self.assertIn("linewidth", kwargs)
            self.assertIn("label", kwargs)

    def test_empty_xlabel_ano(self):
        fig = RecordingFig()
        render_curve_evolution(fig, {})
        self.assertEqual(fig.axes[0]._xlabel, "Ano")
        self.assertEqual(fig.axes[0]._ylabel, "TAXA")

    def test_minor_ticks_exclude_majors(self):
        fig = RecordingFig()
        date_rates = {
            "2026-01-01": _records((1, 14.0), (366, 15.0)),
            "2026-01-02": _records((1, 14.5), (366, 15.5)),
            "2026-01-03": _records((1, 15.0), (366, 16.0)),
        }
        render_curve_evolution(fig, date_rates)
        ax = fig.axes[0]
        major = ax.calls["set_xticks"][0][0]
        minor = ax.calls["set_xticks"][1][0]
        for m in major:
            self.assertNotIn(m, minor)

    def test_minor_ticks_from_all_years(self):
        fig = RecordingFig()
        date_rates = {
            "2026-01-01": _records((1, 14.0), (366, 15.0)),
            "2026-01-02": _records((1, 14.5), (366, 15.5)),
            "2026-01-03": _records((1, 15.0), (366, 16.0)),
        }
        render_curve_evolution(fig, date_rates)
        ax = fig.axes[0]
        minor = ax.calls["set_xticks"][1][0]
        self.assertEqual(minor, [1])

    def test_linewidths_vary(self):
        fig = RecordingFig()
        date_rates = {
            "2026-01-01": _records((1, 14.0), (365, 15.0)),
            "2026-01-02": _records((1, 14.5), (365, 15.5)),
            "2026-01-03": _records((1, 15.0), (365, 16.0)),
        }
        render_curve_evolution(fig, date_rates)
        widths = [kwargs["linewidth"] for _, kwargs in fig.axes[0].calls["plot"]]
        self.assertEqual(len(widths), 3)
        self.assertAlmostEqual(widths[0], 1.5)
        self.assertAlmostEqual(widths[1], 2.0)
        self.assertAlmostEqual(widths[2], 2.5)


class RenderDetailedEvolutionTest(unittest.TestCase):
    def _date_rates(self):
        return {
            "2026-01-01": _records((1, 14.0), (60, 15.0), (120, 16.0)),
            "2026-01-02": _records((1, 14.5), (60, 15.5), (120, 16.5)),
        }

    def test_plots_two_dates(self):
        fig = RecordingFig()
        render_detailed_evolution(fig, self._date_rates())
        ax = fig.axes[0]
        self.assertEqual(len(ax.calls["plot"]), 2)

    def test_empty_shows_message(self):
        fig = RecordingFig()
        render_detailed_evolution(fig, {})
        self.assertEqual(len(fig.axes), 1)

    def test_empty_xlabel_dias_uteis(self):
        fig = RecordingFig()
        render_detailed_evolution(fig, {})
        self.assertEqual(fig.axes[0]._xlabel, "Dias úteis")
        self.assertEqual(fig.axes[0]._ylabel, "TAXA")

    def test_legend_fontsize(self):
        fig = RecordingFig()
        render_detailed_evolution(fig, self._date_rates())
        self.assertEqual(fig.axes[0]._legend_kwargs["fontsize"], 8)

    def test_plot_has_color_and_width(self):
        fig = RecordingFig()
        render_detailed_evolution(fig, self._date_rates())
        for _, kwargs in fig.axes[0].calls["plot"]:
            self.assertIn("color", kwargs)
            self.assertIn("linewidth", kwargs)
            self.assertIn("label", kwargs)

    def test_detailed_xlim(self):
        fig = RecordingFig()
        render_detailed_evolution(fig, self._date_rates())
        self.assertIn((0, 756), fig.axes[0].calls["set_xlim"])

    def test_detailed_ticks(self):
        fig = RecordingFig()
        date_rates = {
            "2026-01-01": _records((1, 14.0), (66, 15.0), (132, 16.0)),
            "2026-01-02": _records((1, 14.5), (66, 15.5), (132, 16.5)),
        }
        render_detailed_evolution(fig, date_rates)
        ax = fig.axes[0]
        major = ax.calls["set_xticks"][0][0]
        minor = ax.calls["set_xticks"][1][0]
        self.assertEqual(major, [66, 132])
        self.assertEqual(minor, [1])

    def test_detailed_linewidths_vary(self):
        fig = RecordingFig()
        date_rates = {
            "2026-01-01": _records((1, 14.0), (60, 15.0), (120, 16.0)),
            "2026-01-02": _records((1, 14.5), (60, 15.5), (120, 16.5)),
            "2026-01-03": _records((1, 15.0), (60, 16.0), (120, 17.0)),
        }
        render_detailed_evolution(fig, date_rates)
        widths = [kwargs["linewidth"] for _, kwargs in fig.axes[0].calls["plot"]]
        self.assertEqual(len(widths), 3)
        self.assertAlmostEqual(widths[0], 1.5)
        self.assertAlmostEqual(widths[1], 2.0)
        self.assertAlmostEqual(widths[2], 2.5)


if __name__ == "__main__":
    unittest.main()
