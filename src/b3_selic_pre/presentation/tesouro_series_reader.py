"""Leitura e agregação headless de séries para os gráficos do Tesouro."""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from dataclasses import dataclass

from b3_selic_pre.application.tesouro import (
    BUCKET_MENSAL,
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    FAMILIAS,
    METRICA_DEMANDA_VALOR,
    METRICA_ESTOQUE_PCT,
    SeriesKey,
    SeriesPoint,
    SeriesProvider,
    agregar_series,
    bucket_para_janela,
    classificar_familia,
    inicio_janela,
)
from b3_selic_pre.presentation.tesouro_chart_data import WINDOW_LABELS


@dataclass(frozen=True)
class SeriesReader:
    """Consulta o provider e devolve percentuais prontos para os gráficos."""

    provider: SeriesProvider
    titles: tuple[str, ...]
    window: str
    latest_data_date: str

    @property
    def anchor(self: SeriesReader) -> str:
        """Return a date usable as the window anchor."""
        latest = self.latest_data_date
        return f"{latest}-01" if len(latest) == 7 else latest

    @property
    def end_date(self: SeriesReader) -> str:
        """Return the inclusive end date of the selected window."""
        latest = self.latest_data_date
        if len(latest) != 7:
            return latest
        year, month = (int(part) for part in latest.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{latest}-{last_day:02d}"

    @property
    def latest_month(self: SeriesReader) -> str:
        """Return the latest stock month, if applicable."""
        return self.latest_data_date[:7]

    def period_label(self: SeriesReader) -> str:
        """Return the window/date label used in chart titles."""
        label = WINDOW_LABELS.get(self.window, self.window)
        return f"{label} até {self.latest_data_date}"

    def collect(
        self: SeriesReader,
        keys: Iterable[str],
        dimension: str,
        start: str,
        end: str,
        bucket: str,
        metric: str,
    ) -> list[SeriesPoint]:
        """Collect points for many keys, keeping only one metric."""
        points: list[SeriesPoint] = []
        for key in keys:
            for point in self.provider.fetch(
                SeriesKey(dimension, key), start, end, bucket
            ):
                if point.metric == metric:
                    points.append(point)
        return points

    def stock_share(self: SeriesReader) -> dict[str, dict[str, float]]:
        """Return the latest-month stock share by family and title."""
        month = self.latest_month
        points = self.collect(
            self.titles,
            DIMENSAO_PRODUTO,
            f"{month}-01",
            f"{month}-01",
            BUCKET_MENSAL,
            METRICA_ESTOQUE_PCT,
        )
        latest = max((point.period for point in points), default=month)
        segments: dict[str, dict[str, float]] = {}
        for point in points:
            if point.period != latest:
                continue
            family = classificar_familia(point.key).familia
            segments.setdefault(family, {})[point.key] = float(point.value)
        return segments

    def demand_share(self: SeriesReader) -> dict[str, dict[str, float]]:
        """Return the aggregated demand share by family and title."""
        points = self.collect(
            self.titles,
            DIMENSAO_PRODUTO,
            inicio_janela(self.anchor, self.window),
            self.end_date,
            bucket_para_janela(self.window),
            METRICA_DEMANDA_VALOR,
        )
        segments: dict[str, dict[str, float]] = {}
        for share in agregar_series(points, metrica_valor=METRICA_DEMANDA_VALOR):
            family = classificar_familia(share.key).familia
            segments.setdefault(family, {})[share.key] = float(
                share.percentual
            )
        return segments

    def family_percentuals(
        self: SeriesReader,
        metric: str,
        bucket: str,
    ) -> dict[str, dict[str, float]]:
        """Return family percentages keyed by period."""
        points = self.collect(
            FAMILIAS,
            DIMENSAO_FAMILIA,
            inicio_janela(self.anchor, self.window),
            self.end_date,
            bucket,
            metric,
        )
        series: dict[str, dict[str, float]] = {}
        for point in points:
            series.setdefault(point.key, {})[point.period] = float(point.value)
        return series

    def family_window_share(self: SeriesReader) -> dict[str, float]:
        """Return aggregated demand percentages for the window."""
        points = self.collect(
            FAMILIAS,
            DIMENSAO_FAMILIA,
            inicio_janela(self.anchor, self.window),
            self.end_date,
            bucket_para_janela(self.window),
            METRICA_DEMANDA_VALOR,
        )
        return {
            share.key: float(share.percentual)
            for share in agregar_series(
                points, metrica_valor=METRICA_DEMANDA_VALOR
            )
        }

    def stock_family_current(self: SeriesReader) -> dict[str, float]:
        """Return the latest-month stock percentages by family."""
        month = self.latest_month
        points = self.collect(
            FAMILIAS,
            DIMENSAO_FAMILIA,
            f"{month}-01",
            f"{month}-01",
            BUCKET_MENSAL,
            METRICA_ESTOQUE_PCT,
        )
        latest = max((point.period for point in points), default=month)
        return {
            point.key: float(point.value)
            for point in points
            if point.period == latest
        }
