"""View-model headless da sub-aba Reservas Internacionais."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from b3_selic_pre.domain.reserves import ReservesRegime

STATUS_INFO = "info"
STATUS_WARNING = "warning"
STATUS_SUCCESS = "success"
EMPTY_MESSAGE = (
    "Sem dados de reservas em cache. Use Atualizar para buscar a série "
    "do BCB SGS 13621."
)
STALE_GAP_DAYS = 2
REGIME_LABELS = {
    ReservesRegime.AUMENTO.value: "Aumento",
    ReservesRegime.ESTAVEL.value: "Estável",
    ReservesRegime.DETERIORACAO.value: "Deterioração",
}


@dataclass
class ReservesOptions:
    """Opções de visualização da sub-aba Reservas Internacionais."""

    janela: str = "12m"

    def set_janela(self: ReservesOptions, value: str) -> None:
        """Select the 12-month or 3-year window."""
        if value in ("12m", "3a"):
            self.janela = value


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def last_business_day(reference: date) -> date:
    """Return the most recent business day on or before ``reference``."""
    current = reference
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def _is_stale(latest: str | None, reference: date) -> bool:
    parsed = _parse(latest)
    if parsed is None:
        return False
    expected = last_business_day(reference)
    return (expected - parsed).days > STALE_GAP_DAYS


def _items(payload: Mapping[str, object]) -> list[dict[str, Any]]:
    serie = _as_dict(payload.get("serie"))
    items = serie.get("itens")
    return [
        _as_dict(item)
        for item in (items if isinstance(items, list) else [])
    ]


def _regime_badge(regime: object) -> str | None:
    if not isinstance(regime, str):
        return None
    label = REGIME_LABELS.get(regime)
    return f"Regime: {label}" if label else f"Regime: {regime}"


def _thresholds_text(thresholds: object) -> str:
    values = _as_dict(thresholds)
    growth = values.get("var_aumento")
    decline = values.get("var_deterioracao")
    drawdown = values.get("drawdown")
    parts: list[str] = []
    if isinstance(growth, (int, float)):
        parts.append(f"3m > {growth:.1f}%")
    if isinstance(decline, (int, float)):
        parts.append(f"3m < {decline:.1f}%")
    if isinstance(drawdown, (int, float)):
        parts.append(f"drawdown <= {drawdown:.1f}%")
    return "Limiares: " + "; ".join(parts) if parts else ""


@dataclass
class ReservesViewModel:
    """Estado derivado do payload de reservas para a GUI."""

    payload: dict[str, Any]
    options: ReservesOptions = field(default_factory=ReservesOptions)
    status_text: str = ""
    status_kind: str = STATUS_INFO
    stale_badge: str | None = None
    empty_message: str | None = None
    regime_badge: str | None = None
    thresholds_text: str = ""
    source_errors: tuple[str, ...] = ()

    @property
    def has_data(self: ReservesViewModel) -> bool:
        """Return whether the series has items."""
        return bool(_items(self.payload))

    @property
    def indicators(self: ReservesViewModel) -> dict[str, Any]:
        """Return the serialized reserves indicators."""
        return _as_dict(self.payload.get("indicadores"))

    @property
    def regime(self: ReservesViewModel) -> str | None:
        """Return the current deterministic regime name."""
        value = self.payload.get("regime")
        if isinstance(value, str):
            return value
        indicator = self.indicators.get("regime")
        return indicator if isinstance(indicator, str) else None

    @property
    def latest_data_date(self: ReservesViewModel) -> str | None:
        """Return the newest data date in the payload."""
        value = self.payload.get("latest_data_date")
        return value if isinstance(value, str) else None

    @property
    def window(self: ReservesViewModel) -> tuple[str, str]:
        """Return the payload window as a pair."""
        window = _as_dict(self.payload.get("janela"))
        return str(window.get("inicio", "")), str(window.get("fim", ""))


def _status_text(
    payload: Mapping[str, object],
    stale: bool,
    source_errors: tuple[str, ...],
) -> str:
    latest = payload.get("latest_data_date") or "-"
    source = payload.get("source") or payload.get("origem") or "BCB SGS 13621"
    text = f"Fonte: {source} • Último dado: {latest}"
    if stale:
        text += " • Dados defasados"
    if source_errors:
        text += f" • Fontes com falha: {', '.join(source_errors)}"
    return text


def build_view_model(
    payload: dict[str, Any],
    options: ReservesOptions | None = None,
    source_errors: tuple[str, ...] = (),
    now: datetime | None = None,
) -> ReservesViewModel:
    """Build the GUI view-model from a reserves payload."""
    options = options or ReservesOptions()
    if not _items(payload):
        return ReservesViewModel(
            payload=payload,
            options=options,
            status_text=EMPTY_MESSAGE,
            status_kind=STATUS_WARNING,
            empty_message=EMPTY_MESSAGE,
            source_errors=source_errors,
        )
    reference = (now or datetime.now()).date()
    latest = payload.get("latest_data_date")
    stale = _is_stale(
        latest if isinstance(latest, str) else None, reference
    )
    return ReservesViewModel(
        payload=payload,
        options=options,
        status_text=_status_text(payload, stale, source_errors),
        status_kind=STATUS_WARNING if stale else STATUS_SUCCESS,
        stale_badge="Dados defasados" if stale else None,
        regime_badge=_regime_badge(payload.get("regime")),
        thresholds_text=_thresholds_text(payload.get("limiares")),
        source_errors=source_errors,
    )


__all__ = [
    "EMPTY_MESSAGE",
    "REGIME_LABELS",
    "STALE_GAP_DAYS",
    "ReservesOptions",
    "ReservesViewModel",
    "build_view_model",
    "last_business_day",
]
