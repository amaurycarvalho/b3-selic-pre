"""Montagem headless dos dados dos gráficos do Tesouro Direto."""

from __future__ import annotations

from dataclasses import dataclass

from b3_selic_pre.application.tesouro import (
    BUCKET_MENSAL,
    FAMILIAS,
    METRICA_DEMANDA_PCT,
    METRICA_ESTOQUE_PCT,
    SeriesProvider,
    bucket_para_janela,
)
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
    ComparisonChart,
    EvolutionChart,
    GapChart,
    ShareChart,
)
from b3_selic_pre.presentation.tesouro_series_reader import SeriesReader


@dataclass(frozen=True)
class SeriesBuilder:
    """Monta os dados dos gráficos a partir do leitor de séries."""

    kind: str
    window: str
    provider: SeriesProvider
    titles: tuple[str, ...]
    latest_data_date: str

    def _reader(self: SeriesBuilder) -> SeriesReader:
        return SeriesReader(
            provider=self.provider,
            titles=self.titles,
            window=self.window,
            latest_data_date=self.latest_data_date,
        )

    def _share_chart(
        self: SeriesBuilder,
        segments: dict[str, dict[str, float]],
        prefix: str,
    ) -> ShareChart:
        reader = self._reader()
        families = tuple(family for family in FAMILIAS if family in segments)
        return ShareChart(
            title=f"{prefix} — {reader.period_label()}",
            families=families,
            totals={
                family: sum(segments[family].values())
                for family in families
            },
            segments=segments,
        )

    def _comparison_chart(self: SeriesBuilder) -> ComparisonChart:
        reader = self._reader()
        estoque = reader.stock_family_current()
        apetite = reader.family_window_share()
        families = tuple(
            family
            for family in FAMILIAS
            if family in estoque or family in apetite
        )
        return ComparisonChart(
            title=(
                "Estoque vs Apetite do mercado "
                f"({reader.period_label()})"
            ),
            families=families,
            estoque=tuple(estoque.get(family, 0.0) for family in families),
            apetite=tuple(apetite.get(family, 0.0) for family in families),
        )

    def _evolution_chart(
        self: SeriesBuilder,
        metric: str,
        bucket: str,
        prefix: str,
        vertical_grid: bool = False,
    ) -> EvolutionChart:
        reader = self._reader()
        series = reader.family_percentuals(metric, bucket)
        periods = tuple(
            sorted({p for values in series.values() for p in values})
        )
        families = tuple(
            family for family in FAMILIAS if family in series
        )
        return EvolutionChart(
            title=f"{prefix} — {reader.period_label()}",
            periods=periods,
            series={
                family: tuple(series[family].get(p, 0.0) for p in periods)
                for family in families
            },
            vertical_grid=vertical_grid,
        )

    def _gap_chart(self: SeriesBuilder) -> GapChart:
        reader = self._reader()
        stock = reader.family_percentuals(METRICA_ESTOQUE_PCT, BUCKET_MENSAL)
        appetite = reader.family_percentuals(
            METRICA_DEMANDA_PCT, BUCKET_MENSAL
        )
        periods = tuple(
            sorted(
                {p for values in stock.values() for p in values}
                | {p for values in appetite.values() for p in values}
            )
        )
        families = tuple(
            family
            for family in FAMILIAS
            if family in stock or family in appetite
        )
        return GapChart(
            title=(
                "Gap Apetite menos Estoque "
                f"({reader.period_label()})"
            ),
            periods=periods,
            series={
                family: tuple(
                    appetite.get(family, {}).get(p, 0.0)
                    - stock.get(family, {}).get(p, 0.0)
                    for p in periods
                )
                for family in families
            },
        )

    def current_chart(self: SeriesBuilder) -> ShareChart | ComparisonChart:
        """Return the current chart for the sub-tab kind."""
        reader = self._reader()
        if self.kind == KIND_VISAO_GERAL:
            return self._comparison_chart()
        if self.kind == KIND_ESTOQUE:
            return self._share_chart(
                reader.stock_share(), "Composição do estoque"
            )
        return self._share_chart(reader.demand_share(), "Apetite do mercado")

    def evolution(self: SeriesBuilder) -> EvolutionChart | GapChart:
        """Return the evolution chart for the sub-tab kind."""
        if self.kind == KIND_VISAO_GERAL:
            return self._gap_chart()
        if self.kind == KIND_ESTOQUE:
            return self._evolution_chart(
                METRICA_ESTOQUE_PCT,
                BUCKET_MENSAL,
                "Evolução do estoque",
                vertical_grid=True,
            )
        return self._evolution_chart(
            METRICA_DEMANDA_PCT,
            bucket_para_janela(self.window),
            "Evolução do apetite",
            vertical_grid=True,
        )
