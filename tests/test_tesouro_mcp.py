import io
import json
from decimal import Decimal
from unittest import mock

import pytest

from b3_selic_pre.application import mcp_services
from b3_selic_pre.infrastructure.disk_cache import DiskCache
from b3_selic_pre.infrastructure.tesouro_cache import TesouroCache
from b3_selic_pre.presentation.mcp.catalog import TOOL_NAMES
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.server import McpServer
from b3_selic_pre.presentation.mcp.tool_handlers import tesouro_vendas

HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;"
    "PU;Quantidade;Valor"
)
CSV = (
    HEADER
    + "\n"
    + "Tesouro Selic 2029;02/01/2029;01/10/2026;15.000,00;2,00;30.000,00\n"
    + "Tesouro IPCA+ 2035;15/05/2035;02/10/2026;3.000,00;1,00;3.000,00\n"
    + "Tesouro Selic 2029;02/01/2029;01/10/2026;14.000,00;3,00;42.000,00\n"
).encode()
META = {
    "_meta": {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    }
}


def _metadata():
    return {
        "schema_version": 1,
        "dataset_name": "vendas-do-tesouro-direto",
        "dataset_id": "dataset-id",
        "resource_id": "resource-id",
        "resource_url": "https://example.test/vendas.csv",
        "etag": "etag-1",
        "last_modified": "2026-10-16T10:29:05",
        "downloaded_at": "2026-10-20T00:00:00+00:00",
        "checked_at": "2026-10-20T00:00:00+00:00",
        "size_bytes": len(CSV),
        "sha256": "abc",
        "row_count": 3,
        "first_data_date": "2026-10-01",
        "last_data_date": "2026-10-02",
    }


def _cache(tmp_path, data=CSV):
    cache = TesouroCache(tmp_path)
    cache.save(data, _metadata())
    return cache


def _context(cache):
    return ToolContext(
        cache=mock.Mock(),
        settings_factory=lambda: None,
        tesouro_cache=cache,
    )


class TestTesouroTool:
    def test_catalog_contains_tool(self):
        assert "tesouro_vendas" in TOOL_NAMES

    def test_structured_response(self, tmp_path):
        payload = tesouro_vendas({}, _context(_cache(tmp_path)))

        assert payload["dataset"] == "vendas"
        assert payload["origem"] == "cache"
        assert payload["total_registros"] == 3
        assert len(payload["registros"]) == 3
        assert payload["registros"][0]["pu"] == "3000.000000"

    def test_filters_and_period(self, tmp_path):
        payload = tesouro_vendas(
            {
                "titulo": "selic",
                "inicio": "2026-10-01",
                "fim": "2026-10-01",
            },
            _context(_cache(tmp_path)),
        )

        assert payload["total_registros"] == 2
        assert all("Selic" in item["tipo_titulo"] for item in payload["registros"])

    def test_aggregation(self, tmp_path):
        payload = tesouro_vendas(
            {"agregar": True}, _context(_cache(tmp_path))
        )

        assert payload["total_agregados"] == 2
        assert payload["total_registros"] == 3
        assert "registros" not in payload

    def test_pagination(self, tmp_path):
        payload = tesouro_vendas(
            {"limite": 1}, _context(_cache(tmp_path))
        )

        assert len(payload["registros"]) == 1
        assert "nextCursor" in payload

    def test_empty_period(self, tmp_path):
        payload = tesouro_vendas(
            {"inicio": "2025-01-01", "fim": "2025-01-02"},
            _context(_cache(tmp_path)),
        )

        assert payload["registros"] == []
        assert payload["total_registros"] == 0

    def test_cache_vazio(self, tmp_path):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_vendas({}, _context(TesouroCache(tmp_path)))

        assert exc.value.motivo == "cache_vazio"
        assert "b3-selic-pre tesouro" in exc.value.dica

    def test_missing_cache_dependency(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_vendas({}, _context(None))

        assert exc.value.motivo == "cache_vazio"

    @pytest.mark.parametrize("value", ["2026-02-30", "02/10/2026", "2026-2-01"])
    def test_invalid_date(self, tmp_path, value):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_vendas(
                {"inicio": value}, _context(_cache(tmp_path))
            )

        assert exc.value.motivo == "data_invalida"

    def test_inverted_period(self, tmp_path):
        with pytest.raises(mcp_services.DomainError) as exc:
            tesouro_vendas(
                {"inicio": "2026-10-02", "fim": "2026-10-01"},
                _context(_cache(tmp_path)),
            )

        assert exc.value.motivo == "periodo_invalido"

    def test_does_not_touch_network_cache(self, tmp_path):
        cache = _cache(tmp_path)
        cache.read = mock.Mock(wraps=cache.read)
        tesouro_vendas({}, _context(cache))

        cache.read.assert_called_once_with(read_only=True)


def _run(lines, tesouro_cache):
    inp = io.StringIO("\n".join(lines) + "\n")
    out = io.StringIO()
    McpServer(
        cache=DiskCache(),
        settings_factory=lambda: None,
        tesouro_cache=tesouro_cache,
    ).run(input_stream=inp, output_stream=out)
    return [json.loads(line) for line in out.getvalue().splitlines()]


def _line(method, params, request_id):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
    )


class TestTesouroMcpServer:
    def test_tools_list_includes_tesouro(self, tmp_path):
        messages = _run(
            [_line("tools/list", META, 1)], _cache(tmp_path)
        )

        names = {tool["name"] for tool in messages[0]["result"]["tools"]}
        assert "tesouro_vendas" in names

    def test_tool_call_returns_structured_content(self, tmp_path):
        messages = _run(
            [
                _line(
                    "tools/call",
                    {
                        **META,
                        "name": "tesouro_vendas",
                        "arguments": {},
                    },
                    1,
                )
            ],
            _cache(tmp_path),
        )

        payload = messages[0]["result"]["structuredContent"]
        assert payload["dataset"] == "vendas"

    def test_invalid_cursor_is_invalid_params(self, tmp_path):
        messages = _run(
            [
                _line(
                    "tools/call",
                    {
                        **META,
                        "name": "tesouro_vendas",
                        "arguments": {"cursor": "bad"},
                    },
                    1,
                )
            ],
            _cache(tmp_path),
        )

        assert messages[0]["error"]["code"] == -32602
