"""View-models headless das sub-abas de análise do Tesouro Direto."""

from __future__ import annotations

from dataclasses import dataclass, field

from b3_selic_pre.application.tesouro import JANELAS_DEMANDA, SeriesProvider
from b3_selic_pre.presentation.tesouro_chart_builder import SeriesBuilder
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
    WINDOW_LABELS,
    ComparisonChart,
    EvolutionChart,
    GapChart,
    ShareChart,
)

__all__ = [
    "KIND_APETITE",
    "KIND_ESTOQUE",
    "KIND_VISAO_GERAL",
    "WINDOW_LABELS",
    "ComparisonChart",
    "EvolutionChart",
    "GapChart",
    "ShareChart",
    "TesouroAnaliseViewModel",
]


@dataclass
class TesouroAnaliseViewModel:
    """Estado e dados derivados de uma sub-aba, sem importar Tkinter."""

    kind: str
    window: str = "12m"
    provider: SeriesProvider | None = None
    titles: tuple[str, ...] = ()
    latest_data_date: str | None = None
    source: str = "Cache"
    extracted_at: str | None = None
    loading: bool = False
    cache_available: bool = False
    error: str | None = None
    has_data: bool = False
    extra: dict[str, object] = field(default_factory=dict)

    @property
    def window_options(self: TesouroAnaliseViewModel) -> tuple[str, ...]:
        """Return the windows offered by the selector."""
        return JANELAS_DEMANDA

    @property
    def window_label(self: TesouroAnaliseViewModel) -> str:
        """Return the human readable window label."""
        return WINDOW_LABELS.get(self.window, self.window)

    @property
    def can_refresh(self: TesouroAnaliseViewModel) -> bool:
        """Return whether the refresh controls are enabled."""
        return not self.loading

    @property
    def empty_message(self: TesouroAnaliseViewModel) -> str:
        """Return the guidance shown when there is no cached data."""
        return "Nenhum dado em cache. Pressione Atualizar para carregar."

    @property
    def placeholder_message(self: TesouroAnaliseViewModel) -> str | None:
        """Return the centered chart message while there is no data."""
        if self.has_data:
            return None
        if self.loading and self.cache_available:
            return "Carregando dados do Tesouro…"
        return self.empty_message

    @property
    def status_text(self: TesouroAnaliseViewModel) -> str:
        """Return the status line for the sub-tab."""
        if self.error:
            return f"Erro ao carregar: {self.error}"
        if self.loading:
            if self.cache_available or self.has_data:
                return "Carregando dados do Tesouro…"
            return self.empty_message
        if not self.has_data:
            return self.empty_message
        parts = [f"Fonte: {self.source}"]
        if self.extracted_at:
            parts.append(f"Extração: {self.extracted_at}")
        if self.latest_data_date:
            parts.append(f"Dados até: {self.latest_data_date}")
        return "  |  ".join(parts)

    @property
    def status_kind(self: TesouroAnaliseViewModel) -> str:
        """Return the status severity used by the status bar."""
        if self.error:
            return "error"
        if self.loading:
            return "info" if self.cache_available or self.has_data else "warning"
        if not self.has_data:
            return "warning"
        return "success"

    @property
    def fluxo_liquido(self: TesouroAnaliseViewModel) -> str | None:
        """Return the formatted net flow detail for the appetite sub-tab."""
        value = self.extra.get("fluxo_liquido")
        if value is None:
            return None
        return f"Fluxo líquido na janela: R$ {value}"

    def _builder(self: TesouroAnaliseViewModel) -> SeriesBuilder | None:
        if (
            self.provider is None
            or not self.has_data
            or not self.latest_data_date
        ):
            return None
        return SeriesBuilder(
            kind=self.kind,
            window=self.window,
            provider=self.provider,
            titles=self.titles,
            latest_data_date=self.latest_data_date,
        )

    def current_chart(
        self: TesouroAnaliseViewModel,
    ) -> ShareChart | ComparisonChart | None:
        """Return the current percentage chart data."""
        builder = self._builder()
        return None if builder is None else builder.current_chart()

    def evolution_chart(
        self: TesouroAnaliseViewModel,
    ) -> EvolutionChart | GapChart | None:
        """Return the evolution chart data."""
        builder = self._builder()
        return None if builder is None else builder.evolution()
