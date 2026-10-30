"""Handlers das tools MCP, separados do catálogo e do despacho."""

from __future__ import annotations

from datetime import date

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.tesouro import (
    TesouroDataError,
    agregar_por_titulo,
    build_agregados_payload,
    build_vendas_payload,
    filtrar_por_periodo,
    filtrar_por_titulo,
    ordenar_vendas,
    parse_vendas,
    resolver_periodo,
)
from b3_selic_pre.domain.models import VendaTesouroDireto
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
    data = inputs.resolve_date(args, ctx)
    records = inputs.load_current(data, ctx)
    return mcp_services.curve_payload(
        records,
        data,
        inputs.curva(args),
        inputs.cursor(args),
        inputs.limite(args),
    )


def exportar(
    args: dict[str, object], ctx: ToolContext, representation: str
) -> dict[str, object]:
    """Handle both CSV export tools."""
    data = inputs.resolve_date(args, ctx)
    historical = inputs.load_historical(data, ctx)
    return mcp_services.export_payload(historical, data, representation)


def analise(args: dict[str, object], ctx: ToolContext) -> dict[str, object]:
    """Handle the ``analise`` tool."""
    data = inputs.resolve_date(args, ctx)
    records = inputs.load_current(data, ctx)
    historical = inputs.load_historical(data, ctx)
    return mcp_services.analysis_payload(
        records,
        historical,
        data,
        inputs.curva(args),
        config=inputs.config(ctx),
    )


def evolucao(args: dict[str, object], ctx: ToolContext) -> dict[str, object]:
    """Handle the ``evolucao`` tool."""
    data = inputs.resolve_date(args, ctx)
    historical = inputs.load_historical(data, ctx)
    return mcp_services.evolution_payload(
        historical,
        data,
        inputs.cursor(args),
        inputs.limite(args),
    )


def estatisticas(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``estatisticas`` tool."""
    data = inputs.resolve_date(args, ctx)
    records = inputs.load_current(data, ctx)
    return mcp_services.statistics_payload(
        records, data, config=inputs.config(ctx)
    )


def listar_datas(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``listar_datas`` tool."""
    return mcp_services.dates_payload(
        ctx.cache.list_entries(),
        inputs.cursor(args),
        inputs.limite(args),
    )


def _tesouro_date(args: dict[str, object], key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidParams(f"{key} deve ser uma string AAAA-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise mcp_services.DomainError(
            "data_invalida",
            f"Data inválida '{value}'.",
            "Use uma data no formato AAAA-MM-DD.",
        ) from exc
    if parsed.isoformat() != value:
        raise mcp_services.DomainError(
            "data_invalida",
            f"Data inválida '{value}'.",
            "Use uma data no formato AAAA-MM-DD.",
        )
    return value


def _tesouro_bool(args: dict[str, object], key: str) -> bool:
    value = args.get(key, False)
    if not isinstance(value, bool):
        raise InvalidParams(f"{key} deve ser um booleano")
    return value


def _tesouro_titulo(args: dict[str, object]) -> str | None:
    value = args.get("titulo")
    if value is not None and not isinstance(value, str):
        raise InvalidParams("titulo deve ser uma string")
    return value


def _load_tesouro(
    ctx: ToolContext,
) -> tuple[list[VendaTesouroDireto], dict[str, object]]:
    cache = ctx.tesouro_cache
    if cache is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há cache de vendas do Tesouro disponível.",
            "Execute `b3-selic-pre tesouro` para preparar o cache.",
        )
    read = cache.read
    cached = read(read_only=True)
    if cached is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há cache válido de vendas do Tesouro.",
            "Execute `b3-selic-pre tesouro` para preparar o cache.",
        )
    try:
        return parse_vendas(cached[0]), cached[1]
    except TesouroDataError as exc:
        raise mcp_services.DomainError(
            "dados_invalidos",
            str(exc),
            "Execute `b3-selic-pre tesouro --no-cache` para atualizar o cache.",
        ) from exc


def tesouro_vendas(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``tesouro_vendas`` read-only cache tool."""
    sales, metadata = _load_tesouro(ctx)
    inicio = _tesouro_date(args, "inicio")
    fim = _tesouro_date(args, "fim")
    if inicio is not None and fim is not None and inicio > fim:
        raise mcp_services.DomainError(
            "periodo_invalido",
            "inicio não pode ser maior que fim.",
            "Informe um período com inicio <= fim.",
        )
    period = resolver_periodo(sales, inicio, fim)
    filtered = ordenar_vendas(
        filtrar_por_periodo(
            filtrar_por_titulo(sales, _tesouro_titulo(args)),
            period[0],
            period[1],
        )
    )
    periodo = {"inicio": period[0], "fim": period[1]}
    if _tesouro_bool(args, "agregar"):
        aggregates = agregar_por_titulo(filtered)
        page, next_cursor = mcp_services.paginate(
            aggregates, inputs.cursor(args), inputs.limite(args)
        )
        payload = build_agregados_payload(
            page,
            metadata,
            periodo,
            len(filtered),
            dataset="vendas",
            include_fonte=False,
        )
    else:
        page, next_cursor = mcp_services.paginate(
            filtered, inputs.cursor(args), inputs.limite(args)
        )
        payload = build_vendas_payload(
            page,
            metadata,
            periodo,
            dataset="vendas",
            include_fonte=False,
        )
        payload["total_registros"] = len(filtered)
    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    return payload
