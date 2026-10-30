"""Provider de séries pré-calculadas usado pela apresentação."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from b3_selic_pre.application.tesouro._series import _periodo
from b3_selic_pre.application.tesouro._series_contract import (
    BUCKET_DIARIO,
    METRICA_DEMANDA_PCT,
    METRICA_DEMANDA_VALOR,
    METRICA_FLUXO_LIQUIDO,
    SeriesKey,
    SeriesPoint,
    validar_bucket,
    validar_dimensao,
)

_CEM = Decimal(100)


def _percentual(value: Decimal, total: Decimal) -> Decimal:
    return (value / total * _CEM) if total else Decimal(0)


def _matches(point: SeriesPoint, key: SeriesKey) -> bool:
    return point.dimension == key.dimension and point.key == key.key


def _daily(points: Sequence[SeriesPoint], key: SeriesKey) -> list[SeriesPoint]:
    return [point for point in points if _matches(point, key)]


class CachedTesouroSeriesProvider:
    """Serve series from precomputed points, aggregating daily buckets."""

    def __init__(
        self: CachedTesouroSeriesProvider,
        *,
        estoque: Sequence[SeriesPoint] = (),
        demanda: Sequence[SeriesPoint] = (),
        fluxo: Sequence[SeriesPoint] = (),
    ) -> None:
        """Store the precomputed source points."""
        self._estoque = tuple(estoque)
        self._demanda = tuple(demanda)
        self._fluxo = tuple(fluxo)
        self._demanda_totals = self._totals(
            self._demanda, METRICA_DEMANDA_VALOR
        )
        self._flow_totals = self._totals(
            self._fluxo, METRICA_FLUXO_LIQUIDO
        )

    @staticmethod
    def _totals(
        points: Sequence[SeriesPoint],
        metric: str,
    ) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for point in points:
            if point.metric == metric:
                totals.setdefault(point.period, point.total)
        return totals

    def fetch(
        self: CachedTesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        """Return points for ``key`` from the precomputed sources."""
        validar_bucket(bucket)
        validar_dimensao(key.dimension)
        points: list[SeriesPoint] = []
        points.extend(self._stock(key, start, end))
        points.extend(self._demand(key, start, end, bucket))
        points.extend(self._flow(key, start, end, bucket))
        return sorted(points, key=lambda item: (item.period, item.metric))

    def _stock(
        self: CachedTesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
    ) -> list[SeriesPoint]:
        start_month, end_month = start[:7], end[:7]
        return [
            point
            for point in self._estoque
            if _matches(point, key)
            and start_month <= point.period <= end_month
        ]

    def _demand(
        self: CachedTesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        start_date, end_date = start[:10], end[:10]
        points = [
            point
            for point in _daily(self._demanda, key)
            if start_date <= point.period <= end_date
        ]
        if bucket == BUCKET_DIARIO:
            return points
        return self._aggregate_demand(
            points, key, bucket, start_date, end_date
        )

    def _aggregate_demand(
        self: CachedTesouroSeriesProvider,
        points: list[SeriesPoint],
        key: SeriesKey,
        bucket: str,
        start: str,
        end: str,
    ) -> list[SeriesPoint]:
        grouped: dict[str, Decimal] = {}
        for point in points:
            if point.metric != METRICA_DEMANDA_VALOR:
                continue
            period = _periodo(point.period, bucket)
            grouped[period] = grouped.get(period, Decimal(0)) + point.value
        totals = self._bucket_totals(
            self._demanda_totals, start, end, bucket
        )
        result: list[SeriesPoint] = []
        for period, value in sorted(grouped.items()):
            total = totals.get(period, Decimal(0))
            result.append(
                SeriesPoint(
                    period,
                    METRICA_DEMANDA_VALOR,
                    value,
                    total,
                    key.dimension,
                    key.key,
                )
            )
            result.append(
                SeriesPoint(
                    period,
                    METRICA_DEMANDA_PCT,
                    _percentual(value, total),
                    total,
                    key.dimension,
                    key.key,
                )
            )
        return result

    def _flow(
        self: CachedTesouroSeriesProvider,
        key: SeriesKey,
        start: str,
        end: str,
        bucket: str,
    ) -> list[SeriesPoint]:
        start_date, end_date = start[:10], end[:10]
        points = [
            point
            for point in _daily(self._fluxo, key)
            if start_date <= point.period <= end_date
        ]
        if bucket == BUCKET_DIARIO:
            return points
        grouped: dict[str, Decimal] = {}
        for point in points:
            period = _periodo(point.period, bucket)
            grouped[period] = grouped.get(period, Decimal(0)) + point.value
        totals = self._bucket_totals(
            self._flow_totals, start_date, end_date, bucket
        )
        return [
            SeriesPoint(
                period,
                METRICA_FLUXO_LIQUIDO,
                value,
                totals.get(period, Decimal(0)),
                key.dimension,
                key.key,
            )
            for period, value in sorted(grouped.items())
        ]

    @staticmethod
    def _bucket_totals(
        daily_totals: dict[str, Decimal],
        start: str,
        end: str,
        bucket: str,
    ) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for period, total in daily_totals.items():
            if not start <= period <= end:
                continue
            bucket_period = _periodo(period, bucket)
            totals[bucket_period] = (
                totals.get(bucket_period, Decimal(0)) + total
            )
        return totals


__all__ = ["CachedTesouroSeriesProvider"]
