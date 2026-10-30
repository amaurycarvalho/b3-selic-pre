"""Handlers MCP das tools de reservas internacionais."""

from __future__ import annotations

from datetime import date

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.market.export import format_market_json
from b3_selic_pre.application.reserves.config import meses_janela
from b3_selic_pre.application.reserves.export import (
    series_csv_from_payload,
)
from b3_selic_pre.application.reserves.payloads import (
    filter_payload_window,
    missing_dates,
)
from b3_selic_pre.application.reserves.series import shift_months
from b3_selic_pre.presentation.mcp import market_tool_inputs as market_inputs
from b3_selic_pre.presentation.mcp import reserves_tool_inputs as reserves_inputs
from b3_selic_pre.presentation.mcp import tool_inputs as inputs
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.reserves_tab import ReservesTabController


def _controller(ctx: ToolContext) -> ReservesTabController:
    services = getattr(ctx, "reserves_services", None)
    if services is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há leitor de cache de reservas disponível.",
            "Reinicie o servidor MCP para preparar o leitor de reservas.",
        )
    return ReservesTabController(services)


def _payload(ctx: ToolContext) -> dict[str, object]:
    payload = _controller(ctx).load_cache_only()
    if not _items(payload):
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há dados de reservas em cache.",
            "Execute `b3-selic-pre reservas --atualizar` para preparar o cache.",
        )
    return payload


def _items(payload: dict[str, object]) -> list[dict[str, object]]:
    serie = payload.get("serie")
    items = serie.get("itens") if isinstance(serie, dict) else None
    return [
        item for item in (items if isinstance(items, list) else [])
        if isinstance(item, dict)
    ]


def _default_window(
    payload: dict[str, object], janela: str
) -> tuple[str | None, str | None]:
    latest = payload.get("latest_data_date")
    if not isinstance(latest, str) or not latest:
        items = _items(payload)
        latest = str(items[-1].get("data")) if items else None
    if latest is None:
        return None, None
    try:
        start = shift_months(
            date.fromisoformat(latest), -meses_janela(janela)
        )
    except ValueError:
        return None, None
    return start.isoformat(), latest


def _window(
    args: dict[str, object], payload: dict[str, object]
) -> tuple[str | None, str | None]:
    inicio = market_inputs.market_date(args, "inicio")
    fim = market_inputs.market_date(args, "fim")
    if inicio is not None and fim is not None and inicio > fim:
        raise mcp_services.DomainError(
            "periodo_invalido",
            "inicio não pode ser maior que fim.",
            "Informe um período com inicio <= fim.",
        )
    if inicio is None and fim is None:
        return _default_window(payload, reserves_inputs.reserves_janela(args))
    return inicio, fim


def _filtered(
    args: dict[str, object], payload: dict[str, object]
) -> tuple[dict[str, object], str | None, str | None]:
    inicio, fim = _window(args, payload)
    filtered = filter_payload_window(payload, inicio, fim)
    if filtered is None:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há série de reservas em cache para a janela solicitada.",
            "Execute `b3-selic-pre reservas --atualizar` para atualizar o cache.",
        )
    return filtered, inicio, fim


def reservas_serie(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``reservas_serie`` read-only cache tool."""
    payload = _payload(ctx)
    filtered, _, _ = _filtered(args, payload)
    page, next_cursor = mcp_services.paginate(
        _items(filtered), inputs.cursor(args), inputs.limite(args)
    )
    result: dict[str, object] = {
        "janela": filtered.get("janela"),
        "itens": page,
    }
    if next_cursor is not None:
        result["nextCursor"] = next_cursor
    return result


def reservas_indicadores(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``reservas_indicadores`` read-only cache tool."""
    _ = args
    payload = _payload(ctx)
    indicators = payload.get("indicadores")
    result = dict(indicators) if isinstance(indicators, dict) else {}
    if not result:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há indicadores de reservas disponíveis no cache.",
            "Execute `b3-selic-pre reservas --atualizar` para preparar o cache.",
        )
    if "regime" not in result and payload.get("regime"):
        result["regime"] = payload.get("regime")
    if "limiares" not in result and payload.get("limiares"):
        result["limiares"] = payload.get("limiares")
    return result


def reservas_exportar(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``reservas_exportar`` tool without writing files."""
    payload = _payload(ctx)
    filtered, inicio, fim = _filtered(args, payload)
    window = filtered.get("janela")
    window = window if isinstance(window, dict) else {}
    missing = missing_dates(
        filtered,
        inicio or str(window.get("inicio", "")),
        fim or str(window.get("fim", "")),
    )
    if reserves_inputs.reserves_format(args) == "json":
        return {
            "nome": "reservas.json",
            "content_type": "application/json",
            "conteudo": format_market_json(filtered),
            "datas_indisponiveis": missing,
        }
    return {
        "nome": "reservas-serie.csv",
        "content_type": "text/csv",
        "conteudo": series_csv_from_payload(filtered),
        "datas_indisponiveis": missing,
    }


__all__ = ["reservas_exportar", "reservas_indicadores", "reservas_serie"]
