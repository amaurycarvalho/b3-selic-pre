"""Handlers MCP somente leitura das tools de feriados."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.calendar.service import BusinessDayResolution
from b3_selic_pre.domain.calendar import HolidayCalendar
from b3_selic_pre.presentation.calendar_text import weekday_abbreviation
from b3_selic_pre.presentation.mcp import tool_inputs as inputs
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.protocol import InvalidParams


def _ano(args: dict[str, object], current: int | None = None) -> int:
    value = args.get("ano")
    if value is None:
        return current or datetime.now(UTC).year
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidParams("ano deve ser um inteiro")
    if value < 1 or value > 9999:
        raise InvalidParams("ano fora do intervalo válido")
    return value


def _cache(ctx: ToolContext) -> object:
    cache = ctx.holiday_cache
    if cache is None:
        raise mcp_services.DomainError(
            "sem_dados",
            "Não há leitor de calendário de feriados disponível.",
            "Reinicie o servidor MCP com o calendário configurado.",
        )
    return cache


def _read_year(ctx: ToolContext, year: int) -> object:
    cache = _cache(ctx)
    data = cache.read(year)
    if data is None or not getattr(data, "published", False):
        raise mcp_services.DomainError(
            "sem_dados",
            f"Não há feriados em cache para {year}.",
            f"Execute `b3-selic-pre feriados --ano {year} --atualizar`.",
        )
    return data


def _items(data: object) -> list[dict[str, object]]:
    origin = str(getattr(data, "source", "ANBIMA"))
    return [
        {
            "data": holiday.date.isoformat(),
            "dia_semana": weekday_abbreviation(holiday.date),
            "nome": holiday.name,
            "origem": origin,
        }
        for holiday in getattr(data, "holidays", ())
    ]


def feriados_listar(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``feriados_listar`` read-only cache tool."""
    year = _ano(args)
    data = _read_year(ctx, year)
    page, next_cursor = mcp_services.paginate(
        _items(data), inputs.cursor(args), inputs.limite(args)
    )
    payload: dict[str, object] = {
        "ano": year,
        "origem": getattr(data, "source", "ANBIMA"),
        "extraido_em": getattr(data, "fetched_at", ""),
        "itens": page,
    }
    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    return payload


def _calendar_for(ctx: ToolContext, year: int) -> HolidayCalendar:
    cache = _cache(ctx)
    holidays = []
    for candidate in (year - 1, year, year + 1):
        data = cache.read(candidate)
        if data is not None and getattr(data, "published", False):
            holidays.extend(data.holidays)
    return HolidayCalendar(tuple(holidays))


def feriados_consultar(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``feriados_consultar`` read-only cache tool."""
    value = args.get("data")
    if not isinstance(value, str):
        raise InvalidParams("data deve ser uma string AAAA-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidParams("data deve estar no formato AAAA-MM-DD") from exc
    data = _read_year(ctx, parsed.year)
    service = ctx.calendar_service
    if service is not None:
        resolution = service.resolve_business_day(value)
    else:
        calendar = _calendar_for(ctx, parsed.year)
        business = calendar.is_business_day(parsed)
        holiday = calendar.holiday_on(parsed)
        resolution = BusinessDayResolution(
            data_solicitada=value,
            data_resolvida=(
                value
                if business
                else calendar.previous_business_day(parsed).isoformat()
            ),
            ajustada=not business,
            motivo=(
                None
                if business
                else (
                    "fim_de_semana"
                    if parsed.weekday() in calendar.weekend
                    else "feriado"
                )
            ),
            feriado=holiday.name if holiday else None,
            calendario_estado="ok",
        )
    calendar = _calendar_for(ctx, parsed.year)
    business = calendar.is_business_day(parsed)
    payload = {
        "data": value,
        "dia_semana": weekday_abbreviation(parsed),
        "dia_util": business,
        "origem": getattr(data, "source", "ANBIMA"),
    }
    payload.update(inputs.adjustment_fields(resolution))
    return payload


def _json_payload(data: object, year: int) -> str:
    return json.dumps(
        {
            "ano": year,
            "origem": getattr(data, "source", "ANBIMA"),
            "extraido_em": getattr(data, "fetched_at", ""),
            "feriados": _items(data),
        },
        ensure_ascii=False,
    )


def _csv_payload(data: object) -> str:
    lines = ["DATA;DIA_SEMANA;NOME;ORIGEM"]
    lines.extend(
        f"{item['data']};{item['dia_semana']};{item['nome']};{item['origem']}"
        for item in _items(data)
    )
    return "\n".join(lines) + "\n"


def feriados_exportar(
    args: dict[str, object], ctx: ToolContext
) -> dict[str, object]:
    """Handle the ``feriados_exportar`` tool without writing files."""
    year = _ano(args)
    data = _read_year(ctx, year)
    formato = args.get("formato", "csv")
    if formato not in ("csv", "json"):
        raise InvalidParams("formato deve ser 'csv' ou 'json'")
    if formato == "json":
        return {
            "nome": f"feriados-{year}.json",
            "content_type": "application/json",
            "conteudo": _json_payload(data, year),
        }
    return {
        "nome": f"feriados-{year}.csv",
        "content_type": "text/csv",
        "conteudo": _csv_payload(data),
    }


__all__ = ["feriados_consultar", "feriados_exportar", "feriados_listar"]
