"""Testes headless do controlador, view-model e dados de gráfico."""

import ast
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from b3_selic_pre.application.market.forecast import FocusExpectation
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    UNIDADE_OURO,
    UNIDADE_USD,
    MarketQuote,
)
from b3_selic_pre.infrastructure.market import build_market_services
from b3_selic_pre.presentation.charts_market import render_market
from b3_selic_pre.presentation.market_chart_data import (
    build_chart_data,
    indicators_text,
)
from b3_selic_pre.presentation.market_tab import (
    GOLD_SOURCE,
    SGS_SOURCE,
    MarketTabController,
    derive_gold_series,
    dol_ticker,
)
from b3_selic_pre.presentation.market_view_model import (
    MarketOptions,
    build_view_model,
)


def _quote(data, valor, ativo=ATIVO_USD, **overrides):
    values = {
        "data": data,
        "ativo": ativo,
        "valor": valor,
        "unidade": UNIDADE_USD if ativo == ATIVO_USD else UNIDADE_OURO,
        "origem": "teste",
        "metodo": "oficial",
        "extraido_em": "2026-10-30T12:00:00+00:00",
    }
    values.update(overrides)
    return MarketQuote(**values)


def _series(ativo, days=100, start=5.0):
    base = date(2026, 10, 30)
    return [
        _quote(
            (base - timedelta(days=index)).isoformat(),
            start + (days - index) * 0.01,
            ativo=ativo,
        )
        for index in range(days)
    ]


class FakeSgs:
    def __init__(self, quotes):
        self.quotes = quotes

    def fetch_series(self, inicio, fim):
        return [quote for quote in self.quotes if inicio <= quote.data <= fim]


class FakeFocus:
    def __init__(self, expectations):
        self.expectations = expectations

    def fetch_expectations(self):
        return self.expectations


class FakeB3:
    def __init__(self, history=None, dol=None):
        self.history = history or []
        self.dol = dol or []

    def fetch_historical_exchange(self, inicio, fim):
        return [quote for quote in self.history if inicio <= quote.data <= fim]

    def fetch_dol(self, ticker, inicio, fim):
        return [quote for quote in self.dol if inicio <= quote.data <= fim]


class FakeGold:
    def __init__(self, quotes=None, fail=False):
        self.quotes = quotes or []
        self.fail = fail

    def fetch_series(self):
        if self.fail:
            raise OSError("sem rede")
        return self.quotes


def _controller(tmp_path, **fake_overrides):
    services = build_market_services(
        tmp_path,
        sgs=fake_overrides.get("sgs", FakeSgs([])),
        focus=fake_overrides.get("focus", FakeFocus([])),
        b3=fake_overrides.get("b3", FakeB3()),
        gold=fake_overrides.get("gold", FakeGold()),
    )
    return MarketTabController(services), services


def _populate(services):
    usd = _series(ATIVO_USD)
    gold = _series(ATIVO_OURO, start=300.0)
    services.raw.write_quotes(SGS_SOURCE, usd)
    services.raw.write_quotes(GOLD_SOURCE, gold)
    services.raw.write_document(
        "bcb_focus",
        "focus.json",
        {"expectations": [{"ano": 2027, "mediana": 5.8, "minimo": 5.4, "maximo": 6.2}]},
    )
    return usd, gold


def test_controller_loads_cache_only_without_network(tmp_path):
    controller, services = _controller(tmp_path)
    _populate(services)

    payload = controller.load_cache_only()

    assert payload["series"][ATIVO_USD]["itens"]
    assert payload["series"][ATIVO_OURO]["itens"]
    assert payload["previsao"][ATIVO_USD]["cenario"] == "Cenário de mercado"
    assert payload["origem"] == "Cache"


def test_controller_empty_cache_reports_no_data(tmp_path):
    controller, _ = _controller(tmp_path)

    payload = controller.load_cache_only()

    assert payload["series"] == {}
    assert build_view_model(payload).empty_message


def test_controller_refresh_fetches_sources_and_precomputes(tmp_path):
    xau = _series(ATIVO_OURO, start=2000.0)
    sgs = FakeSgs(_series(ATIVO_USD))
    controller, services = _controller(
        tmp_path,
        sgs=sgs,
        focus=FakeFocus([FocusExpectation(2027, 5.8, 5.4, 6.2)]),
        b3=FakeB3(dol=[_quote("2026-10-30", 5.5)]),
        gold=FakeGold(xau),
    )

    payload = controller.refresh()

    assert payload["series"][ATIVO_USD]["itens"]
    assert payload["series"][ATIVO_OURO]["itens"]
    assert controller._precompute().read_artifact(controller._key()) is not None
    assert payload["erros_fontes"] == []


def test_controller_refresh_keeps_partial_data_on_source_failure(tmp_path):
    controller, services = _controller(
        tmp_path,
        sgs=FakeSgs(_series(ATIVO_USD)),
        gold=FakeGold(fail=True),
    )

    payload = controller.refresh()

    assert payload["series"][ATIVO_USD]["itens"]
    assert any("Yahoo GC=F" in error for error in payload["erros_fontes"])


def test_controller_refresh_records_focus_failure(tmp_path):
    class BrokenFocus:
        def fetch_expectations(self):
            raise OSError("focus fora")

    controller, _ = _controller(
        tmp_path, sgs=FakeSgs(_series(ATIVO_USD)), focus=BrokenFocus()
    )

    payload = controller.refresh()

    assert any("BCB Focus" in error for error in payload["erros_fontes"])


def test_second_execution_reuses_derived_and_precomputed(tmp_path, monkeypatch):
    controller, services = _controller(
        tmp_path,
        sgs=FakeSgs(_series(ATIVO_USD)),
        gold=FakeGold(_series(ATIVO_OURO, start=2000.0)),
    )
    first = controller.refresh()
    key = controller._key()

    assert services.precompute.read_derived(key) is not None
    assert services.precompute.read_artifact(key) is not None
    calls = []
    monkeypatch.setattr(
        controller, "_build_payload", lambda *a, **k: calls.append(1) or {}
    )

    second = controller.load_cache_only()

    assert calls == []
    assert second["series"] == first["series"]


def test_refresh_preserves_previous_artifact_on_precompute_failure(
    tmp_path, monkeypatch
):
    xau = _series(ATIVO_OURO, start=2000.0)
    controller, services = _controller(
        tmp_path,
        sgs=FakeSgs(_series(ATIVO_USD)),
        gold=FakeGold(xau),
    )
    controller.refresh()
    old_key = controller._key()
    assert services.precompute.read_artifact(old_key) is not None

    def fail(*args, **kwargs):
        raise RuntimeError("disco cheio")

    monkeypatch.setattr(services.precompute, "_write_json", fail)
    services.raw.write_quote(SGS_SOURCE, _quote("2026-10-31", 5.9))

    payload = controller.refresh()

    assert payload["series"][ATIVO_USD]["itens"]
    assert services.precompute.read_artifact(old_key) is not None


def test_derive_gold_series_uses_nearest_previous_usd():
    usd = [_quote("2026-10-01", 5.0), _quote("2026-10-05", 5.1)]
    xau = [_quote("2026-10-02", 2000.0, ativo=ATIVO_OURO)]

    derived = derive_gold_series(usd, xau)

    assert derived[0].valor == 2000.0 * 5.0 / 31.1034768


def test_dol_ticker_advances_one_month():
    assert dol_ticker(date(2026, 10, 30)) == "DOLX26"
    assert dol_ticker(date(2026, 12, 15)) == "DOLF27"


def test_view_model_status_and_stale_badge():
    payload = {
        "janela": {"inicio": "2026-01-01", "fim": "2026-10-30"},
        "series": {
            ATIVO_USD: {
                "defasado": True,
                "itens": [{"data": "2026-10-30", "defasagem_horas": 5.0}],
            }
        },
        "previsao": {},
        "indicadores": {},
        "origem": "Cache",
        "extraido_em": "2026-10-30T12:00:00",
    }

    view = build_view_model(payload)

    assert view.has_data
    assert view.is_stale
    assert view.stale_badge == "Dados defasados"
    assert "5.0 h" in view.status_text
    assert view.available_assets == (ATIVO_USD,)


def test_view_model_empty_and_options():
    view = build_view_model({"series": {}, "previsao": {}})
    options = MarketOptions()

    assert not view.has_data
    assert view.empty_message
    options.set_ativo("usd")
    options.set_ativo("invalido")
    assert options.ativo == "usd"
    options.toggle_base100()
    options.toggle_fibonacci()
    assert options.base100
    assert options.fibonacci


def _payload():
    usd = [
        {"data": "2026-01-01", "valor": 5.0, "minimo": 4.8, "maximo": 5.2},
        {"data": "2026-06-01", "valor": 5.5, "minimo": 5.3, "maximo": 5.7},
    ]
    gold = [
        {"data": "2026-01-01", "valor": 300.0, "minimo": 290.0, "maximo": 310.0},
        {"data": "2026-06-01", "valor": 330.0, "minimo": 320.0, "maximo": 340.0},
    ]
    return {
        "janela": {"inicio": "2026-01-01", "fim": "2026-10-30"},
        "series": {
            ATIVO_USD: {"unidade": UNIDADE_USD, "itens": usd, "defasado": False},
            ATIVO_OURO: {"unidade": UNIDADE_OURO, "itens": gold, "defasado": False},
        },
        "previsao": {
            ATIVO_USD: {
                "itens": [
                    {
                        "data": "2026-11-30",
                        "centro": 5.6,
                        "bandas": [
                            {"nivel": 80, "inferior": 5.4, "superior": 5.8},
                            {"nivel": 95, "inferior": 5.2, "superior": 6.0},
                        ],
                    }
                ]
            }
        },
        "indicadores": {
            "premio_termo": 10.0,
            "vol30": 12.0,
            "regime": True,
            "limiar_regime": 1.5,
        },
    }


def test_chart_data_stacks_panels_and_uses_ranges():
    data = build_chart_data(_payload())

    assert [panel.ativo for panel in data.paineis] == [ATIVO_USD, ATIVO_OURO]
    usd = data.painel(ATIVO_USD)
    assert usd.minimos == (4.8, 5.3)
    assert usd.previsao_datas == ("2026-11-30",)
    assert usd.bandas[0].nivel == 80
    assert "Prêmio a termo" in data.indicadores_texto
    assert "Regime: ligado" in data.indicadores_texto


def test_chart_data_base100_and_fibonacci():
    options = MarketOptions(base100=True, fibonacci=True)
    data = build_chart_data(_payload(), options)

    usd = data.painel(ATIVO_USD)
    assert usd.valores[0] == 100.0
    assert usd.previsao_centro[0] == 100.0 * 5.6 / 5.0
    assert usd.fibonacci is not None
    assert usd.fibonacci[50.0] == 105.0


def test_chart_data_empty_and_asset_filter():
    empty = build_chart_data({"series": {}, "previsao": {}})
    assert empty.vazio

    data = build_chart_data(_payload(), MarketOptions(ativo="ouro"))
    assert [panel.ativo for panel in data.paineis] == [ATIVO_OURO]


def test_chart_data_without_fibonacci_has_no_levels():
    data = build_chart_data(_payload())

    assert data.painel(ATIVO_USD).fibonacci is None


def test_indicators_text_omits_missing_values():
    text = indicators_text({"indicadores": {}})

    assert "Prêmio a termo: -" in text
    assert "Regime: -" in text


def test_render_market_smoke_without_display():
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    data = build_chart_data(_payload())
    figure = Figure()
    render_market(figure, data)

    assert figure.axes
    usd_hover = getattr(figure.axes[0], "_hover_points", [])
    assert usd_hover
    assert "Dólar" in usd_hover[0][2]
    assert "BRL/USD" in usd_hover[0][2]
    assert any("cenário" in point[2] for point in usd_hover)
    assert any("Banda 80%" in point[2] for point in usd_hover)
    assert getattr(figure.axes[1], "_hover_points", [])

    empty = build_chart_data({"series": {}, "previsao": {}})
    empty_figure = Figure()
    render_market(empty_figure, empty)
    assert empty_figure.axes


def test_shell_registers_cambio_between_tesouro_and_sobre():
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "b3_selic_pre"
        / "presentation"
        / "gui"
        / "shell.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register_tab"
    ]
    labels = [
        call.args[1].value
        for call in calls
        if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant)
    ]

    assert labels == [
        "SELIC Pré",
        "Tesouro Direto",
        "Câmbio e Ouro",
        "Feriados",
        "Sobre",
    ]


def test_market_gui_declares_lazy_sub_tabs_in_order():
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
    assert "load_cache_only" in source
    assert "controller.refresh" in source


def test_launch_wires_market_services():
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "b3_selic_pre"
        / "presentation"
        / "gui"
        / "launch.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    keywords = {
        keyword.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "GuiDependencies"
        for keyword in node.keywords
    }

    assert "market_services" in keywords
