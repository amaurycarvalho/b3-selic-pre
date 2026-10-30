import pytest

from b3_selic_pre.application import mcp_services
from b3_selic_pre.presentation.mcp import tools
from b3_selic_pre.presentation.mcp.catalog import (
    TOOL_DEFINITIONS,
    TOOL_NAMES,
)
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.dispatch import Dispatcher
from b3_selic_pre.presentation.mcp.protocol import InvalidParams
from b3_selic_pre.presentation.mcp.tool_handlers import (
    tesouro_estoque,
    tesouro_resgates,
)

RECOMPRA_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade;Valor\n"
    "Tesouro Selic 2029;02/01/2029;01/10/2026;2,00;30.000,00\n"
    "Tesouro Selic 2029;02/01/2029;01/10/2026;3,00;42.000,00\n"
).encode()
CUPOM_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor\n"
    "Tesouro IPCA+ 2035;15/05/2035;02/10/2026;3.000,00;1,00;3.000,00\n"
).encode()
VENCIMENTO_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor\n"
    "Tesouro Selic 2029;02/01/2029;03/10/2026;15.000,00;1,00;15.000,00\n"
).encode()
ESTOQUE_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;"
    "Valor Estoque\n"
    "Tesouro Selic 2029;02/01/2029;09/2026;15.000,00;2,00;30.000,00\n"
    "Tesouro Selic 2029;02/01/2029;09/2026;14.000,00;3,00;42.000,00\n"
    "Tesouro IPCA+ 2035;15/05/2035;08/2026;3.000,00;1,00;3.000,00\n"
).encode()
CSVS = {
    "recompra": RECOMPRA_CSV,
    "cupom": CUPOM_CSV,
    "vencimento": VENCIMENTO_CSV,
    "estoque": ESTOQUE_CSV,
}


def _metadata(key):
    return {
        "schema_version": 1,
        "dataset_name": "dataset",
        "dataset_id": "dataset-id",
        "resource_id": f"id-{key}",
        "resource_url": "https://example.test/file.csv",
        "etag": "etag",
        "last_modified": "2026-10-16T10:29:05",
        "downloaded_at": "2026-10-20T00:00:00+00:00",
        "checked_at": "2026-10-20T00:00:00+00:00",
        "size_bytes": 10,
        "sha256": "abc",
        "row_count": 1,
        "first_data_date": "2026-08",
        "last_data_date": "2026-10-03",
    }


class FakeCache:
    def __init__(self, data=None, metadata=None):
        self.data = data
        self.metadata = metadata
        self.reads = []

    def read(self, read_only=True):
        self.reads.append(read_only)
        if self.data is None:
            return None
        return self.data, self.metadata


class Factory:
    def __init__(self, caches):
        self.caches = caches
        self.requested = []

    def __call__(self, key):
        self.requested.append(key)
        return self.caches.get(key, FakeCache())


def _context(caches=None, factory=None):
    return ToolContext(
        cache=object(),
        settings_factory=object,
        tesouro_cache_factory=factory or Factory(caches or {}),
    )


def _resgates_context():
    caches = {
        key: FakeCache(CSVS[key], _metadata(key))
        for key in ("recompra", "cupom", "vencimento")
    }
    return _context(caches)


def _estoque_context(data=ESTOQUE_CSV):
    return _context({"estoque": FakeCache(data, _metadata("estoque"))})


class TestCatalog:
    def test_tools_are_in_catalog_as_read_only(self):
        names = {tool["name"] for tool in TOOL_DEFINITIONS}
        assert "tesouro_resgates" in names
        assert "tesouro_estoque" in names
        assert names == TOOL_NAMES
        for tool in TOOL_DEFINITIONS:
            assert tool["annotations"]["readOnlyHint"] is True
            assert tool["annotations"]["openWorldHint"] is False
            assert tool["annotations"]["idempotentHint"] is True


class TestResgatesTool:
    def test_payload_uses_cache(self):
        ctx = _resgates_context()
        payload = tesouro_resgates({}, ctx)

        assert payload["dataset"] == "resgates"
        assert payload["origem"] == "cache"
        assert payload["total_registros"] == 4
        assert len(payload["registros"]) == 4
        assert all(
            cache.reads == [True] for cache in ctx.tesouro_cache_factory.caches.values()
        )

    def test_tipo_filter(self):
        payload = tesouro_resgates({"tipo": "cupom"}, _resgates_context())
        assert [item["tipo_resgate"] for item in payload["registros"]] == [
            "cupom"
        ]

    def test_titulo_filter(self):
        payload = tesouro_resgates({"titulo": "ipca"}, _resgates_context())
        assert {item["tipo_titulo"] for item in payload["registros"]} == {
            "Tesouro IPCA+ 2035"
        }

    def test_default_period(self):
        payload = tesouro_resgates({}, _resgates_context())
        assert payload["periodo"] == {
            "inicio": "2026-09-03",
            "fim": "2026-10-03",
        }

    def test_aggregation(self):
        payload = tesouro_resgates({"agregar": True}, _resgates_context())
        assert "agregados" in payload
        assert "registros" not in payload
        recompra = next(
            item
            for item in payload["agregados"]
            if item["tipo_resgate"] == "recompra"
        )
        assert recompra["pu_medio"] == ""

    def test_pagination_returns_cursor(self):
        payload = tesouro_resgates({"limite": 1}, _resgates_context())
        assert len(payload["registros"]) == 1
        assert "nextCursor" in payload
        assert payload["total_registros"] == 4

    def test_empty_period(self):
        payload = tesouro_resgates(
            {"inicio": "2030-01-01", "fim": "2030-01-02"},
            _resgates_context(),
        )
        assert payload["registros"] == []
        assert payload["total_registros"] == 0

    def test_invalid_cursor(self):
        with pytest.raises(ValueError):
            tesouro_resgates({"cursor": "not-a-cursor"}, _resgates_context())

    def test_invalid_period(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_resgates(
                {"inicio": "2026-10-02", "fim": "2026-10-01"},
                _resgates_context(),
            )
        assert exc.value.payload()["motivo"] == "periodo_invalido"

    def test_invalid_tipo(self):
        with pytest.raises(InvalidParams):
            tesouro_resgates({"tipo": "outro"}, _resgates_context())

    def test_cache_vazio_when_no_cache(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_resgates({}, _context({}))
        payload = exc.value.payload()
        assert payload["motivo"] == "cache_vazio"
        assert "tesouro-resgates" in payload["dica"]

    def test_cache_vazio_without_factory(self):
        ctx = ToolContext(cache=object(), settings_factory=object)
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_resgates({}, ctx)
        assert exc.value.payload()["motivo"] == "cache_vazio"

    def test_invalid_cached_data(self):
        caches = {
            key: FakeCache(b"bad", _metadata(key))
            for key in ("recompra", "cupom", "vencimento")
        }
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_resgates({}, _context(caches))
        assert exc.value.payload()["motivo"] == "dados_invalidos"

    def test_catalog_dispatch(self):
        ctx = _resgates_context()
        payload = tools.call_tool("tesouro_resgates", {}, ctx)
        assert payload["dataset"] == "resgates"


class TestEstoqueTool:
    def test_default_last_month(self):
        payload = tesouro_estoque({}, _estoque_context())
        assert payload["dataset"] == "estoque"
        assert payload["origem"] == "cache"
        assert {item["mes"] for item in payload["registros"]} == {"2026-09"}

    def test_interval(self):
        payload = tesouro_estoque(
            {"inicio": "2026-08", "fim": "2026-09"}, _estoque_context()
        )
        assert {item["mes"] for item in payload["registros"]} == {
            "2026-08",
            "2026-09",
        }

    def test_mes(self):
        payload = tesouro_estoque({"mes": "2026-08"}, _estoque_context())
        assert {item["mes"] for item in payload["registros"]} == {"2026-08"}

    def test_aggregation_single_month(self):
        payload = tesouro_estoque(
            {"mes": "2026-09", "agregar": True}, _estoque_context()
        )
        assert "agregados" in payload
        assert payload["agregados"][0]["quantidade"] == "5.00"

    def test_aggregation_multiple_months_is_error(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_estoque(
                {"inicio": "2026-08", "fim": "2026-09", "agregar": True},
                _estoque_context(),
            )
        assert exc.value.payload()["motivo"] == "periodo_invalido"

    def test_pagination_returns_cursor(self):
        payload = tesouro_estoque({"limite": 1}, _estoque_context())
        assert len(payload["registros"]) == 1
        assert "nextCursor" in payload

    def test_empty_period(self):
        payload = tesouro_estoque(
            {"inicio": "2030-01", "fim": "2030-02"}, _estoque_context()
        )
        assert payload["registros"] == []
        assert payload["total_registros"] == 0

    def test_cache_vazio(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_estoque({}, _context({}))
        payload = exc.value.payload()
        assert payload["motivo"] == "cache_vazio"
        assert "tesouro-estoque" in payload["dica"]

    def test_invalid_month(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_estoque({"mes": "2026-13"}, _estoque_context())
        assert exc.value.payload()["motivo"] == "periodo_invalido"

    def test_invalid_cached_data(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_estoque({}, _estoque_context(b"bad"))
        assert exc.value.payload()["motivo"] == "dados_invalidos"

    def test_catalog_dispatch(self):
        payload = tools.call_tool("tesouro_estoque", {}, _estoque_context())
        assert payload["dataset"] == "estoque"


class TestComposition:
    def test_dispatcher_injects_tesouro_factory(self):
        caches = {
            key: FakeCache(CSVS[key], _metadata(key))
            for key in ("recompra", "cupom", "vencimento")
        }
        dispatcher = Dispatcher(
            cache=object(),
            settings_factory=object,
            tesouro_cache_factory=Factory(caches),
        )
        result = dispatcher._call_tool(
            {"name": "tesouro_resgates", "arguments": {}}, None
        )
        payload = result["structuredContent"]
        assert payload["dataset"] == "resgates"
