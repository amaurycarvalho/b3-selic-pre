"""Aplicação de layout do matplotlib com registro de avisos recuperáveis."""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

_TIGHT_WARNING = "Tight layout not applied"
_FALLBACK_MARGINS = {
    "left": 0.14,
    "right": 0.94,
    "top": 0.90,
    "bottom": 0.22,
}


def apply_tight_layout(
    fig: Figure,
    *,
    context: str = "gráfico",
    pad: float | None = None,
) -> None:
    """Apply tight layout, logging and replacing unrecoverable warnings.

    Matplotlib emits ``UserWarning`` when tight layout cannot accommodate all
    axes decorations. The warning is captured, recorded in the application log
    and replaced by conservative margins so it does not leak to the user.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            if pad is None:
                fig.tight_layout()
            else:
                fig.tight_layout(pad=pad)
        except Exception:
            logger.exception(
                "Falha ao aplicar tight_layout em %s", context
            )
            _fallback_layout(fig, context)
            return
    tight_warnings = [
        str(item.message)
        for item in caught
        if _TIGHT_WARNING in str(item.message)
    ]
    for item in caught:
        if _TIGHT_WARNING not in str(item.message):
            warnings.warn(item.message, item.category, stacklevel=2)
    if not tight_warnings:
        return
    logger.warning(
        "Tight layout não aplicado em %s: %s; usando margens conservadoras.",
        context,
        " ".join(tight_warnings),
    )
    _fallback_layout(fig, context)


def _fallback_layout(fig: Figure, context: str) -> None:
    """Apply conservative margins when automatic layout cannot fit."""
    try:
        fig.subplots_adjust(**_FALLBACK_MARGINS)
    except Exception:
        logger.exception(
            "Falha ao aplicar margens de fallback em %s", context
        )


__all__ = ["apply_tight_layout"]
