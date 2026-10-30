"""Textos compartilhados do calendário usados por GUI, CLI e MCP."""

from __future__ import annotations

from datetime import date

WEEKDAY_ABBREVIATIONS = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")


def weekday_abbreviation(value: date | int) -> str:
    """Return the Portuguese abbreviation of a weekday."""
    index = value.weekday() if isinstance(value, date) else value
    return WEEKDAY_ABBREVIATIONS[index]


def adjustment_message(resolution: object) -> str:
    """Describe a business-day adjustment for the status bar and stderr."""
    requested = resolution.data_solicitada
    resolved = resolution.data_resolvida
    motive = resolution.motivo
    holiday = getattr(resolution, "feriado", None)
    if motive == "feriado" and holiday:
        reason = f"feriado: {holiday}"
    elif motive == "fim_de_semana":
        reason = "fim de semana"
    else:
        reason = str(motive)
    return f"Data ajustada de {requested} para {resolved} ({reason})."


__all__ = ["WEEKDAY_ABBREVIATIONS", "adjustment_message", "weekday_abbreviation"]
