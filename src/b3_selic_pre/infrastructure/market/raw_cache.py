"""Cache bruto de mercado por fonte e data, com TTL por recência."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.infrastructure.cache_payload import write_atomic
from b3_selic_pre.infrastructure.market.raw_index import last_date, missing_dates
from b3_selic_pre.infrastructure.market.raw_ttl import is_fresh, ttl_minutes
from b3_selic_pre.infrastructure.xdg import cache_base

RAW_SCHEMA_VERSION = 1


def market_cache_root() -> Path:
    """Return the default root of the market cache."""
    return cache_base() / "b3-selic-pre" / "market"


def _payload_hash(
    fonte: str, data: str, valor: float, extraido_em: str
) -> str:
    content = f"{fonte}|{data}|{valor:.10f}|{extraido_em}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class MarketRawCache:
    """Stores one normalized raw quote per source and date."""

    def __init__(
        self: MarketRawCache,
        cache_dir: str | Path | None = None,
        config: MarketConfig | None = None,
    ) -> None:
        """Initialize the raw cache under ``cache_dir``."""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else market_cache_root()
        )
        self.config = config or MarketConfig()
        self.raw_dir = self.cache_dir / "raw"

    def path(self: MarketRawCache, fonte: str, data: str) -> Path:
        """Return the raw payload path for a source and date."""
        return self.raw_dir / fonte / f"{data}.json"

    def write_quote(
        self: MarketRawCache, fonte: str, quote: MarketQuote, defasado: bool | None = None
    ) -> bool:
        """Write a normalized quote atomically, never persisting empties."""
        if not math.isfinite(quote.valor):
            return False
        if _parse_date(quote.data) is None:
            return False
        target = self.path(fonte, quote.data)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": RAW_SCHEMA_VERSION,
            "fonte": fonte,
            "data": quote.data,
            "ativo": quote.ativo,
            "valor": quote.valor,
            "unidade": quote.unidade,
            "origem": quote.origem,
            "metodo": quote.metodo,
            "extraido_em": quote.extraido_em,
            "defasagem_horas": quote.defasagem_horas,
            "defasado": (
                quote.defasado if defasado is None else defasado
            ),
            "cached_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "hash": _payload_hash(
                fonte, quote.data, quote.valor, quote.extraido_em
            ),
        }
        write_atomic(target, json.dumps(payload, ensure_ascii=False))
        return True

    def write_quotes(
        self: MarketRawCache, fonte: str, quotes: Sequence[MarketQuote]
    ) -> int:
        """Write every quote, returning how many were persisted."""
        return sum(1 for quote in quotes if self.write_quote(fonte, quote))

    def read(self: MarketRawCache, fonte: str, data: str) -> dict[str, object] | None:
        """Read one raw payload without modifying the cache."""
        target = self.path(fonte, data)
        if not target.exists():
            return None
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("schema_version") != RAW_SCHEMA_VERSION:
            return None
        if payload.get("fonte") != fonte or payload.get("data") != data:
            return None
        return payload

    def read_quote(self: MarketRawCache, fonte: str, data: str) -> MarketQuote | None:
        """Read one raw payload as a :class:`MarketQuote`."""
        payload = self.read(fonte, data)
        if payload is None:
            return None
        try:
            return MarketQuote(
                data=str(payload["data"]),
                ativo=str(payload["ativo"]),
                valor=float(payload["valor"]),
                unidade=str(payload["unidade"]),
                origem=str(payload["origem"]),
                metodo=str(payload["metodo"]),
                extraido_em=str(payload["extraido_em"]),
                defasagem_horas=payload.get("defasagem_horas"),  # type: ignore[arg-type]
            )
        except (KeyError, TypeError, ValueError):
            return None

    def document_path(self: MarketRawCache, fonte: str, name: str) -> Path:
        """Return the path of a non-date raw document."""
        return self.raw_dir / fonte / name

    def write_document(
        self: MarketRawCache, fonte: str, name: str, payload: dict[str, object]
    ) -> bool:
        """Write a non-date source document atomically when non-empty."""
        if not payload:
            return False
        target = self.document_path(fonte, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "schema_version": RAW_SCHEMA_VERSION,
            "fonte": fonte,
            "hash": hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "cached_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "payload": payload,
        }
        write_atomic(target, json.dumps(document, ensure_ascii=False))
        return True

    def read_document(
        self: MarketRawCache, fonte: str, name: str
    ) -> dict[str, object] | None:
        """Read a non-date source document without modifying the cache."""
        target = self.document_path(fonte, name)
        if not target.exists():
            return None
        try:
            document = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(document, dict):
            return None
        if document.get("schema_version") != RAW_SCHEMA_VERSION:
            return None
        payload = document.get("payload")
        return payload if isinstance(payload, dict) else None

    def read_series(
        self: MarketRawCache,
        fonte: str,
        inicio: str | None = None,
        fim: str | None = None,
    ) -> list[MarketQuote]:
        """Read all valid quotes for a source in the requested window."""
        directory = self.raw_dir / fonte
        if not directory.exists():
            return []
        quotes: list[MarketQuote] = []
        for target in sorted(directory.glob("*.json")):
            day = _parse_date(target.stem)
            if day is None:
                continue
            if inicio is not None and target.stem < inicio:
                continue
            if fim is not None and target.stem > fim:
                continue
            quote = self.read_quote(fonte, target.stem)
            if quote is not None:
                quotes.append(quote)
        return quotes



    def last_date(
        self: MarketRawCache, fonte: str | None = None
    ) -> str | None:
        """Return the newest valid date, optionally for one source."""
        return last_date(self, fonte)

    def ttl_minutes(
        self: MarketRawCache, data_date: str, reference: str | None = None
    ) -> int | None:
        """Return the TTL for a data date, or ``None`` when immutable."""
        return ttl_minutes(self.config, data_date, reference)

    def is_fresh(
        self: MarketRawCache, fonte: str, data: str, reference: str | None = None
    ) -> bool:
        """Return whether a cached entry is still valid for its recency."""
        return is_fresh(self, fonte, data, reference)

    def missing_dates(
        self: MarketRawCache, fonte: str, inicio: str, fim: str
    ) -> list[str]:
        """Return business days in the window without a cache entry."""
        return missing_dates(self, fonte, inicio, fim)


__all__ = ["RAW_SCHEMA_VERSION", "MarketRawCache", "market_cache_root"]
