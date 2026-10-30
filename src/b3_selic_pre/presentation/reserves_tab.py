"""Controlador headless da sub-aba Reservas Internacionais."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

from b3_selic_pre.application.reserves.config import (
    ReservesConfig,
    meses_janela,
)
from b3_selic_pre.application.reserves.indicators import compute_indicators
from b3_selic_pre.application.reserves.payloads import (
    empty_payload,
    reserves_payload,
)
from b3_selic_pre.application.reserves.series import (
    incremental_start,
    merge_points,
    points_hash,
    retained_points,
    shift_months,
    snapshot_hash,
)
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import FONTE_RESERVAS

RESERVES_SOURCE = "bcb_sgs_13621"


class ReservesTabController:
    """Loads cached snapshots and refreshes the reserves precomputation."""

    def __init__(
        self: ReservesTabController,
        services: object,
        config: ReservesConfig | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        """Store the injected services and optional clock."""
        self.services = services
        self.config = (
            config
            or getattr(services, "config", None)
            or ReservesConfig()
        )
        self._now = now or (lambda: datetime.now(UTC))

    def _today(self: ReservesTabController) -> str:
        return self._now().date().isoformat()

    def _raw(self: ReservesTabController) -> object:
        return self.services.raw  # type: ignore[attr-defined]

    def _precompute(self: ReservesTabController) -> object:
        return self.services.precompute  # type: ignore[attr-defined]

    def _source(self: ReservesTabController) -> object:
        return self.services.source  # type: ignore[attr-defined]

    def snapshot_points(self: ReservesTabController) -> list[MarketQuote]:
        """Read the normalized snapshot without touching the network."""
        return self._raw().read_snapshot_points(RESERVES_SOURCE)

    def _latest(
        self: ReservesTabController,
        points: list[MarketQuote] | None = None,
    ) -> str | None:
        sample = points if points is not None else self.snapshot_points()
        return sample[-1].data if sample else None

    def _retained(
        self: ReservesTabController, points: list[MarketQuote]
    ) -> list[MarketQuote]:
        return retained_points(
            points, self._latest(points), self.config.retencao_anos
        )

    def _key(self: ReservesTabController, points: list[MarketQuote]) -> str:
        retained = self._retained(points)
        return snapshot_hash(
            retained,
            self.config,
            reference=self._latest(retained),
            years=self.config.retencao_anos,
        )

    def _retained_window(
        self: ReservesTabController, retained: list[MarketQuote]
    ) -> dict[str, str]:
        if not retained:
            return {"inicio": "", "fim": ""}
        return {
            "inicio": retained[0].data,
            "fim": retained[-1].data,
        }

    def _build_payload(
        self: ReservesTabController,
        points: list[MarketQuote],
        origem: str,
    ) -> dict[str, Any]:
        retained = self._retained(points)
        if not retained:
            return empty_payload(
                self._window(self._today(), meses_janela("12m"))
            )
        reference = retained[-1].data
        payload = reserves_payload(
            retained,
            compute_indicators(retained, self.config),
            self._retained_window(retained),
            origem,
            self._now().isoformat(timespec="seconds"),
            latest_data_date=reference,
        )
        payload["hash"] = self._key(retained)
        payload["window_retained"] = self._retained_window(retained)
        payload["source"] = FONTE_RESERVAS
        payload["unit"] = "USD_milhoes"
        return payload

    def _window(self: ReservesTabController, end: str, months: int) -> dict[str, str]:
        try:
            reference = date.fromisoformat(end)
        except (TypeError, ValueError):
            return {"inicio": "", "fim": end}
        return {
            "inicio": shift_months(reference, -months).isoformat(),
            "fim": end,
        }

    def _empty(self: ReservesTabController) -> dict[str, Any]:
        return empty_payload(
            self._window(self._today(), meses_janela("12m"))
        )

    def load_precomputed_only(
        self: ReservesTabController,
    ) -> dict[str, Any] | None:
        """Read only the artifact matching the current snapshot hash."""
        points = self.snapshot_points()
        if not points:
            return None
        return self._precompute().read_artifact(self._key(points))

    def load_cache_only(self: ReservesTabController) -> dict[str, Any]:
        """Load the artifact or compute the payload from cache, offline."""
        artifact = self.load_precomputed_only()
        if artifact is not None:
            return artifact
        points = self.snapshot_points()
        if not points:
            return self._empty()
        return self._build_payload(points, "Cache")

    def _fetch_start(self: ReservesTabController, force: bool) -> str:
        today = self._today()
        last = self._raw().snapshot_last_date(RESERVES_SOURCE)
        if force or last is None:
            return shift_months(date.fromisoformat(today), -36).isoformat()
        return incremental_start(last, self.config.sobreposicao_dias)

    def _fetch(
        self: ReservesTabController,
        force: bool,
        errors: list[str],
    ) -> list[MarketQuote]:
        start = self._fetch_start(force)
        try:
            return self._source().fetch_series(start, self._today())
        except Exception as exc:
            errors.append(f"{FONTE_RESERVAS}: {exc}")
            return []

    def _persist(
        self: ReservesTabController, points: list[MarketQuote]
    ) -> list[MarketQuote]:
        retained = self._retained(points)
        latest = self._latest(retained)
        if latest is not None:
            self._raw().write_snapshot(
                RESERVES_SOURCE,
                retained,
                source=FONTE_RESERVAS,
            )
            self._raw().prune_snapshot(
                RESERVES_SOURCE,
                latest,
                self.config.retencao_anos,
            )
        return retained

    def _store_artifact(
        self: ReservesTabController,
        payload: dict[str, Any],
        retained: list[MarketQuote],
        latest: str,
    ) -> None:
        key = str(payload["hash"])
        signatures = {RESERVES_SOURCE: points_hash(retained)}
        try:
            self._precompute().update_if_changed(
                key,
                signatures,
                latest,
                lambda: payload,
            )
        except Exception:
            return
        try:
            self._precompute().housekeeping(latest)
        except Exception:
            return

    def refresh(
        self: ReservesTabController, force: bool = False
    ) -> dict[str, Any]:
        """Fetch the series, persist the snapshot and refresh the artifact."""
        errors: list[str] = []
        incoming = self._fetch(force, errors)
        existing = self.snapshot_points()
        merged = merge_points(existing, incoming)
        retained = self._persist(merged) if merged else []
        if not retained:
            result = self._empty()
            result["erros_fontes"] = errors
            return result
        payload = self._build_payload(retained, "Fontes de mercado")
        self._store_artifact(payload, retained, retained[-1].data)
        artifact = self._precompute().read_artifact(str(payload["hash"]))
        result = artifact if artifact is not None else payload
        result = dict(result)
        result["erros_fontes"] = errors
        return result


__all__ = ["RESERVES_SOURCE", "ReservesTabController"]
