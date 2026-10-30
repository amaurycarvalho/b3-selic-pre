"""Controller headless de carregamento das sub-abas do Tesouro Direto."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from b3_selic_pre.application.tesouro import (
    JANELAS_DEMANDA,
    TesouroSeriesProvider,
    fluxo_liquido_por_familia,
)
from b3_selic_pre.presentation.tesouro_analise_data import AnaliseData
from b3_selic_pre.presentation.tesouro_analise_view_model import (
    KIND_APETITE,
    KIND_ESTOQUE,
    TesouroAnaliseViewModel,
)
from b3_selic_pre.presentation.tesouro_fluxo import fluxo_liquido_total

DEFAULT_WINDOWS = {
    KIND_APETITE: "14d",
    KIND_ESTOQUE: "12m",
    "visao-geral": "12m",
}


AnaliseLoader = Callable[[bool, bool], AnaliseData | None]


@dataclass
class TesouroAnaliseController:
    """Carrega cache e atualização de uma sub-aba, sem importar Tkinter."""

    kind: str
    loader: AnaliseLoader
    provider_factory: Callable[..., TesouroSeriesProvider] = (
        TesouroSeriesProvider
    )
    window: str = ""
    loading: bool = False
    cache_available: bool = False
    error: str | None = None
    source: str = "Cache"
    extracted_at: str | None = None
    _data: AnaliseData | None = field(default=None, repr=False)
    _provider: TesouroSeriesProvider | None = field(default=None, repr=False)

    def __post_init__(self: TesouroAnaliseController) -> None:
        """Apply the default window for the sub-tab kind."""
        if not self.window:
            self.window = DEFAULT_WINDOWS.get(self.kind, "12m")

    @property
    def has_data(self: TesouroAnaliseController) -> bool:
        """Return whether any data has been loaded."""
        return self._data is not None

    def set_window(self: TesouroAnaliseController, window: str) -> None:
        """Change the selected window, rejecting unknown values."""
        if window not in JANELAS_DEMANDA:
            raise ValueError(f"Janela inválida: {window}.")
        self.window = window

    def load(
        self: TesouroAnaliseController,
        *,
        cache_only: bool = False,
        force: bool = False,
    ) -> AnaliseData | None:
        """Load data through the injected loader, isolating failures."""
        self.loading = True
        try:
            data = self.loader(cache_only, force)
        except Exception as exc:
            if not cache_only:
                self.error = str(exc)
            data = None
        finally:
            self.loading = False
        if data is None:
            return None
        self.error = None
        self.cache_available = True
        self._data = data
        self.source = data.source
        self.extracted_at = data.extracted_at
        self._provider = data.provider or self.provider_factory(
            vendas=list(data.vendas),
            resgates=list(data.resgates),
            estoque=list(data.estoque),
        )
        return data

    def _latest(self: TesouroAnaliseController) -> str | None:
        data = self._data
        if data is None:
            return None
        if data.latest_data_date:
            return data.latest_data_date
        candidates = self._latest_candidates(
            [item.mes for item in data.estoque],
            [item.data_liquidacao for item in data.vendas],
        )
        return max(candidates) if candidates else None

    def _latest_candidates(
        self: TesouroAnaliseController,
        months: list[str],
        dates: list[str],
    ) -> list[str]:
        if self.kind == KIND_ESTOQUE:
            return months or dates
        if self.kind == KIND_APETITE:
            return dates or months
        return months or dates

    def _titles(self: TesouroAnaliseController) -> tuple[str, ...]:
        data = self._data
        if data is None:
            return ()
        if data.titles:
            return data.titles
        titles: set[str] = set()
        if self.kind in (KIND_ESTOQUE, "visao-geral"):
            titles.update(item.tipo_titulo for item in data.estoque)
        if self.kind in (KIND_APETITE, "visao-geral"):
            titles.update(item.tipo_titulo for item in data.vendas)
        return tuple(sorted(titles))

    def _fluxo(self: TesouroAnaliseController) -> str | None:
        if self.kind != KIND_APETITE or self._data is None:
            return None
        if self._data.vendas or self._data.resgates:
            items = fluxo_liquido_por_familia(
                list(self._data.vendas),
                list(self._data.resgates),
                self.window,
            )
            total = sum(
                (item.fluxo_liquido for item in items), Decimal(0)
            )
            return f"{total:.2f}"
        if self._provider is None:
            return None
        latest = self._data.fluxo_latest_data_date or self._latest()
        return fluxo_liquido_total(self._provider, latest, self.window)

    def view_model(self: TesouroAnaliseController) -> TesouroAnaliseViewModel:
        """Build the headless view-model for the current state."""
        extra: dict[str, object] = {}
        fluxo = self._fluxo()
        if fluxo is not None:
            extra["fluxo_liquido"] = fluxo
        return TesouroAnaliseViewModel(
            kind=self.kind,
            window=self.window,
            provider=self._provider,
            titles=self._titles(),
            latest_data_date=self._latest(),
            source=self.source,
            extracted_at=self.extracted_at,
            loading=self.loading,
            cache_available=self.cache_available,
            error=self.error,
            has_data=self.has_data,
            extra=extra,
        )
