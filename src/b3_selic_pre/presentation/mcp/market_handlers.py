"""Handlers MCP das tools de mercado, separados dos handlers da curva."""

from __future__ import annotations

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.market.export import (
    forecast_csv_from_payload,
    format_market_json,
    history_csv_from_payload,
)
from b3_selic_pre.application.market.payloads import (
    AVISO_CENARIO,
    filter_payload_window,
)
from b3_selic_pre.presentation.market_tab import MarketTabController
from b3_selic_pre.presentation.mcp import market_tool_inputs as market_inputs
from b3_selic_pre.presentation.mcp import tool_inputs as inputs
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.market_gaps import (
    market_items,
    missing_market_dates,
)


def _market_controller(ctx: ToolContext) -> MarketTabController:
    services = getattr(ctx, "market_services", None)
    if services is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há leitor de cache de mercado disponível.",
            "Reinicie o servidor MCP para preparar o leitor de mercado.",
        )
    return MarketTabController(services)


def _market_payload(
    ctx: ToolContext, resolution: str = "auto"
) -> dict[str, object]:
    controller = _market_controller(ctx)
    controller.options.resolucao = resolution
    payload = controller.load_cache_only()
    if not payload.get("series"):
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há dados de mercado em cache.",
            "Execute `b3-selic-pre mercado --atualizar` para preparar o cache.",
        )
    return payload


def _market_assets(ativo: str) -> tuple[str, ...]:
    return ("usd", "ouro") if ativo == "ambos" else (ativo,)


def mercado_serie(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``mercado_serie`` read-only cache tool."""
    ativo = market_inputs.market_ativo(args)
    inicio = market_inputs.market_date(args, "inicio")
    fim = market_inputs.market_date(args, "fim")
    if inicio is not None and fim is not None and inicio > fim:
        raise mcp_services.DomainError(
            "periodo_invalido",
            "inicio não pode ser maior que fim.",
            "Informe um período com inicio <= fim.",
        )
    payload = _market_payload(ctx, market_inputs.market_resolution(args))
    filtered = filter_payload_window(payload, ativo, inicio, fim)
    if filtered is None:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há série em cache para a janela solicitada.",
            "Execute `b3-selic-pre mercado --atualizar` para atualizar o cache.",
        )
    page, next_cursor = mcp_services.paginate(
        market_items(filtered), inputs.cursor(args), inputs.limite(args)
    )
    result: dict[str, object] = {
        "janela": filtered.get("janela"),
        "itens": page,
    }
    if next_cursor is not None:
        result["nextCursor"] = next_cursor
    return result


def mercado_previsao(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``mercado_previsao`` tool using only the artifact."""
    ativo = market_inputs.market_ativo(args)
    horizon = market_inputs.market_horizon(args)
    artifact = _market_controller(ctx).load_precomputed_only()
    if artifact is None:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há cenário pré-calculado disponível.",
            "Execute `b3-selic-pre mercado --atualizar` para preparar o cache.",
        )
    previsao = artifact.get("previsao")
    selected: dict[str, object] = {}
    for asset in _market_assets(ativo):
        data = (previsao if isinstance(previsao, dict) else {}).get(asset)
        if not isinstance(data, dict):
            continue
        items = data.get("itens")
        items = items if isinstance(items, list) else []
        selected[asset] = {**data, "itens": items[:horizon]}
    if not selected:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há cenário pré-calculado para o ativo solicitado.",
            "Atualize o cache com `b3-selic-pre mercado --atualizar`.",
        )
    return {"previsao": selected, "aviso": AVISO_CENARIO}


def mercado_indicadores(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``mercado_indicadores`` read-only cache tool."""
    _ = args
    payload = _market_payload(ctx)
    indicators = payload.get("indicadores")
    signals = {
        key: value
        for key, value in (indicators if isinstance(indicators, dict) else {}).items()
        if key != "aviso" and value is not None
    }
    if not signals:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há indicadores de mercado disponíveis no cache.",
            "Execute `b3-selic-pre mercado --atualizar` para preparar o cache.",
        )
    return dict(indicators) if isinstance(indicators, dict) else {}


def mercado_exportar(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``mercado_exportar`` tool without writing files."""
    ativo = market_inputs.market_ativo(args)
    inicio = market_inputs.market_date(args, "inicio")
    fim = market_inputs.market_date(args, "fim")
    if inicio is not None and fim is not None and inicio > fim:
        raise mcp_services.DomainError(
            "periodo_invalido",
            "inicio não pode ser maior que fim.",
            "Informe um período com inicio <= fim.",
        )
    payload = _market_payload(ctx)
    filtered = filter_payload_window(payload, ativo, inicio, fim)
    if filtered is None:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há dados de mercado para a janela solicitada.",
            "Execute `b3-selic-pre mercado --atualizar` para preparar o cache.",
        )
    window = filtered.get("janela")
    window = window if isinstance(window, dict) else {}
    missing = missing_market_dates(
        filtered,
        inicio or str(window.get("inicio", "")),
        fim or str(window.get("fim", "")),
        getattr(ctx, "calendar_service", None),
    )
    if market_inputs.market_format(args) == "json":
        return {
            "nome": "mercado.json",
            "content_type": "application/json",
            "conteudo": format_market_json(filtered),
            "datas_indisponiveis": missing,
        }
    result: dict[str, object] = {
        "nome": "mercado-historico.csv",
        "content_type": "text/csv",
        "conteudo": history_csv_from_payload(filtered),
        "datas_indisponiveis": missing,
    }
    if market_inputs.market_bool(args, "prever"):
        result["previsao"] = {
            "nome": "mercado-previsao.csv",
            "content_type": "text/csv",
            "conteudo": forecast_csv_from_payload(filtered),
        }
    return result
