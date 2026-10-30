"""Dados de entrada de uma sub-aba do Tesouro Direto."""

from __future__ import annotations

from dataclasses import dataclass

from b3_selic_pre.application.tesouro import EstoqueRecord, SeriesProvider
from b3_selic_pre.domain.models import (
    ResgateTesouroDireto,
    VendaTesouroDireto,
)


@dataclass(frozen=True)
class AnaliseData:
    """Dados brutos ou séries prontas para montar uma sub-aba."""

    vendas: tuple[VendaTesouroDireto, ...] = ()
    resgates: tuple[ResgateTesouroDireto, ...] = ()
    estoque: tuple[EstoqueRecord, ...] = ()
    latest_data_date: str | None = None
    source: str = "Cache"
    extracted_at: str | None = None
    provider: SeriesProvider | None = None
    titles: tuple[str, ...] = ()
    fluxo_latest_data_date: str | None = None
    btd_note: str | None = None
    btd_status_kind: str | None = None


__all__ = ["AnaliseData"]
