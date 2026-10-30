"""Handlers MCP da curva, da janela de evolução e da análise."""

from __future__ import annotations

from b3_selic_pre.application import mcp_services
from b3_selic_pre.presentation.mcp import tool_inputs as inputs
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.protocol import InvalidParams


def data_referencia(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``data_referencia`` tool."""
    if args:
        raise InvalidParams("data_referencia não aceita argumentos")
    date, origem, disponivel = inputs.reference(ctx)
    cached_at = None
    for entry in ctx.cache.list_entries():
        if entry.date == date:
            cached_at = entry.cached_at
            break
    return mcp_services.reference_payload(
        date, origem, disponivel, cached_at=cached_at
    )


def consultar_curva(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``consultar_curva`` tool."""
    resolution = inputs.resolve_business_day(args, ctx)
    data = str(resolution.data_resolvida)
    records = inputs.load_current(data, ctx)
    payload = mcp_services.curve_payload(
        records,
        data,
        inputs.curva(args),
        inputs.cursor(args),
        inputs.limite(args),
    )
    payload.update(inputs.adjustment_fields(resolution))
    return payload


def exportar(
    args: dict[str, object], ctx: ToolContext, representation: str
) -> dict[str, object]:
    """Handle both CSV export tools."""
    resolution = inputs.resolve_business_day(args, ctx)
    data = str(resolution.data_resolvida)
    historical = inputs.load_historical(data, ctx)
    payload = mcp_services.export_payload(historical, data, representation)
    payload.update(inputs.adjustment_fields(resolution))
    return payload


def analise(args: dict[str, object], ctx: ToolContext) -> dict[str, object]:
    """Handle the ``analise`` tool."""
    resolution = inputs.resolve_business_day(args, ctx)
    data = str(resolution.data_resolvida)
    records = inputs.load_current(data, ctx)
    historical = inputs.load_historical(data, ctx)
    payload = mcp_services.analysis_payload(
        records,
        historical,
        data,
        inputs.curva(args),
        config=inputs.config(ctx),
    )
    payload.update(inputs.adjustment_fields(resolution))
    return payload


def evolucao(args: dict[str, object], ctx: ToolContext) -> dict[str, object]:
    """Handle the ``evolucao`` tool."""
    resolution = inputs.resolve_business_day(args, ctx)
    data = str(resolution.data_resolvida)
    historical = inputs.load_historical(data, ctx)
    payload = mcp_services.evolution_payload(
        historical,
        data,
        inputs.cursor(args),
        inputs.limite(args),
    )
    payload.update(inputs.adjustment_fields(resolution))
    return payload


def estatisticas(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``estatisticas`` tool."""
    resolution = inputs.resolve_business_day(args, ctx)
    data = str(resolution.data_resolvida)
    records = inputs.load_current(data, ctx)
    payload = mcp_services.statistics_payload(
        records, data, config=inputs.config(ctx)
    )
    payload.update(inputs.adjustment_fields(resolution))
    return payload


def listar_datas(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``listar_datas`` tool."""
    return mcp_services.dates_payload(
        ctx.cache.list_entries(),
        inputs.cursor(args),
        inputs.limite(args),
    )


__all__ = [
    "analise",
    "consultar_curva",
    "data_referencia",
    "estatisticas",
    "evolucao",
    "exportar",
    "listar_datas",
]
