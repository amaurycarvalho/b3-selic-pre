"""Handlers das tools MCP, separados do catálogo e do despacho."""

from __future__ import annotations

from datetime import date

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.tesouro import (
    RESGATE_KEYS,
    PeriodoInvalidoError,
    TesouroDataError,
    agregar_estoque,
    agregar_por_titulo,
    agregar_resgates,
    build_agregados_payload,
    build_estoque_agregados_payload,
    build_estoque_payload,
    build_resgates_agregados_payload,
    build_resgates_payload,
    build_vendas_payload,
    combine_metadata,
    filtrar_estoque_por_periodo,
    filtrar_estoque_por_titulo,
    filtrar_por_periodo,
    filtrar_por_titulo,
    filtrar_resgates_por_periodo,
    filtrar_resgates_por_tipo,
    filtrar_resgates_por_titulo,
    meses_presentes,
    ordenar_estoque,
    ordenar_resgates,
    ordenar_vendas,
    parse_estoque,
    parse_resgates,
    parse_vendas,
    resolver_periodo,
    resolver_periodo_estoque,
    resolver_periodo_resgates,
    validar_meses,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)
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


def _tesouro_month(args: dict[str, object], key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidParams(f"{key} deve ser uma string AAAA-MM")
    try:
        validar_meses(value, None)
    except PeriodoInvalidoError as exc:
        raise mcp_services.DomainError(
            "periodo_invalido",
            str(exc),
            "Use um mês no formato AAAA-MM.",
        ) from exc
    return value


def _tesouro_tipo(args: dict[str, object]) -> str | None:
    value = args.get("tipo")
    if value is None:
        return None
    if value not in ("recompra", "cupom", "vencimento"):
        raise InvalidParams(
            "tipo deve ser 'recompra', 'cupom' ou 'vencimento'"
        )
    return value


def _cache_factory(ctx: ToolContext) -> object:
    factory = ctx.tesouro_cache_factory
    if factory is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há leitor de cache do Tesouro disponível.",
            "Reinicie o servidor MCP para preparar o leitor de cache.",
        )
    return factory


def _load_resgates(
    ctx: ToolContext,
) -> tuple[list[ResgateTesouroDireto], dict[str, object]]:
    factory = _cache_factory(ctx)
    records: list[ResgateTesouroDireto] = []
    metadata: dict[str, dict[str, object]] = {}
    for key in RESGATE_KEYS:
        cache = factory(key)  # type: ignore[operator]
        cached = cache.read(read_only=True)  # type: ignore[attr-defined]
        if cached is None:
            continue
        try:
            records.extend(parse_resgates(cached[0], key))
        except TesouroDataError as exc:
            raise mcp_services.DomainError(
                "dados_invalidos",
                str(exc),
                "Execute `b3-selic-pre tesouro-resgates --no-cache` "
                "para atualizar o cache.",
            ) from exc
        metadata[key] = cached[1]
    if not metadata:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há cache de resgates do Tesouro disponível.",
            "Execute `b3-selic-pre tesouro-resgates` para preparar o cache.",
        )
    return records, combine_metadata(metadata)


def _load_estoque(
    ctx: ToolContext,
) -> tuple[list[EstoqueTesouroDireto], dict[str, object]]:
    factory = _cache_factory(ctx)
    cache = factory("estoque")  # type: ignore[operator]
    cached = cache.read(read_only=True)  # type: ignore[attr-defined]
    if cached is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há cache de estoque do Tesouro disponível.",
            "Execute `b3-selic-pre tesouro-estoque` para preparar o cache.",
        )
    try:
        return parse_estoque(cached[0]), cached[1]
    except TesouroDataError as exc:
        raise mcp_services.DomainError(
            "dados_invalidos",
            str(exc),
            "Execute `b3-selic-pre tesouro-estoque --no-cache` "
            "para atualizar o cache.",
        ) from exc


def tesouro_resgates(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``tesouro_resgates`` read-only cache tool."""
    records, metadata = _load_resgates(ctx)
    inicio = _tesouro_date(args, "inicio")
    fim = _tesouro_date(args, "fim")
    if inicio is not None and fim is not None and inicio > fim:
        raise mcp_services.DomainError(
            "periodo_invalido",
            "inicio não pode ser maior que fim.",
            "Informe um período com inicio <= fim.",
        )
    period = resolver_periodo_resgates(records, inicio, fim)
    filtered = ordenar_resgates(
        filtrar_resgates_por_periodo(
            filtrar_resgates_por_titulo(
                filtrar_resgates_por_tipo(records, _tesouro_tipo(args)),
                _tesouro_titulo(args),
            ),
            period[0],
            period[1],
        )
    )
    periodo = {"inicio": period[0], "fim": period[1]}
    if _tesouro_bool(args, "agregar"):
        aggregates = agregar_resgates(filtered)
        page, next_cursor = mcp_services.paginate(
            aggregates, inputs.cursor(args), inputs.limite(args)
        )
        payload = build_resgates_agregados_payload(
            page,
            metadata,
            periodo,
            len(filtered),
            include_fonte=False,
        )
    else:
        page, next_cursor = mcp_services.paginate(
            filtered, inputs.cursor(args), inputs.limite(args)
        )
        payload = build_resgates_payload(
            page, metadata, periodo, include_fonte=False
        )
        payload["total_registros"] = len(filtered)
    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    return payload


def tesouro_estoque(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``tesouro_estoque`` read-only cache tool."""
    records, metadata = _load_estoque(ctx)
    inicio = _tesouro_month(args, "inicio")
    fim = _tesouro_month(args, "fim")
    mes = _tesouro_month(args, "mes")
    if inicio is not None and fim is not None and inicio > fim:
        raise mcp_services.DomainError(
            "periodo_invalido",
            "inicio não pode ser maior que fim.",
            "Informe um período com inicio <= fim.",
        )
    period = resolver_periodo_estoque(records, inicio, fim, mes)
    filtered = ordenar_estoque(
        filtrar_estoque_por_periodo(
            filtrar_estoque_por_titulo(records, _tesouro_titulo(args)),
            period[0],
            period[1],
        )
    )
    periodo = {"inicio": period[0], "fim": period[1], "mes": mes}
    if _tesouro_bool(args, "agregar"):
        if len(meses_presentes(filtered)) > 1:
            raise mcp_services.DomainError(
                "periodo_invalido",
                "A agregação de estoque exige um único mês.",
                "Informe um intervalo de um único mês.",
            )
        aggregates = agregar_estoque(filtered)
        page, next_cursor = mcp_services.paginate(
            aggregates, inputs.cursor(args), inputs.limite(args)
        )
        payload = build_estoque_agregados_payload(
            page,
            metadata,
            periodo,
            len(filtered),
            include_fonte=False,
        )
    else:
        page, next_cursor = mcp_services.paginate(
            filtered, inputs.cursor(args), inputs.limite(args)
        )
        payload = build_estoque_payload(
            page, metadata, periodo, include_fonte=False
        )
        payload["total_registros"] = len(filtered)
    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    return payload
