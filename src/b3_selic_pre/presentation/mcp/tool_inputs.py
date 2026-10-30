"""Validação de argumentos e resolução de dados das tools MCP."""

from __future__ import annotations

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.use_cases import (
    FutureQueryDateError,
    OldQueryDateError,
    evolution_dates,
    validate_reference_date,
)
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation.cli_data import config_from_settings, resolve_data
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.protocol import InvalidParams


def arguments(value: object) -> dict[str, object]:
    """Validate and normalize tool arguments."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InvalidParams("arguments deve ser um objeto")
    return value


def curva(args: dict[str, object]) -> str:
    """Return the requested curve representation."""
    value = args.get("curva", "curta")
    if value not in ("curta", "longa"):
        raise InvalidParams("curva deve ser 'curta' ou 'longa'")
    return value


def cursor(args: dict[str, object]) -> str | None:
    """Return the optional pagination cursor."""
    value = args.get("cursor")
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidParams("cursor deve ser uma string")
    return value


def limite(args: dict[str, object]) -> int | None:
    """Return the optional page size."""
    value = args.get("limite")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidParams("limite deve ser um inteiro maior ou igual a 1")
    return value


def reference(ctx: ToolContext) -> tuple[str, str, bool]:
    """Resolve the reference date from settings or the cache."""
    settings = ctx.settings_factory()
    raw = settings.get("data_referencia", "")
    date: str | None = None
    origem = "settings"
    if isinstance(raw, str) and raw.strip():
        try:
            date = validate_reference_date(raw.strip())
        except ValueError:
            date = None
    if date is None:
        date = ctx.cache.last_cached_date()
        origem = "cache"
    if date is None:
        raise mcp_services.DomainError(
            "cache_vazio",
            "Não há data de referência válida nem dados no cache local.",
            "Execute `b3-selic-pre mcp --atualizar` para preparar o cache.",
        )
    records = ctx.cache.get(date, read_only=True)
    return date, origem, bool(records)


def resolve_date(args: dict[str, object], ctx: ToolContext) -> str:
    """Resolve and validate the date requested by a tool."""
    value = args.get("data")
    if value is not None and not isinstance(value, str):
        raise InvalidParams("data deve ser uma string AAAA-MM-DD")
    if value is None:
        value, _, _ = reference(ctx)
    try:
        return resolve_data(value)
    except FutureQueryDateError as exc:
        raise mcp_services.DomainError(
            "data_futura",
            str(exc),
            "Informe uma data até hoje.",
        ) from exc
    except OldQueryDateError as exc:
        raise mcp_services.DomainError(
            "data_antiga",
            str(exc),
            "Informe uma data dentro dos últimos 30 dias.",
        ) from exc
    except ValueError as exc:
        raise mcp_services.DomainError(
            "data_invalida",
            str(exc),
            "Use uma data no formato AAAA-MM-DD.",
        ) from exc


def load_current(data: str, ctx: ToolContext) -> list[RateRecord]:
    """Load the current curve from the cache."""
    records = ctx.cache.get(data, read_only=True)
    if not records:
        raise mcp_services.DomainError(
            "sem_dados",
            f"Não há registros em cache para {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    return records


def load_historical(
    data: str, ctx: ToolContext
) -> dict[str, list[RateRecord]]:
    """Load the evolution window from the cache."""
    historical: dict[str, list[RateRecord]] = {}
    for date_str in evolution_dates(data):
        historical[date_str] = ctx.cache.get(date_str, read_only=True) or []
    if not any(historical.values()):
        raise mcp_services.DomainError(
            "sem_dados",
            f"Não há registros em cache para a janela de {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    return historical


def config(ctx: ToolContext) -> object:
    """Build the analysis configuration from fresh settings."""
    return config_from_settings(ctx.settings_factory())

