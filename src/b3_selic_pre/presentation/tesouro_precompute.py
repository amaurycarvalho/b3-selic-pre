"""Orquestração do pré-cálculo das séries do Tesouro Direto."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Mapping
from typing import Protocol

from b3_selic_pre.application.tesouro import (
    SeriesSourceSnapshot,
    build_demanda_snapshot,
    build_estoque_snapshot,
    build_fluxo_snapshot,
)
from b3_selic_pre.presentation.tesouro_analise_controller import AnaliseData
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
)

logger = logging.getLogger(__name__)

SnapshotBuilder = Callable[[], SeriesSourceSnapshot | None]


class PrecomputeCache(Protocol):
    """Adapter used to persist precomputed series snapshots."""

    def expected_hashes(
        self: PrecomputeCache, name: str
    ) -> dict[str, str] | None:
        """Return the current hashes of a snapshot's raw sources."""

    def update_if_changed(
        self: PrecomputeCache,
        name: str,
        expected_hashes: Mapping[str, str] | None,
        build: SnapshotBuilder,
        *,
        source: str,
        extracted_at: str | None,
    ) -> bool:
        """Build and persist a snapshot only when its source changed."""


class TesouroPrecompute:
    """Builds source snapshots after a refresh, skipping unchanged sources."""

    def __init__(
        self: TesouroPrecompute, series_cache: PrecomputeCache | None
    ) -> None:
        """Store the injected series cache adapter."""
        self._cache = series_cache

    def __call__(
        self: TesouroPrecompute, kind: str, data: AnaliseData | None
    ) -> None:
        """Run the precompute without propagating failures."""
        if data is None or self._cache is None:
            return
        try:
            self.run(kind, data)
        except Exception as exc:
            logger.warning("Falha no pré-cálculo do Tesouro: %s", exc)

    def run(self: TesouroPrecompute, kind: str, data: AnaliseData) -> None:
        """Build only the sources refreshed by the sub-tab."""
        for name, build in self._targets(kind, data):
            hashes = self._cache.expected_hashes(name)
            if hashes is None:
                continue
            self._cache.update_if_changed(
                name,
                hashes,
                build,
                source=data.source,
                extracted_at=data.extracted_at,
            )

    def _targets(
        self: TesouroPrecompute, kind: str, data: AnaliseData
    ) -> Iterator[tuple[str, SnapshotBuilder]]:
        if kind in (KIND_ESTOQUE, KIND_VISAO_GERAL) and data.estoque:
            yield "estoque", lambda: build_estoque_snapshot(data.estoque)
        if kind in (KIND_APETITE, KIND_VISAO_GERAL) and data.vendas:
            yield "demanda", lambda: build_demanda_snapshot(data.vendas)
        if kind == KIND_APETITE and (data.vendas or data.resgates):
            yield "fluxo", lambda: build_fluxo_snapshot(
                data.vendas, data.resgates
            )


__all__ = ["TesouroPrecompute"]
