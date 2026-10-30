"""Estado de carregamento headless das sub-abas do Tesouro Direto."""

from __future__ import annotations

import inspect
from collections.abc import Callable

from b3_selic_pre.presentation.tesouro_analise_data import AnaliseData

AnaliseLoader = Callable[..., AnaliseData | None]
StageCallback = Callable[[str], None]


def _accepts_stage_callback(loader: AnaliseLoader) -> bool:
    try:
        parameters = inspect.signature(loader).parameters.values()
    except (TypeError, ValueError):
        return False
    positional = 0
    for parameter in parameters:
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            return True
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional += 1
    return positional >= 3


class TesouroLoadingMixin:
    """Métodos de carga compartilhados pelo controller do Tesouro."""

    def begin_load(
        self: TesouroLoadingMixin, *, cache_only: bool = False
    ) -> None:
        """Start a load, clearing the previous error and defining its origin."""
        self.loading = True
        self.loading_origin = "cache" if cache_only else "network"
        self.loading_stage = None
        self.error = None
        self.error_context = None

    def note_cache_presence(
        self: TesouroLoadingMixin, cache_present: bool
    ) -> bool:
        """Record cache availability and report a fresh cache-only reload."""
        became_present = cache_present and not self._cache_present
        self._cache_present = cache_present
        self.cache_available = cache_present
        return became_present and not self.has_data and not self.loading

    def load(
        self: TesouroLoadingMixin,
        *,
        cache_only: bool = False,
        force: bool = False,
        stage_callback: StageCallback | None = None,
    ) -> AnaliseData | None:
        """Load data through the injected loader, isolating failures."""
        self.begin_load(cache_only=cache_only)
        try:
            data = self._invoke_loader(cache_only, force, stage_callback)
        except Exception as exc:
            self.error = str(exc)
            self.error_context = "ler o cache" if cache_only else None
            data = None
        finally:
            self.loading = False
            self.loading_stage = None
        if data is None:
            return None
        self.error = None
        self.error_context = None
        self.cache_available = True
        self._cache_present = True
        self._data = data
        self.source = data.source
        self.extracted_at = data.extracted_at
        self._provider = data.provider or self.provider_factory(
            vendas=list(data.vendas),
            resgates=list(data.resgates),
            estoque=list(data.estoque),
        )
        return data

    def _invoke_loader(
        self: TesouroLoadingMixin,
        cache_only: bool,
        force: bool,
        stage_callback: StageCallback | None,
    ) -> AnaliseData | None:
        if stage_callback is not None and _accepts_stage_callback(self.loader):
            return self.loader(cache_only, force, stage_callback)
        return self.loader(cache_only, force)
