"""Snapshot normalizado por fonte do cache bruto de mercado."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from b3_selic_pre.application.reserves.series import (
    points_hash,
    retained_points,
)
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import (
    ATIVO_RESERVAS,
    METODO_RESERVAS,
    UNIDADE_RESERVAS,
)
from b3_selic_pre.infrastructure.cache_payload import write_atomic

if TYPE_CHECKING:
    from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache

RAW_SCHEMA_VERSION = 1
SNAPSHOT_NAME = "snapshot.json"


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _valid_points(
    points: Sequence[MarketQuote],
) -> list[MarketQuote]:
    valid = [
        point
        for point in points
        if point.data and math.isfinite(point.valor)
    ]
    valid.sort(key=lambda point: point.data)
    return valid


def _same_snapshot(
    existing: dict[str, object] | None,
    digest: str,
    unidade: str,
    metodo: str,
    source: str,
) -> bool:
    if existing is None:
        return False
    return (
        existing.get("hash") == digest
        and existing.get("unit") == unidade
        and existing.get("method") == metodo
        and existing.get("source") == source
    )


def _snapshot_payload(
    valid: Sequence[MarketQuote],
    digest: str,
    unidade: str,
    metodo: str,
    fonte: str,
    source: str,
) -> dict[str, object]:
    extracted = valid[-1].extraido_em or datetime.now(UTC).isoformat(
        timespec="seconds"
    )
    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "source": source,
        "fonte": fonte,
        "unit": unidade,
        "unidade": unidade,
        "method": metodo,
        "metodo": metodo,
        "extracted_at": extracted,
        "extraido_em": extracted,
        "points": [
            {"date": point.data, "value": point.valor}
            for point in valid
        ],
        "hash": digest,
        "cached_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def _point_from_item(
    item: object,
    unidade: str,
    origem: str,
    metodo: str,
    extraido_em: str,
) -> MarketQuote | None:
    if not isinstance(item, dict):
        return None
    day = item.get("date", item.get("data"))
    value = item.get("value", item.get("valor"))
    if not isinstance(day, str):
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if _parse_date(day) is None or not math.isfinite(parsed):
        return None
    return MarketQuote(
        data=day,
        ativo=ATIVO_RESERVAS,
        valor=parsed,
        unidade=unidade,
        origem=origem,
        metodo=metodo,
        extraido_em=extraido_em,
    )


class SnapshotMixin:
    """Store one normalized and canonical snapshot per market source."""

    raw_dir: Path

    def snapshot_path(self: SnapshotMixin, fonte: str) -> Path:
        """Return the normalized snapshot path for a source."""
        return self.raw_dir / fonte / SNAPSHOT_NAME

    def write_snapshot(
        self: SnapshotMixin,
        fonte: str,
        points: Sequence[MarketQuote],
        *,
        unidade: str = UNIDADE_RESERVAS,
        metodo: str = METODO_RESERVAS,
        source: str | None = None,
    ) -> bool:
        """Write a canonical source snapshot only when its pairs change."""
        valid = _valid_points(points)
        if not valid:
            return False
        digest = points_hash(valid)
        chosen_source = source or fonte
        if _same_snapshot(
            self.read_snapshot(fonte),
            digest,
            unidade,
            metodo,
            chosen_source,
        ):
            return False
        payload = _snapshot_payload(
            valid, digest, unidade, metodo, fonte, chosen_source
        )
        target = self.snapshot_path(fonte)
        target.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(target, json.dumps(payload, ensure_ascii=False))
        return True

    def read_snapshot(
        self: SnapshotMixin, fonte: str
    ) -> dict[str, object] | None:
        """Read a normalized source snapshot without modifying the cache."""
        target = self.snapshot_path(fonte)
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
        points = payload.get("points")
        if not isinstance(points, list):
            return None
        return payload

    def read_snapshot_points(
        self: SnapshotMixin, fonte: str
    ) -> list[MarketQuote]:
        """Read a normalized snapshot as domain quotes."""
        payload = self.read_snapshot(fonte)
        if payload is None:
            return []
        origem = str(payload.get("source") or fonte)
        unidade = str(payload.get("unit") or UNIDADE_RESERVAS)
        metodo = str(payload.get("method") or METODO_RESERVAS)
        extraido_em = str(payload.get("extracted_at") or "")
        quotes: list[MarketQuote] = []
        for item in payload.get("points", []) or []:
            point = _point_from_item(
                item, unidade, origem, metodo, extraido_em
            )
            if point is not None:
                quotes.append(point)
        return sorted(quotes, key=lambda quote: quote.data)

    def prune_snapshot(
        self: SnapshotMixin,
        fonte: str,
        reference: str,
        years: int = 3,
    ) -> list[str]:
        """Remove snapshot points older than the retention window."""
        points = self.read_snapshot_points(fonte)
        if not points:
            return []
        kept = retained_points(points, reference, years)
        kept_dates = {point.data for point in kept}
        removed = [
            point.data for point in points if point.data not in kept_dates
        ]
        if removed:
            self.write_snapshot(fonte, kept)
        return removed

    def snapshot_last_date(
        self: SnapshotMixin, fonte: str
    ) -> str | None:
        """Return the newest date in a normalized source snapshot."""
        points = self.read_snapshot_points(fonte)
        return points[-1].data if points else None

    def snapshot_ttl_minutes(
        self: SnapshotMixin, fonte: str, reference: str | None = None
    ) -> int | None:
        """Return the snapshot TTL based on its newest point's recency."""
        latest = self.snapshot_last_date(fonte)
        if latest is None:
            return None
        cache: MarketRawCache = self  # type: ignore[assignment]
        return cache.ttl_minutes(latest, reference)

    def is_snapshot_fresh(
        self: SnapshotMixin, fonte: str, reference: str | None = None
    ) -> bool:
        """Return whether a snapshot is still valid for its recency."""
        payload = self.read_snapshot(fonte)
        if payload is None:
            return False
        latest = self.snapshot_last_date(fonte)
        if latest is None:
            return False
        cache: MarketRawCache = self  # type: ignore[assignment]
        ttl = cache.ttl_minutes(latest, reference)
        if ttl is None:
            return True
        raw = payload.get("cached_at")
        if not isinstance(raw, str):
            return False
        try:
            cached_at = datetime.fromisoformat(raw)
        except ValueError:
            return False
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=UTC)
        return datetime.now(UTC) - cached_at < timedelta(
            minutes=ttl
        )


__all__ = ["RAW_SCHEMA_VERSION", "SNAPSHOT_NAME", "SnapshotMixin"]
