"""Validação dos argumentos das tools MCP de mercado."""

from __future__ import annotations

from datetime import date

from b3_selic_pre.application import mcp_services
from b3_selic_pre.presentation.mcp.protocol import InvalidParams


def market_ativo(args: dict[str, object]) -> str:
    """Return the validated market asset filter."""
    value = args.get("ativo", "ambos")
    if value not in ("usd", "ouro", "ambos"):
        raise InvalidParams("ativo deve ser 'usd', 'ouro' ou 'ambos'")
    return str(value)


def market_resolution(args: dict[str, object]) -> str:
    """Return the validated market resolution."""
    value = args.get("resolucao", "auto")
    if value not in ("auto", "dia", "semana", "mes"):
        raise InvalidParams(
            "resolucao deve ser 'auto', 'dia', 'semana' ou 'mes'"
        )
    return str(value)


def market_format(args: dict[str, object]) -> str:
    """Return the validated export format."""
    value = args.get("formato", "csv")
    if value not in ("csv", "json"):
        raise InvalidParams("formato deve ser 'csv' ou 'json'")
    return str(value)


def market_date(
    args: dict[str, object], key: str
) -> str | None:
    """Return an optional ISO market date."""
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


def market_bool(args: dict[str, object], key: str) -> bool:
    """Return a boolean market option, defaulting to false."""
    value = args.get(key, False)
    if not isinstance(value, bool):
        raise InvalidParams(f"{key} deve ser um booleano")
    return value


def market_horizon(args: dict[str, object]) -> int:
    """Return the validated forecast horizon in months."""
    value = args.get("horizonte", 12)
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidParams("horizonte deve ser um inteiro")
    if value < 1 or value > 24:
        raise InvalidParams("horizonte deve estar entre 1 e 24 meses")
    return value
