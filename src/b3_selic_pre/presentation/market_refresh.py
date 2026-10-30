"""Atualização via rede das fontes de mercado."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from b3_selic_pre.application.market.forecast import FocusExpectation
from b3_selic_pre.presentation.logging_utils import log_exception_once
from b3_selic_pre.presentation.market_sources import (
    B3_SOURCE,
    DOL_SOURCE,
    FETCH_DAYS,
    FOCUS_DOCUMENT,
    FOCUS_SOURCE,
    GOLD_SOURCE,
    SGS_SOURCE,
    YAHOO_SOURCE,
    _focus_payload,
    derive_gold_series,
    dol_ticker,
)

logger = logging.getLogger(__name__)


def _log_source_failure(exc: Exception, source: str) -> None:
    log_exception_once(logger, exc, f"Falha ao atualizar a fonte {source}")


class RefreshMixin:
    """Fetch every market source and persist raw data + precompute."""

    def _refresh_usd(self: RefreshMixin, inicio: str, today: str, errors: list[str]) -> None:
        try:
            quotes = self.services.sgs.fetch_series(inicio, today)  # type: ignore[attr-defined]
            if quotes:
                self._raw().write_quotes(SGS_SOURCE, quotes)
        except Exception as exc:
            _log_source_failure(exc, "BCB SGS 1")
            errors.append(f"BCB SGS 1: {exc}")
        try:
            quotes = self.services.b3.fetch_historical_exchange(  # type: ignore[attr-defined]
                inicio, today
            )
            if quotes:
                self._raw().write_quotes(B3_SOURCE, quotes)
        except Exception as exc:
            _log_source_failure(exc, "B3")
            errors.append(f"B3: {exc}")

    def _refresh_dol(self: RefreshMixin, today: str, errors: list[str]) -> None:
        try:
            quotes = self.services.b3.fetch_dol(  # type: ignore[attr-defined]
                dol_ticker(date.fromisoformat(today)),
                (date.fromisoformat(today) - timedelta(days=30)).isoformat(),
                today,
            )
            if quotes:
                self._raw().write_quotes(DOL_SOURCE, quotes)
        except Exception as exc:
            _log_source_failure(exc, "B3 DOL")
            errors.append(f"B3 DOL: {exc}")

    def _refresh_focus(
        self: RefreshMixin, errors: list[str]
    ) -> list[FocusExpectation]:
        try:
            expectations = self.services.focus.fetch_expectations()  # type: ignore[attr-defined]
        except Exception as exc:
            _log_source_failure(exc, "BCB Focus")
            errors.append(f"BCB Focus: {exc}")
            return []
        if expectations:
            self._raw().write_document(
                FOCUS_SOURCE, FOCUS_DOCUMENT, _focus_payload(expectations)
            )
        return expectations

    def _refresh_gold(self: RefreshMixin, inicio: str, today: str, errors: list[str]) -> None:
        try:
            xau = self.services.gold.fetch_series()  # type: ignore[attr-defined]
        except Exception as exc:
            _log_source_failure(exc, "Yahoo GC=F")
            errors.append(f"Yahoo GC=F: {exc}")
            return
        if not xau:
            return
        self._raw().write_quotes(YAHOO_SOURCE, xau)
        derived = derive_gold_series(
            self._usd_quotes(inicio, today), xau
        )
        if derived:
            self._raw().write_quotes(GOLD_SOURCE, derived)

    def refresh(self: RefreshMixin) -> dict[str, Any]:
        """Fetch every source, persist raw data and run the precompute."""
        today = self._today()
        inicio = (
            date.fromisoformat(today) - timedelta(days=FETCH_DAYS)
        ).isoformat()
        errors: list[str] = []
        self._refresh_usd(inicio, today, errors)
        self._refresh_dol(today, errors)
        focus = self._refresh_focus(errors)
        self._refresh_gold(inicio, today, errors)
        payload = self._build_payload(
            focus=focus or None,
            reference=self._latest() or today,
            origem="Fontes de mercado",
        )
        if payload is not None:
            latest = self._latest() or today
            key = self._key()
            signatures = self._signatures()
            try:
                if self._precompute().read_derived(key) is None:
                    self._precompute().write_derived(
                        key,
                        {
                            "janela": payload.get("janela"),
                            "series": payload.get("series"),
                            "indicadores": payload.get("indicadores"),
                        },
                        signatures,
                        latest,
                    )
            except Exception as exc:
                log_exception_once(
                    logger,
                    exc,
                    "Falha no pré-cálculo derivado de mercado",
                )
            self._precompute().update_if_changed(
                key, signatures, latest, lambda: payload
            )
            try:
                self._precompute().housekeeping(latest)
            except Exception as exc:
                log_exception_once(
                    logger,
                    exc,
                    "Falha no housekeeping do pré-cálculo de mercado",
                )
        result = self.load_cache_only()
        result["erros_fontes"] = errors
        return result
