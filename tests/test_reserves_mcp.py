"""Testes das tools MCP de reservas, somente leitura."""

from datetime import date, timedelta

import pytest

from b3_selic_pre.application.mcp_services import DomainError
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import FONTE_RESERVAS, UNIDADE_RESERVAS
from b3_selic_pre.infrastructure.reserves import build_reserves_services
from b3_selic_pre.presentation.mcp import reserves_handlers as handlers
from b3_selic_pre.presentation.mcp.catalog import TOOL_DEFINITIONS
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.protocol import InvalidParams
from b3_selic_pre.presentation.reserves_tab import ReservesTabController


class FakeSource:
    def __init__(self, points):
        self.points = points

    def fetch_series(self, inicio, fim):
        return [point for point in self.points if inicio <= point.data <= fim]


class BrokenSource:
    def fetch_series(self, *args, **kwargs):
        raise AssertionError("rede não permitida")


class _Clock:
    def __call__(self):
        from datetime import datetime

        return datetime.fromisoformat("2026-10-30T12:00:00+00:00")


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


def _setup(tmp_path, points=None):
    services = build_reserves_services(
        tmp_path, source=FakeSource(points or _series())
    )
    controller = ReservesTabController(services, now=_Clock())
    controller.refresh()
    context = ToolContext(
        cache=None,
        settings_factory=lambda: None,
        reserves_services=services,
    )
    return services, controller, context


def test_catalog_lists_reserves_tools_as_read_only():
    names = {tool["name"] for tool in TOOL_DEFINITIONS}
    assert {
        "reservas_serie",
        "reservas_indicadores",
        "reservas_exportar",
    } <= names
    for tool in TOOL_DEFINITIONS:
        if str(tool["name"]).startswith("reservas_"):
            annotations = tool["annotations"]
            assert annotations["readOnlyHint"] is True
            assert annotations["openWorldHint"] is False
            assert annotations["idempotentHint"] is True


def test_reservas_serie_filters_window_and_has_provenance(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = handlers.reservas_serie({}, ctx)

    assert result["itens"]
    assert result["janela"]["fim"] == "2026-10-30"
    first = result["itens"][0]
    assert {
        "data",
        "valor",
        "unidade",
        "origem",
        "metodo",
        "extraido_em",
        "defasado",
    } <= set(first)


def test_reservas_serie_three_years_and_pagination(tmp_path):
    _, _, ctx = _setup(tmp_path)

    twelve = handlers.reservas_serie({"limite": 500}, ctx)
    three = handlers.reservas_serie({"janela": "3a", "limite": 500}, ctx)
    page = handlers.reservas_serie({"limite": 3}, ctx)

    assert len(twelve["itens"]) < len(three["itens"])
    assert len(page["itens"]) == 3
    assert page["nextCursor"]


def test_reservas_serie_invalid_inputs(tmp_path):
    _, _, ctx = _setup(tmp_path)

    with pytest.raises(DomainError):
        handlers.reservas_serie(
            {"inicio": "2026-12-31", "fim": "2026-01-01"}, ctx
        )
    with pytest.raises(InvalidParams):
        handlers.reservas_serie({"janela": "5a"}, ctx)


def test_reservas_indicadores_returns_metrics_and_regime(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = handlers.reservas_indicadores({}, ctx)

    assert result["nivel_atual"] is not None
    assert result["var_3m"] is not None
    assert result["regime"] in ("aumento", "estavel", "deterioracao")
    assert result["limiares"]


def test_reservas_indicadores_sem_dados(tmp_path):
    services = build_reserves_services(tmp_path, source=FakeSource([]))
    ctx = ToolContext(
        cache=None,
        settings_factory=lambda: None,
        reserves_services=services,
    )

    with pytest.raises(DomainError) as exc:
        handlers.reservas_indicadores({}, ctx)
    assert exc.value.motivo == "sem_dados"


def test_reservas_exportar_csv_and_json(tmp_path):
    _, _, ctx = _setup(tmp_path)

    csv = handlers.reservas_exportar({"formato": "csv"}, ctx)
    as_json = handlers.reservas_exportar({"formato": "json"}, ctx)

    assert csv["nome"] == "reservas-serie.csv"
    assert csv["content_type"] == "text/csv"
    assert csv["conteudo"].startswith("DATA;VALOR;UNIDADE;ORIGEM;METODO")
    assert as_json["nome"] == "reservas.json"
    assert as_json["content_type"] == "application/json"
    assert '"indicadores"' in as_json["conteudo"]
    assert isinstance(as_json["datas_indisponiveis"], list)


def test_reservas_exportar_missing_dates(tmp_path):
    points = [_quote("2026-10-01", 350000.0), _quote("2026-10-30", 360000.0)]
    _, _, ctx = _setup(tmp_path, points=points)

    result = handlers.reservas_exportar(
        {"inicio": "2026-10-01", "fim": "2026-10-30"}, ctx
    )

    assert result["datas_indisponiveis"]
    assert all(date.fromisoformat(day).weekday() < 5
               for day in result["datas_indisponiveis"])


def test_reservas_exportar_sem_dados(tmp_path):
    services, _, ctx = _setup(tmp_path)
    ctx.reserves_services = build_reserves_services(
        tmp_path / "vazio", source=FakeSource([])
    )

    with pytest.raises(DomainError) as exc:
        handlers.reservas_exportar({}, ctx)
    assert exc.value.motivo == "sem_dados"


def test_reserves_tools_do_not_write_or_use_network(tmp_path):
    services, _, ctx = _setup(tmp_path)
    services.source = BrokenSource()
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    handlers.reservas_serie({}, ctx)
    handlers.reservas_indicadores({}, ctx)
    handlers.reservas_exportar({}, ctx)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert before == after
