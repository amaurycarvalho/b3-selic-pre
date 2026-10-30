"""Leitura das séries pré-calculadas do Tesouro Direto."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from b3_selic_pre.application.tesouro import (
    CachedTesouroSeriesProvider,
    SeriesPoint,
)
from b3_selic_pre.presentation.tesouro_analise_data import AnaliseData
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
)

_KIND_SOURCES = {
    KIND_ESTOQUE: ("estoque",),
    KIND_APETITE: ("demanda", "fluxo"),
    KIND_VISAO_GERAL: ("estoque", "demanda"),
}


class StoredSeriesLike(Protocol):
    """Snapshot shape consumed by the loader."""

    points: Sequence[SeriesPoint]
    latest_data_date: str
    source: str
    extracted_at: str | None
    titles: Sequence[str]


class SeriesCache(Protocol):
    """Adapter used to read precomputed series snapshots."""

    def expected_hashes(
        self: SeriesCache, name: str
    ) -> dict[str, str] | None:
        """Return the current hashes of a snapshot's raw sources."""
        return None

    def read(
        self: SeriesCache,
        name: str,
        expected_hashes: dict[str, str] | None = None,
    ) -> StoredSeriesLike | None:
        """Read a snapshot."""
        return None

    def has(self: SeriesCache, name: str) -> bool:
        """Return whether a snapshot exists."""
        return False


def _snapshot(
    series_cache: SeriesCache | None, name: str
) -> StoredSeriesLike | None:
    if series_cache is None:
        return None
    expected = series_cache.expected_hashes(name)
    return series_cache.read(name, expected_hashes=expected)


def _points(
    stored: dict[str, StoredSeriesLike], name: str
) -> Sequence[SeriesPoint]:
    payload = stored.get(name)
    return payload.points if payload is not None else ()


def _provider(
    stored: dict[str, StoredSeriesLike],
) -> CachedTesouroSeriesProvider:
    return CachedTesouroSeriesProvider(
        estoque=_points(stored, "estoque"),
        demanda=_points(stored, "demanda"),
        fluxo=_points(stored, "fluxo"),
    )


def _titles(stored: dict[str, StoredSeriesLike]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                title
                for payload in stored.values()
                for title in payload.titles
            }
        )
    )


def _fluxo_latest(stored: dict[str, StoredSeriesLike]) -> str | None:
    payload = stored.get("fluxo")
    return payload.latest_data_date if payload is not None else None


def series_data(
    series_cache: SeriesCache | None, kind: str
) -> AnaliseData | None:
    """Build sub-tab data from precomputed series when present."""
    if series_cache is None:
        return None
    stored: dict[str, StoredSeriesLike] = {}
    for name in _KIND_SOURCES[kind]:
        payload = _snapshot(series_cache, name)
        if payload is None:
            return None
        stored[name] = payload
    reference = stored.get("estoque") or stored["demanda"]
    return AnaliseData(
        provider=_provider(stored),
        titles=_titles(stored),
        latest_data_date=reference.latest_data_date,
        source=reference.source,
        extracted_at=reference.extracted_at,
        fluxo_latest_data_date=_fluxo_latest(stored),
    )


def series_available(
    series_cache: SeriesCache | None, kind: str
) -> bool:
    """Return whether every snapshot needed by a sub-tab exists."""
    if series_cache is None:
        return False
    return all(
        series_cache.has(name) for name in _KIND_SOURCES[kind]
    )


__all__ = [
    "SeriesCache",
    "StoredSeriesLike",
    "series_available",
    "series_data",
]
