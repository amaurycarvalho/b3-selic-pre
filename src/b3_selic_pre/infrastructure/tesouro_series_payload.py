"""Serialização dos snapshots de séries do Tesouro Direto."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from b3_selic_pre.application.tesouro import SeriesPoint, SeriesSourceSnapshot

SERIES_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class StoredSeries:
    """Snapshot lido do cache analítico."""

    name: str
    points: tuple[SeriesPoint, ...]
    latest_data_date: str
    source: str
    extracted_at: str | None
    titles: tuple[str, ...]
    source_hashes: dict[str, str]


def point_payload(point: SeriesPoint) -> dict[str, str]:
    """Return a JSON-friendly representation of a series point."""
    return {
        "period": point.period,
        "metric": point.metric,
        "value": str(point.value),
        "total": str(point.total),
        "dimension": point.dimension,
        "key": point.key,
    }


def point_from_payload(raw: object) -> SeriesPoint | None:
    """Parse a series point, returning ``None`` when it is invalid."""
    if not isinstance(raw, dict):
        return None
    try:
        return SeriesPoint(
            period=str(raw["period"]),
            metric=str(raw["metric"]),
            value=Decimal(str(raw["value"])),
            total=Decimal(str(raw["total"])),
            dimension=str(raw["dimension"]),
            key=str(raw["key"]),
        )
    except (KeyError, ValueError):
        return None


def payload_from_snapshot(
    snapshot: SeriesSourceSnapshot,
    *,
    source: str,
    extracted_at: str | None,
    hashes: Mapping[str, str],
) -> dict[str, object]:
    """Build the persisted payload of a source snapshot."""
    return {
        "schema_version": SERIES_SCHEMA_VERSION,
        "name": snapshot.name,
        "source_hashes": dict(hashes),
        "latest_data_date": snapshot.latest_data_date,
        "source": source,
        "extracted_at": extracted_at,
        "titles": list(snapshot.titles),
        "points": [point_payload(point) for point in snapshot.points],
    }


def _points(raw_points: object) -> tuple[SeriesPoint, ...] | None:
    if not isinstance(raw_points, list):
        return None
    points = tuple(
        point
        for point in (point_from_payload(raw) for raw in raw_points)
        if point is not None
    )
    if len(points) != len(raw_points):
        return None
    return points


def _texts(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    return tuple(str(item) for item in value)


def _hashes(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): str(item) for key, item in value.items()}


def stored_from_payload(payload: object) -> StoredSeries | None:
    """Parse a stored snapshot, returning ``None`` when it is invalid."""
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != SERIES_SCHEMA_VERSION:
        return None
    points = _points(payload.get("points"))
    hashes = _hashes(payload.get("source_hashes"))
    titles = _texts(payload.get("titles"))
    latest = payload.get("latest_data_date")
    name = payload.get("name")
    if points is None or hashes is None or titles is None:
        return None
    if not isinstance(latest, str) or not isinstance(name, str):
        return None
    extracted = payload.get("extracted_at")
    return StoredSeries(
        name=name,
        points=points,
        latest_data_date=latest,
        source=str(payload.get("source") or "Cache"),
        extracted_at=extracted if isinstance(extracted, str) else None,
        titles=titles,
        source_hashes=hashes,
    )


__all__ = [
    "SERIES_SCHEMA_VERSION",
    "StoredSeries",
    "payload_from_snapshot",
    "point_from_payload",
    "point_payload",
    "stored_from_payload",
]
