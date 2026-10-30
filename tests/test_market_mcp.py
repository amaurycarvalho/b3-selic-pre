"""Testes das tools MCP de mercado, somente leitura."""

from datetime import date, timedelta

from b3_selic_pre.application.market.forecast import FocusExpectation
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    UNIDADE_OURO,
    UNIDADE_USD,
    MarketQuote,
)
from b3_selic_pre.infrastructure.market import build_market_services
from b3_selic_pre.presentation.market_tab import MarketTabController
from b3_selic_pre.presentation.mcp import tool_handlers
from b3_selic_pre.presentation.mcp.catalog import TOOL_DEFINITIONS
from b3_selic_pre.presentation.mcp.context import ToolContext


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
    def fetch_expectations(self):
        return [FocusExpectation(2027, 5.8, 5.4, 6.2)]


class FakeB3:
    def fetch_historical_exchange(self, inicio, fim):
        return []

    def fetch_dol(self, ticker, inicio, fim):
        return [_quote("2026-10-30", 5.5)]


class FakeGold:
    def fetch_series(self):
        return _series(ATIVO_OURO, start=2000.0)


def _setup(tmp_path):
    services = build_market_services(
        tmp_path,
        sgs=FakeSgs(_series(ATIVO_USD)),
        focus=FakeFocus(),
        b3=FakeB3(),
        gold=FakeGold(),
    )
    controller = MarketTabController(services)
    controller.refresh()
    context = ToolContext(
        cache=None,
        settings_factory=lambda: None,
        market_services=services,
    )
    return services, controller, context


def test_catalog_lists_market_tools_as_read_only():
    names = {tool["name"] for tool in TOOL_DEFINITIONS}
    assert {
        "mercado_serie",
        "mercado_previsao",
        "mercado_indicadores",
        "mercado_exportar",
    } <= names
    for tool in TOOL_DEFINITIONS:
        if str(tool["name"]).startswith("mercado_"):
            annotations = tool["annotations"]
            assert annotations["readOnlyHint"] is True
            assert annotations["openWorldHint"] is False
            assert annotations["idempotentHint"] is True


def test_mercado_serie_filters_asset_and_has_provenance(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = tool_handlers.mercado_serie({"ativo": "usd"}, ctx)

    assert result["itens"]
    assert all(item["ativo"] == "usd" for item in result["itens"])
    first = result["itens"][0]
    assert {"data", "valor", "unidade", "origem", "metodo", "extraido_em"} <= set(
        first
    )
    assert "defasado" in first


def test_mercado_serie_paginates(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = tool_handlers.mercado_serie({"limite": 2}, ctx)

    assert len(result["itens"]) == 2
    assert result["nextCursor"]


def test_mercado_serie_invalid_window_and_resolution(tmp_path):
    import pytest

    from b3_selic_pre.application.mcp_services import DomainError
    from b3_selic_pre.presentation.mcp.protocol import InvalidParams

    _, _, ctx = _setup(tmp_path)

    with pytest.raises(DomainError):
        tool_handlers.mercado_serie(
            {"inicio": "2026-12-31", "fim": "2026-01-01"}, ctx
        )
    with pytest.raises(InvalidParams):
        tool_handlers.mercado_serie({"resolucao": "hora"}, ctx)


def test_mercado_previsao_reads_artifact_and_horizon(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = tool_handlers.mercado_previsao(
        {"ativo": "usd", "horizonte": 3}, ctx
    )

    assert list(result["previsao"]) == ["usd"]
    assert len(result["previsao"]["usd"]["itens"]) == 3
    assert result["previsao"]["usd"]["itens"][0]["bandas"]
    assert result["aviso"]


def test_mercado_previsao_without_artifact_is_sem_dados(tmp_path):
    import pytest

    from b3_selic_pre.application.mcp_services import DomainError

    services = build_market_services(
        tmp_path,
        sgs=FakeSgs([]),
        focus=FakeFocus(),
        b3=FakeB3(),
        gold=FakeGold(),
    )
    ctx = ToolContext(
        cache=None, settings_factory=lambda: None, market_services=services
    )

    with pytest.raises(DomainError) as exc:
        tool_handlers.mercado_previsao({}, ctx)
    assert exc.value.motivo == "sem_dados"


def test_mercado_indicadores_returns_signals(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = tool_handlers.mercado_indicadores({}, ctx)

    assert result["vol30"] is not None
    assert result["premio_termo"] is not None
    assert result["data_referencia"]


def test_mercado_indicadores_without_data_is_sem_dados(tmp_path):
    import pytest

    from b3_selic_pre.application.mcp_services import DomainError

    services = build_market_services(
        tmp_path,
        sgs=FakeSgs([]),
        focus=FakeFocus(),
        b3=FakeB3(),
        gold=FakeGold(),
    )
    ctx = ToolContext(
        cache=None, settings_factory=lambda: None, market_services=services
    )

    with pytest.raises(DomainError) as exc:
        tool_handlers.mercado_indicadores({}, ctx)
    assert exc.value.motivo == "sem_dados"


def test_mercado_exportar_csv_and_forecast(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = tool_handlers.mercado_exportar(
        {"formato": "csv", "prever": True}, ctx
    )

    assert result["nome"] == "mercado-historico.csv"
    assert result["content_type"] == "text/csv"
    assert "DATA;ATIVO;VALOR;UNIDADE;ORIGEM;METODO" in result["conteudo"]
    assert "previsao" in result
    assert "DATA;ATIVO;CENARIO" in result["previsao"]["conteudo"]


def test_mercado_exportar_json_and_missing_dates(tmp_path):
    _, _, ctx = _setup(tmp_path)

    result = tool_handlers.mercado_exportar(
        {"formato": "json", "inicio": "2026-10-01", "fim": "2026-10-30"}, ctx
    )

    assert result["nome"] == "mercado.json"
    assert result["content_type"] == "application/json"
    assert '"series"' in result["conteudo"]
    assert isinstance(result["datas_indisponiveis"], list)


def test_market_tools_do_not_write_to_cache(tmp_path):
    services, _, ctx = _setup(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    tool_handlers.mercado_serie({}, ctx)
    tool_handlers.mercado_previsao({}, ctx)
    tool_handlers.mercado_indicadores({}, ctx)
    tool_handlers.mercado_exportar({}, ctx)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert before == after


def test_market_tools_do_not_use_network(tmp_path):
    class Broken:
        def fetch_series(self, *args, **kwargs):
            raise AssertionError("rede não permitida")

        def fetch_historical_exchange(self, *args, **kwargs):
            raise AssertionError("rede não permitida")

        def fetch_dol(self, *args, **kwargs):
            raise AssertionError("rede não permitida")

        def fetch_expectations(self, *args, **kwargs):
            raise AssertionError("rede não permitida")

    services = build_market_services(
        tmp_path, sgs=Broken(), focus=Broken(), b3=Broken(), gold=Broken()
    )
    controller = MarketTabController(services)
    controller.options.resolucao = "auto"
    from b3_selic_pre.presentation.market_tab import GOLD_SOURCE, SGS_SOURCE

    services.raw.write_quotes(SGS_SOURCE, _series(ATIVO_USD))
    services.raw.write_quotes(GOLD_SOURCE, _series(ATIVO_OURO, start=300.0))
    ctx = ToolContext(
        cache=None, settings_factory=lambda: None, market_services=services
    )

    assert tool_handlers.mercado_serie({}, ctx)["itens"]
