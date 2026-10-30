"""Controlador headless da aba ``Feriados``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from b3_selic_pre.presentation.feriados_view_model import FeriadosViewModel


@dataclass(frozen=True)
class RefreshOutcome:
    """Resultado da atualização forçada do calendário."""

    model: FeriadosViewModel
    refreshed: bool
    failed_years: tuple[int, ...]


class FeriadosController:
    """Lê apenas o cache e coordena a atualização forçada da aba."""

    def __init__(
        self: FeriadosController,
        cache: object,
        service: object,
        current_year: int | None = None,
    ) -> None:
        """Store the cache, calendar service and optional reference year."""
        self.cache = cache
        self.service = service
        self.current_year = current_year or datetime.now(UTC).year
        self._model = self.load_model()

    @property
    def model(self: FeriadosController) -> FeriadosViewModel:
        """Return the current view-model."""
        return self._model

    def load_model(self: FeriadosController) -> FeriadosViewModel:
        """Build the view-model from the cache without any network access."""
        years = getattr(self.cache, "years", None)
        cached_years = years() if callable(years) else []
        data = [
            item
            for item in (self.cache.read(year) for year in cached_years)
            if item is not None
        ]
        return FeriadosViewModel(data)

    def refresh(
        self: FeriadosController, displayed_years: tuple[int, ...] = ()
    ) -> RefreshOutcome:
        """Force revalidation of displayed years or the current year."""
        years = displayed_years or (self.current_year,)
        failed: list[int] = []
        for year in years:
            state = self.service.ensure_year(year, force=True)
            if state != "ok":
                failed.append(year)
        if failed:
            return RefreshOutcome(self._model, False, tuple(failed))
        self._model = self.load_model()
        return RefreshOutcome(self._model, True, ())


__all__ = ["FeriadosController", "RefreshOutcome"]
