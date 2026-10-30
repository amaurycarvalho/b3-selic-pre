"""Fluxo líquido de vendas menos recompras antecipadas do Tesouro."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from b3_selic_pre.application.tesouro._percentuais import (
    DIMENSAO_FAMILIA,
    DIMENSAO_TITULO,
    _agrupar,
    _validar_dimensao,
    _validar_janela,
    inicio_janela,
)
from b3_selic_pre.domain.models import (
    ResgateTesouroDireto,
    VendaTesouroDireto,
)


@dataclass(frozen=True)
class FluxoLiquidoItem:
    """Fluxo líquido de uma chave em uma janela."""

    chave: str
    dimensao: str
    valor_vendas: Decimal
    valor_recompras: Decimal
    fluxo_liquido: Decimal


def _maior_data_fluxo(
    vendas: list[VendaTesouroDireto],
    recompras: list[ResgateTesouroDireto],
) -> str | None:
    dates = [item.data_liquidacao for item in vendas]
    dates.extend(item.data_resgate for item in recompras)
    if not dates:
        return None
    return max(dates)


def _recompras_na_janela(
    resgates: list[ResgateTesouroDireto],
    inicio: str,
    fim: str,
) -> list[ResgateTesouroDireto]:
    return [
        item
        for item in resgates
        if item.tipo_resgate == "recompra"
        and inicio <= item.data_resgate <= fim
    ]


def _fluxo(
    vendas: list[VendaTesouroDireto],
    resgates: list[ResgateTesouroDireto],
    janela: str,
    dimensao: str,
) -> list[FluxoLiquidoItem]:
    _validar_janela(janela)
    _validar_dimensao(dimensao)
    latest = _maior_data_fluxo(vendas, resgates)
    if latest is None:
        return []
    inicio = inicio_janela(latest, janela)
    window_sales = [
        item for item in vendas if inicio <= item.data_liquidacao <= latest
    ]
    window_redemptions = _recompras_na_janela(resgates, inicio, latest)
    sales = _agrupar(window_sales, dimensao, lambda item: item.valor)
    redemptions = _agrupar(
        window_redemptions, dimensao, lambda item: item.valor
    )
    keys = sorted(set(sales) | set(redemptions))
    return [
        FluxoLiquidoItem(
            chave=key,
            dimensao=dimensao,
            valor_vendas=sales.get(key, Decimal(0)),
            valor_recompras=redemptions.get(key, Decimal(0)),
            fluxo_liquido=(
                sales.get(key, Decimal(0))
                - redemptions.get(key, Decimal(0))
            ),
        )
        for key in keys
    ]


def fluxo_liquido_por_familia(
    vendas: list[VendaTesouroDireto],
    resgates: list[ResgateTesouroDireto],
    janela: str,
) -> list[FluxoLiquidoItem]:
    """Return net sales minus early redemptions grouped by family."""
    return _fluxo(vendas, resgates, janela, DIMENSAO_FAMILIA)


def fluxo_liquido_por_titulo(
    vendas: list[VendaTesouroDireto],
    resgates: list[ResgateTesouroDireto],
    janela: str,
) -> list[FluxoLiquidoItem]:
    """Return net sales minus early redemptions grouped by title."""
    return _fluxo(vendas, resgates, janela, DIMENSAO_TITULO)
