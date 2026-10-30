"""Retenção de três anos do snapshot de reservas."""

from __future__ import annotations

from b3_selic_pre.application.reserves.config import RETENCAO_ANOS
from b3_selic_pre.application.reserves.series import retained_points
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache


def run_snapshot_housekeeping(
    cache: MarketRawCache,
    fonte: str,
    reference: str,
    years: int = RETENCAO_ANOS,
) -> list[str]:
    """Prune snapshot points older than the retention window.

    The snapshot is the only storage unit, so pruning rewrites the same
    file. Corrupted snapshots are ignored without interrupting the caller.
    """
    points = cache.read_snapshot_points(fonte)
    if not points:
        return []
    kept = retained_points(points, reference, years)
    kept_dates = {point.data for point in kept}
    removed = [point.data for point in points if point.data not in kept_dates]
    if removed:
        cache.write_snapshot(fonte, kept)
    return removed


__all__ = ["run_snapshot_housekeeping"]
