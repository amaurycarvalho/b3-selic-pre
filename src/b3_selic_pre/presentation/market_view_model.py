"""View-model headless da sub-aba de câmbio e ouro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

ATIVO_AMBOS = "ambos"
STATUS_INFO = "info"
STATUS_WARNING = "warning"
STATUS_SUCCESS = "success"
EMPTY_MESSAGE = (
    "Sem dados de mercado em cache. Use Atualizar para consultar as fontes."
)


@dataclass
class MarketOptions:
    """Opções de visualização da sub-aba Dólar e Ouro."""

    ativo: str = ATIVO_AMBOS
    resolucao: str = "auto"
    base100: bool = False
    fibonacci: bool = False

    def set_ativo(self: MarketOptions, value: str) -> None:
        """Select the asset filter."""
        if value in (ATIVO_AMBOS, "usd", "ouro"):
            self.ativo = value

    def toggle_base100(self: MarketOptions) -> None:
        """Toggle the base-100 indexing."""
        self.base100 = not self.base100

    def toggle_fibonacci(self: MarketOptions) -> None:
        """Toggle the Fibonacci overlay."""
        self.fibonacci = not self.fibonacci


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def last_business_day(
    reference: date, calendar: object | None = None
) -> date:
    """Return the most recent business day on or before ``reference``."""
    if calendar is not None:
        return calendar.calendar_for(reference.year).previous_business_day(
            reference
        )
    current = reference
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def artifact_is_stale(
    latest: str | None,
    reference: date,
    calendar: object | None = None,
) -> bool:
    """Return whether the artifact is older than the expected business day."""
    if not latest:
        return False
    try:
        parsed = date.fromisoformat(latest)
    except ValueError:
        return False
    return last_business_day(reference, calendar) > parsed


@dataclass
class MarketViewModel:
    """Estado derivado do payload para a GUI."""

    payload: dict[str, Any]
    options: MarketOptions
    status_text: str
    status_kind: str
    stale_badge: str | None
    empty_message: str | None
    source_errors: tuple[str, ...] = ()

    @property
    def has_data(self: MarketViewModel) -> bool:
        """Return whether any series has items."""
        return any(
            series.get("itens")
            for series in _as_dict(self.payload.get("series")).values()
        )

    @property
    def available_assets(self: MarketViewModel) -> tuple[str, ...]:
        """Return the assets with data, in deterministic order."""
        series = _as_dict(self.payload.get("series"))
        return tuple(
            ativo
            for ativo in ("usd", "ouro")
            if _as_dict(series.get(ativo)).get("itens")
        )

    @property
    def window(self: MarketViewModel) -> tuple[str, str]:
        """Return the payload window as a pair."""
        window = _as_dict(self.payload.get("janela"))
        return str(window.get("inicio", "")), str(window.get("fim", ""))

    def series(self: MarketViewModel, ativo: str) -> list[dict[str, Any]]:
        """Return the serialized items for ``ativo``."""
        items = _as_dict(_as_dict(self.payload.get("series")).get(ativo)).get(
            "itens"
        )
        return [
            _as_dict(item)
            for item in (items if isinstance(items, list) else [])
        ]

    def forecast(self: MarketViewModel, ativo: str) -> list[dict[str, Any]]:
        """Return the serialized forecast items for ``ativo``."""
        previsao = _as_dict(self.payload.get("previsao"))
        items = _as_dict(previsao.get(ativo)).get("itens")
        return [
            _as_dict(item)
            for item in (items if isinstance(items, list) else [])
        ]

    @property
    def indicators(self: MarketViewModel) -> dict[str, Any]:
        """Return the serialized policy indicators."""
        return _as_dict(self.payload.get("indicadores"))

    @property
    def is_stale(self: MarketViewModel) -> bool:
        """Return whether any series is marked as stale."""
        return any(
            bool(_as_dict(series).get("defasado"))
            for series in _as_dict(self.payload.get("series")).values()
        )


def _stale_hours(payload: dict[str, Any]) -> float | None:
    hours: list[float] = []
    for series in _as_dict(payload.get("series")).values():
        for item in _as_dict(series).get("itens", []) or []:
            value = _as_dict(item).get("defasagem_horas")
            if isinstance(value, (int, float)):
                hours.append(float(value))
    return max(hours) if hours else None


def _status_text(
    payload: dict[str, Any],
    stale_hours: float | None,
    source_errors: tuple[str, ...] = (),
) -> str:
    extracted = payload.get("extraido_em") or "-"
    origin = payload.get("origem") or "-"
    text = f"Fonte: {origin} • Extração: {extracted}"
    if stale_hours is not None:
        text += f" • Dados defasados ({stale_hours:.1f} h)"
    if source_errors:
        text += f" • Fontes com falha: {', '.join(source_errors)}"
    return text


def build_view_model(
    payload: dict[str, Any],
    options: MarketOptions | None = None,
    source_errors: tuple[str, ...] = (),
) -> MarketViewModel:
    """Build the GUI view-model from a market payload."""
    options = options or MarketOptions()
    view = MarketViewModel(
        payload=payload,
        options=options,
        status_text="",
        status_kind=STATUS_INFO,
        stale_badge=None,
        empty_message=None,
        source_errors=source_errors,
    )
    if not view.has_data:
        return MarketViewModel(
            payload=payload,
            options=options,
            status_text=EMPTY_MESSAGE,
            status_kind=STATUS_WARNING,
            stale_badge=None,
            empty_message=EMPTY_MESSAGE,
            source_errors=source_errors,
        )
    stale_hours = _stale_hours(payload)
    return MarketViewModel(
        payload=payload,
        options=options,
        status_text=_status_text(payload, stale_hours, source_errors),
        status_kind=(
            STATUS_WARNING if stale_hours is not None else STATUS_SUCCESS
        ),
        stale_badge=(
            "Dados defasados" if stale_hours is not None else None
        ),
        empty_message=None,
        source_errors=source_errors,
    )


__all__ = [
    "ATIVO_AMBOS",
    "EMPTY_MESSAGE",
    "MarketOptions",
    "MarketViewModel",
    "artifact_is_stale",
    "build_view_model",
    "last_business_day",
]
