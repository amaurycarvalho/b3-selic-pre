"""Testes headless do controlador, view-model e gráfico de reservas."""

from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure

from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import FONTE_RESERVAS, UNIDADE_RESERVAS
from b3_selic_pre.application.reserves.config import ReservesConfig
from b3_selic_pre.infrastructure.reserves import build_reserves_services
from b3_selic_pre.presentation.charts_reserves import render_reserves
from b3_selic_pre.presentation.reserves_chart_data import (
    build_chart_data,
    moving_average,
)
from b3_selic_pre.presentation.reserves_tab import (
    RESERVES_SOURCE,
    ReservesTabController,
)
from b3_selic_pre.presentation.reserves_view_model import (
    ReservesOptions,
    build_view_model,
)


class FakeSource:
    def __init__(self, points=None, fail=False):
        self.points = points or []
        self.fail = fail
        self.calls = []

    def fetch_series(self, inicio, fim):
        self.calls.append((inicio, fim))
        if self.fail:
            raise OSError("sem rede")
        return [point for point in self.points if inicio <= point.data <= fim]


def _quote(day, value):
    return MarketQuote(
        data=day,
        ativo="reservas",
        valor=value,
        unidade=UNIDADE_RESERVAS,
        origem=FONTE_RESERVAS,
        metodo="oficial",
        extraido_em="2026-10-30T12:00:00+00:00",
    )


def _series(days=425, start="2025-09-01", base=300000.0):
    first = date.fromisoformat(start)
    return [
        _quote(
            (first + timedelta(days=index)).isoformat(),
            base + index * 100,
        )
        for index in range(days)
    ]


class _Clock:
    def __init__(self, value="2026-10-30T12:00:00+00:00"):
        self.value = datetime.fromisoformat(value)

    def __call__(self):
        return self.value


def _controller(tmp_path, points=None, fail=False, now=None):
    source = FakeSource(points, fail)
    services = build_reserves_services(tmp_path, source=source)
    return (
        ReservesTabController(services, now=now or _Clock()),
        services,
        source,
    )


def test_cache_only_empty_returns_empty_state_without_network(tmp_path):
    controller, _, source = _controller(tmp_path, fail=True)

    payload = controller.load_cache_only()

    assert payload["serie"]["itens"] == []
    assert payload["latest_data_date"] is None
    assert source.calls == []
    assert build_view_model(payload).empty_message


def test_cache_only_builds_from_snapshot_without_network(tmp_path):
    controller, services, source = _controller(tmp_path, fail=True)
    points = _series()
    services.raw.write_snapshot(
        RESERVES_SOURCE, points, source=FONTE_RESERVAS
    )

    payload = controller.load_cache_only()

    assert payload["serie"]["itens"]
    assert payload["latest_data_date"] == points[-1].data
    assert payload["indicadores"]["regime"]
    assert source.calls == []
    assert services.precompute.read_artifact(payload["hash"]) is None


def test_refresh_fetches_persists_and_reuses_artifact(tmp_path, monkeypatch):
    points = _series()
    controller, services, source = _controller(tmp_path, points=points)

    first = controller.refresh()

    assert source.calls
    assert first["serie"]["itens"]
    assert first["erros_fontes"] == []
    assert services.raw.read_snapshot(RESERVES_SOURCE) is not None
    artifact = services.precompute.read_artifact(first["hash"])
    assert artifact is not None

    calls = []
    monkeypatch.setattr(
        controller,
        "_build_payload",
        lambda *args, **kwargs: calls.append(1) or {},
    )

    second = controller.load_cache_only()

    assert calls == []
    assert second["serie"] == first["serie"]


def test_refresh_invalidates_artifact_on_value_or_parameter_change(tmp_path):
    points = _series()
    controller, services, _ = _controller(tmp_path, points=points)
    first = controller.refresh()
    old_key = first["hash"]

    revised = [*points[:-1], _quote(points[-1].data, 999999.0)]
    controller.services.source = FakeSource(revised)
    second = controller.refresh()

    assert second["hash"] != old_key
    assert services.precompute.read_artifact(second["hash"]) is not None
    assert services.precompute.read_artifact(old_key) is not None

    controller.config = ReservesConfig.from_mapping(
        {"limiares": {"var_aumento": 5.0}}
    )
    third = controller.refresh()

    assert third["hash"] != second["hash"]


def test_refresh_keeps_previous_artifact_on_precompute_failure(
    tmp_path, monkeypatch
):
    points = _series()
    controller, services, _ = _controller(tmp_path, points=points)
    first = controller.refresh()
    old_key = first["hash"]

    def fail(*args, **kwargs):
        raise RuntimeError("disco cheio")

    monkeypatch.setattr(services.precompute, "_write_json", fail)
    controller.services.source = FakeSource(
        [*points[:-1], _quote(points[-1].data, 999999.0)]
    )

    payload = controller.refresh()

    assert payload["serie"]["itens"]
    assert services.precompute.read_artifact(old_key) is not None


def test_refresh_keeps_previous_state_on_network_failure(tmp_path):
    points = _series()
    controller, services, _ = _controller(tmp_path, points=points)
    controller.refresh()

    failing = FakeSource(fail=True)
    controller.services.source = failing

    payload = controller.refresh()

    assert payload["serie"]["itens"]
    assert any("BCB SGS" in error for error in payload["erros_fontes"])


def test_refresh_prunes_old_points_outside_retention(tmp_path):
    old = _quote("2019-01-01", 1.0)
    points = [old, *_series(days=30)]
    controller, services, _ = _controller(tmp_path, points=points)

    controller.refresh()

    snapshot = services.raw.read_snapshot_points(RESERVES_SOURCE)
    assert old.data not in {point.data for point in snapshot}


def test_view_model_status_regime_and_staleness(tmp_path):
    controller, _, _ = _controller(tmp_path, points=_series())
    payload = controller.refresh()

    current = build_view_model(
        payload, now=datetime(2026, 10, 30, 12, 0)
    )
    assert current.has_data
    assert current.regime is not None
    assert current.regime_badge
    assert current.thresholds_text
    assert current.status_kind == "success"
    assert not current.stale_badge

    stale = build_view_model(
        payload, now=datetime(2026, 12, 30, 12, 0)
    )
    assert stale.stale_badge == "Dados defasados"
    assert stale.status_kind == "warning"


def test_chart_data_windows_averages_and_extremos(tmp_path):
    points = _series()
    controller, _, _ = _controller(tmp_path, points=points)
    payload = controller.refresh()

    twelve = build_chart_data(
        payload, ReservesOptions(janela="12m"), datetime(2026, 10, 30)
    )
    three = build_chart_data(
        payload, ReservesOptions(janela="3a"), datetime(2026, 10, 30)
    )

    assert len(twelve.datas) < len(three.datas)
    assert twelve.minimo is not None
    assert twelve.maximo is not None
    assert twelve.maximo > twelve.minimo
    assert len(twelve.medias_30) == len(twelve.datas)
    assert len(twelve.medias_90) == len(twelve.datas)
    assert twelve.regime_label
    assert not twelve.vazio


def test_moving_average_is_trailing_and_deterministic():
    points = [
        ("2026-10-01", 10.0),
        ("2026-10-02", 20.0),
        ("2026-10-03", 30.0),
    ]
    values = moving_average(points, 2)

    assert values == (10.0, 15.0, 25.0)


def test_chart_empty_state():
    data = build_chart_data({"serie": {"itens": []}}, ReservesOptions())

    assert data.vazio
    assert data.mensagem
    figure = Figure()
    render_reserves(figure, data)
    assert figure.axes


def test_render_reserves_smoke_without_display(tmp_path):
    controller, _, _ = _controller(tmp_path, points=_series())
    payload = controller.refresh()
    data = build_chart_data(payload, ReservesOptions("3a"))
    figure = Figure()

    render_reserves(figure, data)

    assert figure.axes
    assert (
        figure.axes[0].get_title(loc="left") == "Reservas Internacionais"
    )
    hover = getattr(figure.axes[0], "_hover_points", [])
    assert hover
    assert "Reservas" in hover[0][2]
    assert "US$ bilhões" in hover[0][2]
    assert "Média 30d" in hover[0][2]


def test_gui_registers_reserves_after_dolar():
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "b3_selic_pre"
        / "presentation"
        / "gui"
        / "market_tab.py"
    )
    source = path.read_text(encoding="utf-8")

    assert '("dolar-ouro", "Dólar e Ouro")' in source
    assert '("reservas", "Reservas Internacionais")' in source
    assert source.index('"dolar-ouro"') < source.index('"reservas"')
    assert "ReservesSubTab" in source
    assert "load_cache_only" in source


def test_reserves_orientation_sections_cover_the_sub_tab():
    import ast

    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "b3_selic_pre"
        / "presentation"
        / "gui"
        / "reserves_orientation.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id in ("ORIENTATION_SECTIONS", "TEXT_WIDTH"):
            values[target.id] = ast.literal_eval(node.value)
    ORIENTATION_SECTIONS = values["ORIENTATION_SECTIONS"]
    TEXT_WIDTH = values["TEXT_WIDTH"]

    titles = [title for title, _ in ORIENTATION_SECTIONS]
    body = " ".join(text for _, text in ORIENTATION_SECTIONS)

    assert titles == [
        "Objetivo",
        "Responde a pergunta",
        "Indicadores envolvidos",
        "Como interpretar",
    ]
    assert "BCB SGS 13621" in body
    assert "médias móveis" in body
    assert "não uma recomendação" in body
    assert TEXT_WIDTH == 29


def test_reserves_sub_tab_wires_orientation_textbox():
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "b3_selic_pre"
        / "presentation"
        / "gui"
        / "reserves_sub_tab.py"
    )
    source = path.read_text(encoding="utf-8")

    assert "build_reserves_orientation" in source
    assert "ttk.PanedWindow" in source
    assert "self.paned.add(charts, weight=4)" in source
    assert "self.paned.add(orientation, weight=1)" in source
