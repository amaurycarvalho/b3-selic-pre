"""Hook best-effort do calendário nas cargas do Tesouro Direto."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


def ensure_calendar(cache: object) -> None:
    """Guarantee the current year calendar without blocking the load."""
    service = getattr(cache, "calendar", None)
    if service is None:
        return
    try:
        service.ensure_year(datetime.now(UTC).year)
    except Exception as exc:
        logger.warning(
            "Falha ao garantir o calendário de feriados: %s", exc
        )


__all__ = ["ensure_calendar"]
