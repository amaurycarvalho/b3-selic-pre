"""Percentuais de estoque/demanda e fluxo líquido do Tesouro Direto."""

from __future__ import annotations

import calendar
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from b3_selic_pre.application.tesouro._errors import TesouroDataError
from b3_selic_pre.application.tesouro._taxonomia import classificar_familia
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)

JANELA_14_DIAS = "14d"
JANELA_3_MESES = "3m"
JANELA_12_MESES = "12m"
JANELA_3_ANOS = "3a"
JANELAS_DEMANDA = (
    JANELA_14_DIAS,
    JANELA_3_MESES,
    JANELA_12_MESES,
    JANELA_3_ANOS,
)
_MESES_POR_JANELA = {
    JANELA_3_MESES: 3,
    JANELA_12_MESES: 12,
    JANELA_3_ANOS: 36,
}

DIMENSAO_FAMILIA = "familia"
DIMENSAO_TITULO = "titulo"
DIMENSOES_PERCENTUAL = (DIMENSAO_FAMILIA, DIMENSAO_TITULO)
_CEM = Decimal(100)

Record = EstoqueTesouroDireto | VendaTesouroDireto | ResgateTesouroDireto


@dataclass(frozen=True)
class PercentualItem:
    """Percentual de uma chave sobre o total de uma base."""

    chave: str
    dimensao: str
    valor: Decimal
    total: Decimal
    percentual: Decimal


def _validar_dimensao(dimensao: str) -> None:
    if dimensao not in DIMENSOES_PERCENTUAL:
        raise ValueError(f"Dimensão inválida: {dimensao}.")


def _validar_janela(janela: str) -> None:
    if janela not in JANELAS_DEMANDA:
        raise ValueError(f"Janela inválida: {janela}.")


def _subtrair_meses(value: date, months: int) -> date:
    total = value.year * 12 + (value.month - 1) - months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def inicio_janela(latest: str, janela: str) -> str:
    """Return the inclusive start date for a demand/flow window."""
    _validar_janela(janela)
    latest_date = date.fromisoformat(latest)
    if janela == JANELA_14_DIAS:
        return (latest_date - timedelta(days=14)).isoformat()
    return _subtrair_meses(latest_date, _MESES_POR_JANELA[janela]).isoformat()


def _chave(record: Record, dimensao: str) -> str:
    if dimensao == DIMENSAO_TITULO:
        return record.tipo_titulo
    return classificar_familia(record.tipo_titulo).familia


def _agrupar(
    records: Iterable[Record],
    dimensao: str,
    value_of: Callable[[Record], Decimal],
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for record in records:
        key = _chave(record, dimensao)
        totals[key] = totals.get(key, Decimal(0)) + value_of(record)
    return totals


def _percentual_item(
    chave: str,
    dimensao: str,
    valor: Decimal,
    total: Decimal,
) -> PercentualItem:
    return PercentualItem(
        chave=chave,
        dimensao=dimensao,
        valor=valor,
        total=total,
        percentual=(valor / total * _CEM) if total else Decimal(0),
    )


def _composicao(
    records: list[EstoqueTesouroDireto],
    dimensao: str,
) -> list[PercentualItem]:
    _validar_dimensao(dimensao)
    if not records:
        return []
    latest = max(item.mes for item in records)
    month_records = [item for item in records if item.mes == latest]
    total = sum(
        (item.valor_estoque for item in month_records), Decimal(0)
    )
    if total == 0:
        raise TesouroDataError(
            f"Total de estoque do mês {latest} é zero; não é possível "
            "calcular percentuais."
        )
    grouped = _agrupar(
        month_records, dimensao, lambda item: item.valor_estoque
    )
    return [
        _percentual_item(chave, dimensao, valor, total)
        for chave, valor in sorted(grouped.items())
    ]


def composicao_estoque_por_familia(
    records: list[EstoqueTesouroDireto],
) -> list[PercentualItem]:
    """Return the latest-month stock composition grouped by indexer family."""
    return _composicao(records, DIMENSAO_FAMILIA)


def composicao_estoque_por_titulo(
    records: list[EstoqueTesouroDireto],
) -> list[PercentualItem]:
    """Return the latest-month stock composition grouped by title."""
    return _composicao(records, DIMENSAO_TITULO)


def _maior_data_vendas(vendas: list[VendaTesouroDireto]) -> str | None:
    if not vendas:
        return None
    return max(item.data_liquidacao for item in vendas)


def _janela_vendas(
    vendas: list[VendaTesouroDireto],
    janela: str,
) -> tuple[str, str] | None:
    latest = _maior_data_vendas(vendas)
    if latest is None:
        return None
    return inicio_janela(latest, janela), latest


def _vendas_na_janela(
    vendas: list[VendaTesouroDireto],
    janela: str,
) -> list[VendaTesouroDireto]:
    interval = _janela_vendas(vendas, janela)
    if interval is None:
        return []
    inicio, fim = interval
    return [
        item
        for item in vendas
        if inicio <= item.data_liquidacao <= fim
    ]


def _demanda(
    vendas: list[VendaTesouroDireto],
    janela: str,
    dimensao: str,
) -> list[PercentualItem]:
    _validar_janela(janela)
    _validar_dimensao(dimensao)
    window = _vendas_na_janela(vendas, janela)
    total = sum((item.valor for item in window), Decimal(0))
    if total == 0:
        return []
    grouped = _agrupar(window, dimensao, lambda item: item.valor)
    return [
        _percentual_item(chave, dimensao, valor, total)
        for chave, valor in sorted(grouped.items())
    ]


def percentual_demanda_por_familia(
    vendas: list[VendaTesouroDireto],
    janela: str,
) -> list[PercentualItem]:
    """Return the sales share by indexer family for a demand window."""
    return _demanda(vendas, janela, DIMENSAO_FAMILIA)


def percentual_demanda_por_titulo(
    vendas: list[VendaTesouroDireto],
    janela: str,
) -> list[PercentualItem]:
    """Return the sales share by title for a demand window."""
    return _demanda(vendas, janela, DIMENSAO_TITULO)



