"""Construção do payload de mercado a partir apenas do cache local."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from typing import Any

from b3_selic_pre.application.market.cache_key import key_from_config
from b3_selic_pre.application.market.forecast import FocusExpectation, focus_target
from b3_selic_pre.application.market.indicators import compute_indicators
from b3_selic_pre.application.market.payloads import (
    AVISO_CENARIO,
    build_forecasts,
    market_payload,
)
from b3_selic_pre.application.market.series import (
    bucket_points,
    layered_buckets,
    series_from_quotes,
    stale_gold,
)
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    UNIDADE_OURO,
    UNIDADE_USD,
    Bucket,
    MarketQuote,
    PolicyIndicators,
    Resolution,
)
from b3_selic_pre.presentation.market_sources import (
    B3_SOURCE,
    DOL_SOURCE,
    FOCUS_DOCUMENT,
    FOCUS_SOURCE,
    GOLD_SOURCE,
    SGS_SOURCE,
    STALE_GAP_DAYS,
    WINDOW_DAYS,
    YAHOO_SOURCE,
    _as_dict,
    _parse_focus,
    derive_gold_series,
)


class PayloadMixin:
    """Build the shared market payload from raw cache files."""

    def _reference(self: PayloadMixin) -> str:
        raw = self._raw()
        candidates = [
            raw.last_date(source)
            for source in (SGS_SOURCE, B3_SOURCE, GOLD_SOURCE)
        ]
        dates = [value for value in candidates if value]
        return max(dates) if dates else self._today()

    def _window(self: PayloadMixin, reference: str) -> dict[str, str]:
        end = date.fromisoformat(reference)
        start = end - timedelta(days=WINDOW_DAYS)
        return {"inicio": start.isoformat(), "fim": reference}

    def _focus(self: PayloadMixin) -> list[FocusExpectation]:
        payload = self._raw().read_document(FOCUS_SOURCE, FOCUS_DOCUMENT)
        return _parse_focus(payload) if payload is not None else []

    def _dol(self: PayloadMixin) -> MarketQuote | None:
        last = self._raw().last_date(DOL_SOURCE)
        return (
            self._raw().read_quote(DOL_SOURCE, last) if last else None
        )

    def _signatures(self: PayloadMixin) -> dict[str, str]:
        raw = self._raw()
        signatures: dict[str, str] = {}
        for source in (SGS_SOURCE, B3_SOURCE, GOLD_SOURCE, DOL_SOURCE):
            last = raw.last_date(source)
            if last is None:
                continue
            payload = raw.read(source, last) or {}
            signatures[source] = f"{last}:{payload.get('hash', '')}"
        document = raw.read_document(FOCUS_SOURCE, FOCUS_DOCUMENT)
        if document is not None:
            signatures[FOCUS_SOURCE] = hashlib.sha256(
                json.dumps(document, sort_keys=True).encode("utf-8")
            ).hexdigest()
        return signatures

    def _key(self: PayloadMixin) -> str:
        return key_from_config(self._signatures(), self.config)

    def _latest(self: PayloadMixin) -> str | None:
        raw = self._raw()
        dates = [
            raw.last_date(source)
            for source in (SGS_SOURCE, B3_SOURCE, GOLD_SOURCE, DOL_SOURCE)
        ]
        valid = [value for value in dates if value]
        return max(valid) if valid else None

    def _usd_quotes(self: PayloadMixin, inicio: str, fim: str) -> list[MarketQuote]:
        raw = self._raw()
        quotes = raw.read_series(SGS_SOURCE, inicio, fim)
        if not quotes:
            quotes = raw.read_series(B3_SOURCE, inicio, fim)
        return quotes

    def _gold_quotes(
        self: PayloadMixin, inicio: str, fim: str, reference: str
    ) -> list[MarketQuote]:
        raw = self._raw()
        quotes = raw.read_series(GOLD_SOURCE, inicio, fim)
        if not quotes:
            quotes = derive_gold_series(
                self._usd_quotes(inicio, reference),
                raw.read_series(YAHOO_SOURCE, inicio, fim),
            )
        if quotes and quotes[-1].data < reference:
            gap = (
                date.fromisoformat(reference)
                - date.fromisoformat(quotes[-1].data)
            ).days
            if gap > STALE_GAP_DAYS:
                quotes[-1] = stale_gold(quotes[-1], self._now())
        return quotes

    def _buckets(
        self: PayloadMixin, quotes: list[MarketQuote], reference: str
    ) -> list[Bucket]:
        resolution = Resolution(self.options.resolucao)
        if resolution == Resolution.AUTO:
            return layered_buckets(quotes, reference, self.config)
        return bucket_points(quotes, resolution)

    def _series_parts(
        self: PayloadMixin,
        ativo: str,
        unidade: str,
        quotes: list[MarketQuote],
        reference: str,
    ) -> tuple[object, list[Bucket]] | None:
        buckets = self._buckets(quotes, reference)
        by_date = {quote.data: quote for quote in quotes}
        selected = [
            (bucket, by_date[bucket.fim])
            for bucket in buckets
            if bucket.fim in by_date
        ]
        if not selected:
            return None
        resolution = (
            Resolution.AUTO
            if self.options.resolucao == "auto"
            else Resolution(self.options.resolucao)
        )
        series = series_from_quotes(
            ativo, unidade, [quote for _, quote in selected], resolution
        )
        return series, [bucket for bucket, _ in selected]

    def _build_payload(
        self: PayloadMixin,
        focus: list[FocusExpectation] | None = None,
        reference: str | None = None,
        origem: str = "Cache",
    ) -> dict[str, Any] | None:
        reference = reference or self._reference()
        inicio = self._window(reference)["inicio"]
        usd = self._usd_quotes(inicio, reference)
        gold = self._gold_quotes(inicio, reference, reference)
        if not usd and not gold:
            return None
        series: dict[str, Any] = {}
        faixas: dict[str, list[Bucket]] = {}
        for ativo, unidade, quotes in (
            (ATIVO_USD, UNIDADE_USD, usd),
            (ATIVO_OURO, UNIDADE_OURO, gold),
        ):
            parts = self._series_parts(ativo, unidade, quotes, reference)
            if parts is not None:
                series[ativo], faixas[ativo] = parts
        expectations = focus if focus is not None else self._focus()
        usd_spot = usd[-1] if usd else None
        target = (
            focus_target(
                expectations, date.fromisoformat(reference),
                self.config.projecao.meses,
            )
            if expectations
            else None
        )
        indicators = (
            compute_indicators(
                usd,
                usd_spot,
                self.config,
                focus=target,
                dol_front=self._dol(),
                dias_ate_vencimento=self.config.projecao.dol_dias_vencimento,
            )
            if usd_spot is not None
            else PolicyIndicators(referencia=reference)
        )
        forecasts = build_forecasts(
            usd_spot,
            usd,
            gold,
            expectations,
            date.fromisoformat(reference),
            self.config,
        )
        window = self._window(reference)
        payload = market_payload(
            window,
            series,  # type: ignore[arg-type]
            forecasts,
            indicators,
            origem,
            self._now().isoformat(timespec="seconds"),
        )
        self._attach_ranges(payload, faixas)
        return payload

    @staticmethod
    def _attach_ranges(
        payload: dict[str, Any], faixas: dict[str, list[Bucket]]
    ) -> None:
        series = _as_dict(payload.get("series"))
        for ativo, buckets in faixas.items():
            items = _as_dict(series.get(ativo)).get("itens")
            if not isinstance(items, list):
                continue
            ranges = {bucket.fim: bucket for bucket in buckets}
            for item in items:
                bucket = ranges.get(str(_as_dict(item).get("data")))
                if bucket is not None:
                    item["minimo"] = bucket.minimo
                    item["maximo"] = bucket.maximo

    def _empty_payload(self: PayloadMixin, reference: str) -> dict[str, Any]:
        return {
            "janela": self._window(reference),
            "series": {},
            "previsao": {},
            "indicadores": {},
            "origem": "Cache",
            "gerado_em": self._now().isoformat(timespec="seconds"),
            "aviso": AVISO_CENARIO,
        }

    def load_precomputed_only(self: PayloadMixin) -> dict[str, Any] | None:
        """Read only the precomputed artifact without computing anything."""
        return self._precompute().read_artifact(self._key())

    def load_cache_only(self: PayloadMixin) -> dict[str, Any]:
        """Load the precomputed artifact or build the payload from cache only."""
        artifact = self.load_precomputed_only()
        if artifact is not None:
            return artifact
        reference = self._reference()
        payload = self._build_payload(reference=reference)
        return payload or self._empty_payload(reference)
