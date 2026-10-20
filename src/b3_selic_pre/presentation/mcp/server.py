"""Loop JSON-RPC e despacho de tools do servidor MCP via stdio."""

from __future__ import annotations

import json
import logging
import sys
import threading
from typing import TextIO

from b3_selic_pre.presentation.mcp import protocol
from b3_selic_pre.presentation.mcp.dispatch import Dispatcher

logger = logging.getLogger(__name__)


class McpServer:
    """Servidor MCP stateless sobre newline-delimited JSON-RPC."""

    def __init__(
        self: McpServer,
        cache: object,
        settings_factory: object,
    ) -> None:
        """Crie o servidor com o cache somente leitura injetado."""
        self._dispatcher = Dispatcher(cache, settings_factory)
        self._out: TextIO | None = None
        self._write_lock = threading.Lock()
        self._pending: dict[tuple[str, object], threading.Event] = {}
        self._pending_lock = threading.Lock()
        self._threads: list[threading.Thread] = []

    def run(
        self: McpServer,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> int:
        """Read JSON-RPC messages until EOF and return exit code 0."""
        input_stream = input_stream or sys.stdin
        old_stdout = sys.stdout
        self._out = output_stream or old_stdout
        sys.stdout = sys.stderr
        try:
            for line in input_stream:
                line = line.strip()
                if not line:
                    continue
                self._handle_line(line)
        finally:
            for thread in list(self._threads):
                thread.join(timeout=2.0)
            sys.stdout = old_stdout
            self._out = None
        return 0

    def _handle_line(self: McpServer, line: str) -> None:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            self._write(
                protocol.error_response(
                    None, protocol.PARSE_ERROR, "Parse error"
                )
            )
            return
        if isinstance(message, list):
            self._write(
                protocol.error_response(
                    None,
                    protocol.INVALID_REQUEST,
                    "Batch requests are not supported",
                )
            )
            return
        if not isinstance(message, dict) or not isinstance(
            message.get("method"), str
        ):
            self._write(
                protocol.error_response(
                    message.get("id") if isinstance(message, dict) else None,
                    protocol.INVALID_REQUEST,
                    "Invalid request",
                )
            )
            return
        method = message["method"]
        if method == "notifications/cancelled":
            self._cancel(message.get("params"))
            return
        if "id" not in message:
            return
        key = self._request_key(message.get("id"))
        event = threading.Event()
        if key is not None:
            with self._pending_lock:
                self._pending[key] = event
        thread = threading.Thread(
            target=self._process,
            args=(message, event, key),
            daemon=True,
        )
        self._threads.append(thread)
        thread.start()

    @staticmethod
    def _request_key(request_id: object) -> tuple[str, object] | None:
        try:
            hash(request_id)
        except TypeError:
            return None
        return (type(request_id).__name__, request_id)

    def _cancel(self: McpServer, params: object) -> None:
        if not isinstance(params, dict):
            return
        key = self._request_key(params.get("requestId"))
        if key is None:
            return
        with self._pending_lock:
            event = self._pending.get(key)
        if event is not None:
            event.set()

    def _process(
        self: McpServer,
        message: dict[str, object],
        event: threading.Event,
        key: tuple[str, object] | None,
    ) -> None:
        request_id = message.get("id")
        try:
            if event.is_set():
                return
            try:
                payload = self._dispatcher.dispatch(message, event)
            except protocol.JsonRpcError as exc:
                if not event.is_set():
                    self._write(
                        protocol.error_response(
                            request_id, exc.code, exc.message, exc.data
                        )
                    )
                return
            except Exception:
                logger.exception("Falha interna ao processar requisição MCP")
                if event.is_set():
                    return
                if message.get("method") == "tools/call":
                    payload = protocol.tool_result(
                        {
                            "motivo": "erro_interno",
                            "detalhe": "Falha interna ao executar a tool.",
                            "dica": "Consulte o stderr do servidor.",
                        },
                        is_error=True,
                    )
                    self._write(
                        protocol.success_response(request_id, payload)
                    )
                else:
                    self._write(
                        protocol.error_response(
                            request_id,
                            protocol.INTERNAL_ERROR,
                            "Internal error",
                        )
                    )
                return
            if not event.is_set():
                self._write(protocol.success_response(request_id, payload))
        finally:
            if key is not None:
                with self._pending_lock:
                    self._pending.pop(key, None)

    def _write(self: McpServer, message: dict[str, object]) -> None:
        if self._out is None:
            return
        line = json.dumps(message, ensure_ascii=False)
        with self._write_lock:
            self._out.write(line + "\n")
            self._out.flush()


def serve(cache: object, settings_factory: object) -> int:
    """Run an MCP server with the given read-only cache."""
    return McpServer(cache=cache, settings_factory=settings_factory).run()
