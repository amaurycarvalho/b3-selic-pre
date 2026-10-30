"""Tipos compartilhados pelos adaptadores de mercado."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

ATIVO_XAU_USD = "xau_usd"
UNIDADE_XAU_USD = "USD/oz"
FONTE_BCB_SGS = "bcb_sgs_1"
FONTE_BCB_FOCUS = "bcb_focus"
FONTE_B3 = "b3_bdi"
FONTE_YAHOO = "yahoo_gc_f"
FONTE_OURO_DERIVADO = "ouro_derivado"
FONTE_DOL = "dol_front"
DOC_FOCUS = "focus.json"

Opener = Callable[..., object]


class MarketSourceError(Exception):
    """Previsível falha ao consultar uma fonte de mercado."""


class HttpSource(Protocol):
    """Contrato mínimo dos clientes HTTP de mercado."""

    def fetch_series(self: HttpSource) -> list[object]:
        """Return the normalized quotes exposed by the source."""
