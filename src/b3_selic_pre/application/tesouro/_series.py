"""Provider de séries temporais normalizadas do Tesouro Direto."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal

from b3_selic_pre.application.tesouro._series_contract import (
    BUCKET_DIARIO,
    BUCKET_MENSAL,
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    DIMENSAO_PRODUTO_VENCIMENTO,
    METRICA_DEMANDA_PCT,
    METRICA_DEMANDA_VALOR,
    METRICA_ESTOQUE_PCT,
    METRICA_ESTOQUE_VALOR,
    METRICA_FLUXO_LIQUIDO,
    EstoqueRecord,
    Record,
    SeriesKey,
    SeriesPoint,
    chave_series,
    validar_bucket,
    validar_dimensao,
)
from b3_selic_pre.application.tesouro._taxonomia import classificar_familia
from b3_selic_pre.domain.models import (
    ResgateTesouroDireto,
    VendaTesouroDireto,
)

_CEM = Decimal(100)


def _periodo(value: str, bucket: str) -> str:
    if bucket == BUCKET_MENSAL:
        return value[:7]
    if bucket == BUCKET_DIARIO:
        return value
    current = date.fromisoformat(value)
    return (current - timedelta(days=current.weekday())).isoformat()


def _intervalo_mensal(start: str, end: str) -> tuple[str, str]:
    return start[:7], end[:7]


def _intervalo_datas(start: str, end: str) -> tuple[str, str]:
    return start[:10], end[:10]


def _agrupar_por_periodo(
    records: list[Record],
    date_of: Callable[[Record], str],
    value_of: Callable[[Record], Decimal],
    bucket: str,
) -> dict[str, Decimal]:
    grouped: dict[str, Decimal] = {}
    for record in records:
        period = _periodo(date_of(record), bucket)
        grouped[period] = grouped.get(period, Decimal(0)) + value_of(record)
    return grouped


def _percentual(value: Decimal, total: Decimal) -> Decimal:
    return (value / total * _CEM) if total else Decimal(0)


def _selecionar(
    records: list[Record],
    key: SeriesKey,
) -> list[Record]:
    return [
        record
        for record in records
        if chave_series(record, key.dimension) == key.key
    ]


def _match_familia(item: EstoqueRecord, key: str) -> bool:
    return classificar_familia(item.tipo_titulo).familia == key


def _match_produto(item: EstoqueRecord, key: str) -> bool:
    return item.tipo_titulo == key


def _match_vencimento(item: EstoqueRecord, key: str) -> bool:
    vencimento = getattr(item, "vencimento", None)
    return vencimento is not None and f"{item.tipo_titulo}|{vencimento}" == key


_MATCHERS = {
    DIMENSAO_FAMILIA: _match_familia,
    DIMENSAO_PRODUTO: _match_produto,
    DIMENSAO_PRODUTO_VENCIMENTO: _match_vencimento,
}


def _selecionar_estoque(
    records: list[EstoqueRecord],
    key: SeriesKey,
) -> list[EstoqueRecord]:
    matcher = _MATCHERS.get(key.dimension)
    if matcher is None:
        return []
    return [item for item in records if matcher(item, key.key)]


def _point(
    period: str,
    metric: str,
    value: Decimal,
    total: Decimal,
    key: SeriesKey,
) -> SeriesPoint:
    percentual = metric in (METRICA_ESTOQUE_PCT, METRICA_DEMANDA_PCT)
    return SeriesPoint(
        period=period,
        metric=metric,
        value=_percentual(value, total) if percentual else value,
        total=total,
        dimension=key.dimension,
        key=key.key,
    )


class TesouroSeriesProvider:
    """Produces normalized Tesouro series from already parsed records."""

    def __init__(
        self: TesouroSeriesProvider,
        vendas: list[VendaTesouroDireto] | None = None,
        resgates: list[ResgateTesouroDireto] | None = None,
        estoque: list[EstoqueRecord] | None = None,
    ) -> None:
        """Store the parsed source records used by the provider."""
        self._vendas = list(vendas or [])
        self._resgates = list(resgates or [])
        self._estoque = list(estoque or [])

    def fetch(
        self: TesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        """Return all applicable metrics for ``key`` in the interval."""
        validar_bucket(bucket)
        validar_dimensao(key.dimension)
        points: list[SeriesPoint] = []
        points.extend(self._estoque_points(key, start, end))
        points.extend(self._demanda_points(key, start, end, bucket))
        points.extend(self._fluxo_points(key, start, end, bucket))
        return sorted(points, key=lambda item: (item.period, item.metric))

    def _estoque_points(
        self: TesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
    ) -> list[SeriesPoint]:
        start_month, end_month = _intervalo_mensal(start, end)
        records = [
            item
            for item in self._estoque
            if start_month <= item.mes <= end_month
        ]
        if not records:
            return []
        totals: dict[str, Decimal] = {}
        for item in records:
            totals[item.mes] = totals.get(item.mes, Decimal(0)) + (
                item.valor_estoque
            )
        grouped = _agrupar_por_periodo(
            _selecionar_estoque(records, key),
            lambda item: item.mes,
            lambda item: item.valor_estoque,
            BUCKET_MENSAL,
        )
        points: list[SeriesPoint] = []
        for period, value in sorted(grouped.items()):
            total = totals[period]
            points.append(
                _point(period, METRICA_ESTOQUE_PCT, value, total, key)
            )
            points.append(
                _point(period, METRICA_ESTOQUE_VALOR, value, total, key)
            )
        return points

    def _demanda_points(
        self: TesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        inicio, fim = _intervalo_datas(start, end)
        window = [
            item
            for item in self._vendas
            if inicio <= item.data_liquidacao <= fim
        ]
        if not window:
            return []
        totals = _agrupar_por_periodo(
            window,
            lambda item: item.data_liquidacao,
            lambda item: item.valor,
            bucket,
        )
        grouped = _agrupar_por_periodo(
            _selecionar(window, key),
            lambda item: item.data_liquidacao,
            lambda item: item.valor,
            bucket,
        )
        points: list[SeriesPoint] = []
        for period, value in sorted(grouped.items()):
            total = totals[period]
            points.append(
                _point(period, METRICA_DEMANDA_PCT, value, total, key)
            )
            points.append(
                _point(period, METRICA_DEMANDA_VALOR, value, total, key)
            )
        return points

    def _fluxo_points(
        self: TesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        inicio, fim = _intervalo_datas(start, end)
        window_sales = [
            item
            for item in self._vendas
            if inicio <= item.data_liquidacao <= fim
        ]
        window_redemptions = [
            item
            for item in self._resgates
            if item.tipo_resgate == "recompra"
            and inicio <= item.data_resgate <= fim
        ]
        totals = _agrupar_por_periodo(
            window_sales,
            lambda item: item.data_liquidacao,
            lambda item: item.valor,
            bucket,
        )
        sales = _agrupar_por_periodo(
            _selecionar(window_sales, key),
            lambda item: item.data_liquidacao,
            lambda item: item.valor,
            bucket,
        )
        redemptions = _agrupar_por_periodo(
            _selecionar(window_redemptions, key),
            lambda item: item.data_resgate,
            lambda item: item.valor,
            bucket,
        )
        periods = sorted(set(sales) | set(redemptions))
        return [
            _point(
                period,
                METRICA_FLUXO_LIQUIDO,
                sales.get(period, Decimal(0))
                - redemptions.get(period, Decimal(0)),
                totals.get(period, Decimal(0)),
                key,
            )
            for period in periods
        ]
