"""Retenção de três anos do cache bruto e derivado de mercado."""

from __future__ import annotations

import logging
import shutil
from datetime import date
from pathlib import Path

from b3_selic_pre.infrastructure.market.precompute_cache import (
    MarketPrecomputeCache,
)
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache

RETENTION_YEARS = 3

logger = logging.getLogger(__name__)


def shift_years(value: date, years: int) -> date:
    """Shift a date by whole years, clamping February 29."""
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def cutoff(reference: str, years: int = RETENTION_YEARS) -> date | None:
    """Return the retention cutoff relative to a reference date."""
    try:
        parsed = date.fromisoformat(reference)
    except (TypeError, ValueError):
        return None
    return shift_years(parsed, -years)


def expired(
    data_date: str, reference: str, years: int = RETENTION_YEARS
) -> bool:
    """Return whether ``data_date`` is older than the retention window."""
    limit = cutoff(reference, years)
    try:
        parsed = date.fromisoformat(data_date)
    except (TypeError, ValueError):
        return False
    if limit is None:
        return False
    return parsed < limit


def _remove(path: Path) -> bool:
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return True
    except OSError:
        logger.warning("Não foi possível remover %s do cache de mercado.", path)
        return False


def run_raw_housekeeping(
    cache: MarketRawCache, reference: str
) -> list[str]:
    """Remove raw files older than the retention window."""
    if not cache.raw_dir.exists():
        return []
    removed: list[str] = []
    for source_dir in sorted(cache.raw_dir.glob("*")):
        if not source_dir.is_dir():
            continue
        for target in sorted(source_dir.glob("*.json")):
            if expired(target.stem, reference) and _remove(target):
                removed.append(str(target))
    return removed


def run_precompute_housekeeping(
    cache: MarketPrecomputeCache, reference: str
) -> list[str]:
    """Remove derived/precomputed keys older than the retention window."""
    manifest = cache.load_manifest()
    if manifest is None:
        return []
    entries = manifest.get("keys")
    if not isinstance(entries, dict):
        return []
    kept: dict[str, object] = {}
    removed: list[str] = []
    for key, raw in sorted(entries.items()):
        entry = raw if isinstance(raw, dict) else {}
        latest = str(entry.get("latest_data_date") or "")
        if latest and expired(latest, reference):
            _remove(cache.derived_path(key).parent)
            _remove(cache.artifact_path(key).parent)
            removed.append(key)
        else:
            kept[key] = raw
    if removed:
        manifest["keys"] = kept
        cache.write_manifest(manifest)
    return removed


def run_housekeeping(
    cache_dir: str | Path, reference: str
) -> dict[str, list[str]]:
    """Run raw and precompute housekeeping for the market cache."""
    raw = MarketRawCache(cache_dir)
    precompute = MarketPrecomputeCache(cache_dir)
    return {
        "raw": run_raw_housekeeping(raw, reference),
        "precomputed": run_precompute_housekeeping(precompute, reference),
    }


__all__ = [
    "RETENTION_YEARS",
    "cutoff",
    "expired",
    "run_housekeeping",
    "run_precompute_housekeeping",
    "run_raw_housekeeping",
    "shift_years",
]
