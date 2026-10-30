"""Contrato genérico de séries temporais e buckets do Tesouro Direto."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from b3_selic_pre.application.tesouro._percentuais import (
    JANELA_3_MESES,
    JANELA_14_DIAS,
    JANELAS_DEMANDA,
)
from b3_selic_pre.application.tesouro._taxonomia import classificar_familia
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)

DIMENSAO_FAMILIA = "familia"
DIMENSAO_PRODUTO = "produto"
DIMENSAO_PRODUTO_VENCIMENTO = "produto_vencimento"
DIMENSOES_SERIE = (
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    DIMENSAO_PRODUTO_VENCIMENTO,
)

METRICA_ESTOQUE_PCT = "estoque_pct"
METRICA_DEMANDA_PCT = "demanda_pct"
METRICA_FLUXO_LIQUIDO = "fluxo_liquido"
METRICA_ESTOQUE_VALOR = "estoque_valor"
METRICA_DEMANDA_VALOR = "demanda_valor"
METRICAS_SERIE = (
    METRICA_ESTOQUE_PCT,
    METRICA_DEMANDA_PCT,
    METRICA_FLUXO_LIQUIDO,
    METRICA_ESTOQUE_VALOR,
    METRICA_DEMANDA_VALOR,
)

BUCKET_DIARIO = "diario"
BUCKET_SEMANAL = "semanal"
BUCKET_MENSAL = "mensal"
BUCKETS = (BUCKET_DIARIO, BUCKET_SEMANAL, BUCKET_MENSAL)

_JANELA_PARA_BUCKET = {
    JANELA_14_DIAS: BUCKET_DIARIO,
    JANELA_3_MESES: BUCKET_SEMANAL,
    "12m": BUCKET_MENSAL,
    "3a": BUCKET_MENSAL,
}
Record = EstoqueTesouroDireto | VendaTesouroDireto | ResgateTesouroDireto


@dataclass(frozen=True)
class SeriesKey:
    """Identifica uma dimensão e uma chave de série."""

    dimension: str
    key: str


@dataclass(frozen=True)
class SeriesPoint:
    """Um ponto normalizado de série temporal."""

    period: str
    metric: str
    value: Decimal
    total: Decimal
    dimension: str
    key: str


@runtime_checkable
class SeriesProvider(Protocol):
    """Contrato genérico de provedor de séries temporais."""

    def fetch(
        self: SeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        """Return points for ``key`` between ``start`` and ``end``."""
        ...


def bucket_para_janela(janela: str) -> str:
    """Return the bucket prescribed for a demand/flow window."""
    if janela not in JANELAS_DEMANDA:
        raise ValueError(f"Janela inválida: {janela}.")
    return _JANELA_PARA_BUCKET[janela]


def bucket_para_metrica(metrica: str, janela: str) -> str:
    """Return the bucket prescribed for a metric; stock is always monthly."""
    if metrica not in METRICAS_SERIE:
        raise ValueError(f"Métrica inválida: {metrica}.")
    if metrica in (METRICA_ESTOQUE_PCT, METRICA_ESTOQUE_VALOR):
        return BUCKET_MENSAL
    return bucket_para_janela(janela)


def validar_bucket(bucket: str) -> None:
    """Validate a series bucket."""
    if bucket not in BUCKETS:
        raise ValueError(f"Bucket inválido: {bucket}.")


def validar_dimensao(dimensao: str) -> None:
    """Validate a series dimension."""
    if dimensao not in DIMENSOES_SERIE:
        raise ValueError(f"Dimensão inválida: {dimensao}.")


def chave_series(record: Record, dimensao: str) -> str:
    """Return the series key of a record for the requested dimension."""
    validar_dimensao(dimensao)
    if dimensao == DIMENSAO_FAMILIA:
        return classificar_familia(record.tipo_titulo).familia
    if dimensao == DIMENSAO_PRODUTO:
        return record.tipo_titulo
    return f"{record.tipo_titulo}|{record.vencimento}"
