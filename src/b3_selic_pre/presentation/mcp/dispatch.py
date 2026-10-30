"""Despacho dos métodos MCP e das chamadas de tools."""

from __future__ import annotations

from b3_selic_pre.application import mcp_services
from b3_selic_pre.presentation.mcp import protocol
from b3_selic_pre.presentation.mcp import tools as tool_module
from b3_selic_pre.presentation.mcp.catalog import (
    TOOL_DEFINITIONS,
    TOOL_NAMES,
)

INSTRUCTIONS = (
    "Servidor somente leitura das taxas referenciais SELIC Pré. "
    "Atende apenas com dados do cache local; não acessa a B3 ou a CVM "
    "durante as chamadas. Use data_referencia e listar_datas para descobrir "
    "o que está disponível. Para vendas do Tesouro Direto, use tesouro_vendas "
    "após preparar o cache com `b3-selic-pre tesouro`."
)


class Dispatcher:
    """Executa métodos de protocolo e tools, devolvendo resultados MCP."""

    def __init__(
        self: Dispatcher,
        cache: object,
        settings_factory: object,
        tesouro_cache: object | None = None,
        tesouro_cache_factory: object | None = None,
        market_services: object | None = None,
        reserves_services: object | None = None,
        holiday_cache: object | None = None,
        calendar_service: object | None = None,
    ) -> None:
        """Crie o dispatcher com o cache e a fábrica de settings."""
        self.cache = cache
        self.settings_factory = settings_factory
        self.tesouro_cache = tesouro_cache
        self.tesouro_cache_factory = tesouro_cache_factory
        self.market_services = market_services
        self.reserves_services = reserves_services
        self.holiday_cache = holiday_cache
        self.calendar_service = calendar_service

    def dispatch(
        self: Dispatcher,
        message: dict[str, object],
        event: object,
    ) -> dict[str, object]:
        """Dispatch one request to the matching protocol method."""
        method = message.get("method")
        params = message.get("params")
        if method == "initialize":
            raise protocol.initialize_error()
        if method not in ("server/discover", "tools/list", "tools/call"):
            raise protocol.JsonRpcError(
                protocol.METHOD_NOT_FOUND,
                f"Method not found: {method}",
            )
        protocol.validate_meta(params)
        if method == "server/discover":
            return protocol.discover_result(INSTRUCTIONS)
        if method == "tools/list":
            return self._list_tools(params)
        return self._call_tool(params, event)

    @staticmethod
    def _list_tools(params: object) -> dict[str, object]:
        cursor = params.get("cursor") if isinstance(params, dict) else None
        try:
            page, next_cursor = mcp_services.paginate(
                TOOL_DEFINITIONS, cursor, None
            )
        except ValueError as exc:
            raise protocol.InvalidParams(str(exc)) from exc
        payload: dict[str, object] = {"tools": page}
        if next_cursor is not None:
            payload["nextCursor"] = next_cursor
        return protocol.result(payload)

    def _call_tool(
        self: Dispatcher,
        params: object,
        event: object,
    ) -> dict[str, object]:
        if not isinstance(params, dict):
            raise protocol.InvalidParams("params deve ser um objeto")
        name = params.get("name")
        if not isinstance(name, str):
            raise protocol.InvalidParams("name obrigatório")
        if name not in TOOL_NAMES:
            raise protocol.InvalidParams(f"Unknown tool: {name}")
        context = tool_module.ToolContext(
            cache=self.cache,
            settings_factory=self.settings_factory,
            tesouro_cache=self.tesouro_cache,
            tesouro_cache_factory=self.tesouro_cache_factory,
            market_services=self.market_services,
            reserves_services=self.reserves_services,
            holiday_cache=self.holiday_cache,
            calendar_service=self.calendar_service,
        )
        try:
            payload = tool_module.call_tool(
                name,
                params.get("arguments"),
                context,
                event,
            )
        except mcp_services.DomainError as exc:
            return protocol.tool_result(exc.payload(), is_error=False)
        except protocol.JsonRpcError:
            raise
        except ValueError as exc:
            raise protocol.InvalidParams(str(exc)) from exc
        return protocol.tool_result(payload)
