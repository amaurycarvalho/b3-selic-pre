"""Retenção de três anos do cache analítico do Tesouro Direto."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from b3_selic_pre.infrastructure.tesouro_analytics_cache import (
        TesouroAnalyticsCache,
    )

logger = logging.getLogger(__name__)

RETENTION_YEARS = 3
RETENTION_MONTHS = 36


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _partitions(manifest: dict[str, object]) -> dict[str, object]:
    return _as_dict(manifest.get("partitions"))


def _shift_months(value: date, months: int) -> date:
    total = value.year * 12 + (value.month - 1) + months
    year, month_index = divmod(total, 12)
    return date(year, month_index + 1, 1)


def _shift_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _latest_date(latest_data_date: str) -> date | None:
    try:
        return date.fromisoformat(
            latest_data_date
            if len(latest_data_date) == 10
            else f"{latest_data_date[:7]}-01"
        )
    except ValueError:
        return None


def expired(period: str, latest_data_date: str) -> bool:
    """Return whether a partition period is older than the retention cut."""
    if not period:
        return False
    latest_date = _latest_date(latest_data_date)
    if latest_date is None:
        return False
    if len(period) == 7:
        cutoff = _shift_months(latest_date, -RETENTION_MONTHS)
        return period < cutoff.isoformat()[:7]
    try:
        period_date = date.fromisoformat(period)
    except ValueError:
        return False
    return period_date < _shift_years(latest_date, -RETENTION_YEARS)


def run_housekeeping(
    cache: TesouroAnalyticsCache,
    latest_data_date: str,
) -> list[str]:
    """Remove expired partitions and update the manifest atomically."""
    manifest = cache.load_manifest()
    if manifest is None:
        return []
    partitions = dict(_partitions(manifest))
    removed: list[str] = []
    for name, raw in sorted(partitions.items()):
        period = str(_as_dict(raw).get("period") or "")
        if not expired(period, latest_data_date):
            continue
        try:
            cache.partition_path(name).unlink()
        except OSError:
            logger.warning(
                "Não foi possível remover a partição analítica %s.", name
            )
            continue
        partitions.pop(name, None)
        removed.append(name)
    if removed:
        manifest["partitions"] = partitions
        cache.write_manifest(manifest)
    return removed
