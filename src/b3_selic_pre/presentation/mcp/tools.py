"""Despacho das tools MCP para os handlers especializados."""

from __future__ import annotations

from collections.abc import Callable

from b3_selic_pre.presentation.mcp.catalog import TOOL_NAMES
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.curve_handlers import (
    analise,
    consultar_curva,
    data_referencia,
    estatisticas,
    evolucao,
    exportar,
    listar_datas,
)
from b3_selic_pre.presentation.mcp.feriados_handlers import (
    feriados_consultar,
    feriados_exportar,
    feriados_listar,
)
from b3_selic_pre.presentation.mcp.protocol import InvalidParams
from b3_selic_pre.presentation.mcp.reserves_handlers import (
    reservas_exportar,
    reservas_indicadores,
    reservas_serie,
)
from b3_selic_pre.presentation.mcp.tool_handlers import (
    mercado_exportar,
    mercado_indicadores,
    mercado_previsao,
    mercado_serie,
    tesouro_estoque,
    tesouro_resgates,
    tesouro_vendas,
)
from b3_selic_pre.presentation.mcp.tool_inputs import arguments

Handler = Callable[[dict[str, object], ToolContext], dict[str, object]]

_HANDLERS: dict[str, Handler] = {
    "data_referencia": data_referencia,
    "consultar_curva": consultar_curva,
    "exportar_curva_curta": lambda args, ctx: exportar(args, ctx, "curta"),
    "exportar_curva_longa": lambda args, ctx: exportar(args, ctx, "longa"),
    "analise": analise,
    "evolucao": evolucao,
    "estatisticas": estatisticas,
    "listar_datas": listar_datas,
    "tesouro_vendas": tesouro_vendas,
    "tesouro_resgates": tesouro_resgates,
    "tesouro_estoque": tesouro_estoque,
    "mercado_serie": mercado_serie,
    "mercado_previsao": mercado_previsao,
    "mercado_indicadores": mercado_indicadores,
    "mercado_exportar": mercado_exportar,
    "reservas_serie": reservas_serie,
    "reservas_indicadores": reservas_indicadores,
    "reservas_exportar": reservas_exportar,
    "feriados_listar": feriados_listar,
    "feriados_consultar": feriados_consultar,
    "feriados_exportar": feriados_exportar,
}


def call_tool(
    name: str,
    raw_arguments: object,
    ctx: ToolContext,
    cancel_event: object | None = None,
) -> dict[str, object]:
    """Execute a tool by name and return its structured payload."""
    if name not in TOOL_NAMES:
        raise InvalidParams(f"Unknown tool: {name}")
    args = arguments(raw_arguments)
    if cancel_event is not None and cancel_event.is_set():
        return {}
    return _HANDLERS[name](args, ctx)
