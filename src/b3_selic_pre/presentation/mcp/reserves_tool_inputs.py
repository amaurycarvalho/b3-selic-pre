"""Validação dos argumentos das tools MCP de reservas."""

from __future__ import annotations

from b3_selic_pre.presentation.mcp.protocol import InvalidParams


def reserves_janela(args: dict[str, object]) -> str:
    """Return the validated reserves window."""
    value = args.get("janela", "12m")
    if value not in ("12m", "3a"):
        raise InvalidParams("janela deve ser '12m' ou '3a'")
    return str(value)


def reserves_format(args: dict[str, object]) -> str:
    """Return the validated reserves export format."""
    value = args.get("formato", "csv")
    if value not in ("csv", "json"):
        raise InvalidParams("formato deve ser 'csv' ou 'json'")
    return str(value)


__all__ = ["reserves_format", "reserves_janela"]
