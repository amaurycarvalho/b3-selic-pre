import io
import json
import tempfile
import threading
from contextlib import redirect_stderr
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.disk_cache import DiskCache
from b3_selic_pre.presentation.mcp import tools as tool_module
from b3_selic_pre.presentation.mcp.server import McpServer

META = {
    "_meta": {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    }
}


class _Settings:
    def __init__(self, data=None):
        self.data = data or {}

    def get(self, key, default=None):
        return self.data.get(key, default)


def _business_day(value):
    while value.weekday() >= 5:
        value -= timedelta(days=1)
    return value


def _today():
    today = _business_day(datetime.now(timezone.utc).date())
    return today.isoformat()


def _days_ago(days):
    today = datetime.strptime(_today(), "%Y-%m-%d").date()
    return (today - timedelta(days=days)).isoformat()


def _records(*rates):
    return [
        RateRecord(day252=i + 1, day360=(i + 1) * 30, rate=str(rate))
        for i, rate in enumerate(rates)
    ]


def _populate(cache):
    today = _today()
    cache.put(today, _records(10.0, 11.0, 12.0))
    cache.put(_days_ago(7), _records(9.0, 10.0, 11.0))
    return today


def _line(method, params, request_id):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
    )


def _run(lines, cache, settings):
    inp = io.StringIO("\n".join(lines) + "\n")
    out = io.StringIO()
    code = McpServer(
        cache=cache,
        settings_factory=lambda: settings,
    ).run(input_stream=inp, output_stream=out)
    messages = [json.loads(line) for line in out.getvalue().splitlines()]
    return code, messages


def _call(name, arguments, request_id, meta=None):
    params = {**(meta or META), "name": name, "arguments": arguments}
    return _line("tools/call", params, request_id)


class TestProtocol:
    def test_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            _, messages = _run(
                [_line("server/discover", META, 1)], cache, _Settings()
            )
        result = messages[0]["result"]
        assert result["supportedVersions"] == ["2026-07-28"]
        assert result["capabilities"] == {"tools": {}}
        assert result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == (
            "b3-selic-pre"
        )

    def test_missing_meta_is_invalid_params(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_line("server/discover", {}, 1)], DiskCache(tmp), _Settings()
            )
        assert messages[0]["error"]["code"] == -32602

    def test_unsupported_version(self):
        meta = {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": "1900-01-01",
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_line("server/discover", meta, 1)], DiskCache(tmp), _Settings()
            )
        error = messages[0]["error"]
        assert error["code"] == -32022
        assert error["data"]["supported"] == ["2026-07-28"]

    def test_initialize_is_rejected_with_supported_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_line("initialize", {}, 1)], DiskCache(tmp), _Settings()
            )
        error = messages[0]["error"]
        assert error["code"] == -32601
        assert "2026-07-28" in error["message"]

    def test_parse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = io.StringIO("{bad json}\n")
            out = io.StringIO()
            McpServer(DiskCache(tmp), _Settings).run(inp, out)
        message = json.loads(out.getvalue().splitlines()[0])
        assert message["error"]["code"] == -32700

    def test_unknown_method(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_line("unknown/method", META, 1)], DiskCache(tmp), _Settings()
            )
        assert messages[0]["error"]["code"] == -32601


class TestToolsCatalog:
    def test_catalog_has_exactly_eight_read_only_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_line("tools/list", META, 1)], DiskCache(tmp), _Settings()
            )
        tools = messages[0]["result"]["tools"]
        assert {tool["name"] for tool in tools} == {
            "data_referencia",
            "consultar_curva",
            "exportar_curva_curta",
            "exportar_curva_longa",
            "analise",
            "evolucao",
            "estatisticas",
            "listar_datas",
        }
        for tool in tools:
            assert tool["annotations"]["readOnlyHint"] is True
            assert tool["annotations"]["openWorldHint"] is False

    def test_invalid_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [
                    _line(
                        "tools/list",
                        {**META, "cursor": "bad"},
                        1,
                    )
                ],
                DiskCache(tmp),
                _Settings(),
            )
        assert messages[0]["error"]["code"] == -32602

    def test_unknown_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_call("nope", {}, 1)], DiskCache(tmp), _Settings()
            )
        assert messages[0]["error"]["code"] == -32602


class TestTools:
    def test_data_referencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [_call("data_referencia", {}, 1)],
                cache,
                _Settings({"data_referencia": today}),
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload["data_referencia"] == today
        assert payload["disponivel"] is True

    def test_data_referencia_cache_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [_call("data_referencia", {}, 1)], cache, _Settings()
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload["data_referencia"] == today
        assert payload["origem"] == "cache"

    def test_data_referencia_cache_vazio(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_call("data_referencia", {}, 1)],
                DiskCache(tmp),
                _Settings(),
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload["motivo"] == "cache_vazio"
        assert "isError" not in messages[0]["result"]

    def test_consultar_curta(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [_call("consultar_curva", {"data": today}, 1)],
                cache,
                _Settings({"data_referencia": today}),
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload["curva"] == "curta"
        assert payload["itens"][0]["taxa"] == 10.0

    def test_consultar_longa(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [
                    _call(
                        "consultar_curva",
                        {"data": today, "curva": "longa"},
                        1,
                    )
                ],
                cache,
                _Settings({"data_referencia": today}),
            )
        items = messages[0]["result"]["structuredContent"]["itens"]
        assert items[0]["ano"] == 0
        assert "taxa_media" in items[0]

    def test_consultar_data_antiga(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_call("consultar_curva", {"data": "2020-01-01"}, 1)],
                DiskCache(tmp),
                _Settings(),
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload["motivo"] == "data_antiga"

    def test_consultar_sem_dados(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [_call("consultar_curva", {"data": _days_ago(1)}, 1)],
                cache,
                _Settings({"data_referencia": today}),
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload["motivo"] == "sem_dados"

    def test_exportar_curta_e_longa(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [
                    _call("exportar_curva_curta", {"data": today}, 1),
                    _call("exportar_curva_longa", {"data": today}, 2),
                ],
                cache,
                _Settings({"data_referencia": today}),
            )
        by_id = {message["id"]: message for message in messages}
        assert "DATA;DU252;DC365;TAXA" in (
            by_id[1]["result"]["structuredContent"]["conteudo"]
        )
        assert "DATA;ANO;TAXA_MEDIA" in (
            by_id[2]["result"]["structuredContent"]["conteudo"]
        )

    def test_analise_curta_e_longa(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [
                    _call("analise", {"data": today}, 1),
                    _call("analise", {"data": today, "curva": "longa"}, 2),
                ],
                cache,
                _Settings({"data_referencia": today}),
            )
        by_id = {message["id"]: message for message in messages}
        assert by_id[1]["result"]["structuredContent"]["curva"] == "curta"
        assert by_id[2]["result"]["structuredContent"]["curva"] == "longa"
        assert "Curva Longa" in (
            by_id[2]["result"]["structuredContent"]["texto"]
        )

    def test_evolucao_e_estatisticas_e_datas(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DiskCache(tmp)
            today = _populate(cache)
            _, messages = _run(
                [
                    _call("evolucao", {"data": today}, 1),
                    _call("estatisticas", {"data": today}, 2),
                    _call("listar_datas", {}, 3),
                ],
                cache,
                _Settings({"data_referencia": today}),
            )
        by_id = {message["id"]: message for message in messages}
        assert by_id[1]["result"]["structuredContent"]["itens"]
        assert by_id[2]["result"]["structuredContent"]["total_registros"] == 3
        assert len(by_id[3]["result"]["structuredContent"]["itens"]) == 2

    def test_empty_cache_listar_datas_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, messages = _run(
                [_call("listar_datas", {}, 1)],
                DiskCache(tmp),
                _Settings(),
            )
        payload = messages[0]["result"]["structuredContent"]
        assert payload == {"itens": []}


class TestResilience:
    def test_internal_error_keeps_server_alive(self):
        calls = [RuntimeError("boom"), {"ok": True}]

        def fake_call(*args, **kwargs):
            value = calls.pop(0)
            if isinstance(value, Exception):
                raise value
            return value

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(tool_module, "call_tool", side_effect=fake_call):
                _, messages = _run(
                    [
                        _call("data_referencia", {}, 1),
                        _call("data_referencia", {}, 2),
                    ],
                    DiskCache(tmp),
                    _Settings(),
                )
        by_id = {message["id"]: message for message in messages}
        assert by_id[1]["result"]["isError"] is True
        assert by_id[2]["result"]["structuredContent"] == {"ok": True}

    def test_cancelled_request_has_no_response(self):
        started = threading.Event()
        release = threading.Event()

        def slow_call(*args, **kwargs):
            started.set()
            release.wait(timeout=2)
            return {"ok": True}

        class Stream:
            def __iter__(self):
                yield _call("data_referencia", {}, 1)
                started.wait(timeout=2)
                yield _line(
                    "notifications/cancelled",
                    {"requestId": 1},
                    None,
                )
                release.set()
                yield _line("server/discover", META, 2)

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(tool_module, "call_tool", side_effect=slow_call):
                out = io.StringIO()
                McpServer(DiskCache(tmp), _Settings).run(Stream(), out)
        messages = [json.loads(line) for line in out.getvalue().splitlines()]
        assert not any(message.get("id") == 1 for message in messages)
        assert any(message.get("id") == 2 for message in messages)

    def test_stdout_is_clean_even_if_tool_prints(self):
        def noisy_call(*args, **kwargs):
            print("noise")
            return {"ok": True}

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(tool_module, "call_tool", side_effect=noisy_call):
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    _, messages = _run(
                        [_call("data_referencia", {}, 1)],
                        DiskCache(tmp),
                        _Settings(),
                    )
        assert all("jsonrpc" in message for message in messages)
        assert "noise" in stderr.getvalue()

    def test_eof_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            code = McpServer(DiskCache(tmp), _Settings).run(
                io.StringIO(""), out
            )
        assert code == 0
        assert out.getvalue() == ""
