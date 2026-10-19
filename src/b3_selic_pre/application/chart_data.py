"""Transformações puras de dados usadas pelos gráficos de taxas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from b3_selic_pre.application.use_cases import average_rate_by_year
from b3_selic_pre.domain.models import RateRecord

if TYPE_CHECKING:
    import numpy as np


def nearest_ticks(
    all_values: list[int],
    targets: range,
    tolerance: int,
    exclude_set: set[int] | None = None,
) -> list[int]:
    """Seleciona, entre os valores disponíveis, os mais próximos dos alvos."""
    result = []
    seen = set(exclude_set) if exclude_set else set()
    for target in targets:
        nearest = min(all_values, key=lambda d: abs(d - target))
        if abs(nearest - target) <= tolerance and nearest not in seen:
            result.append(nearest)
            seen.add(nearest)
    return result


def interpolate_rates(records: list[RateRecord], common_x: np.ndarray) -> np.ndarray:
    """Interpola as taxas dos registros na grade comum de dias úteis."""
    import numpy as np

    days = [r.day252 for r in records]
    rates = [float(r.rate.replace(",", ".")) for r in records]
    return np.interp(common_x, days, rates, left=np.nan, right=np.nan)


def nearest_rate(
    day_rates: dict[int, float], pos: int, tolerance: int
) -> float | None:
    """Devolve a taxa mais próxima de ``pos`` dentro de ``tolerance``."""
    nearest = min(day_rates.keys(), key=lambda d: abs(d - pos))
    if abs(nearest - pos) <= tolerance:
        return day_rates[nearest]
    return None


def consolidated_3d_data(
    date_rates: dict[str, list[RateRecord]], dates_sorted: list[str]
) -> tuple[list[dict[int, float]], np.ndarray, np.ndarray]:
    """Constrói as grades X/Z consolidadas por ano para a superfície 3D."""
    import numpy as np

    per_date_rates = [average_rate_by_year(date_rates[d]) for d in dates_sorted]
    all_years = set()
    for rates in per_date_rates:
        all_years.update(rates.keys())
    years = sorted(y for y in all_years if 0 <= y <= 20)
    X = np.tile(np.array(years), (len(dates_sorted), 1))
    Z = np.array([
        [rates.get(y, np.nan) for y in years]
        for rates in per_date_rates
    ])
    return per_date_rates, X, Z


def daily_3d_data(
    date_rates: dict[str, list[RateRecord]], dates_sorted: list[str]
) -> tuple[list[tuple[list[int], list[float]]], np.ndarray, np.ndarray]:
    """Constrói as grades X/Z por dia útil para a superfície 3D."""
    import numpy as np

    per_date_data = []
    all_days = set()
    for date_str in dates_sorted:
        records = date_rates[date_str]
        days = [r.day252 for r in records if r.day252 <= 756]
        rates = [float(r.rate.replace(",", ".")) for r in records if r.day252 <= 756]
        per_date_data.append((days, rates))
        all_days.update(days)
    max_day = max(all_days) if all_days else 0
    common_x = np.linspace(0, max_day, num=200)
    X = np.tile(common_x, (len(dates_sorted), 1))
    Z = np.array([
        np.interp(common_x, days, rates, left=np.nan, right=np.nan)
        for days, rates in per_date_data
    ])
    return per_date_data, X, Z


def interpolate_3d_surface(
    X: np.ndarray, Z: np.ndarray, z_indices: list[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Interpola a superfície 3D em uma grade fina entre as datas."""
    import numpy as np

    z_arr = np.array(z_indices)
    y_fine = np.linspace(z_arr.min(), z_arr.max(), len(z_indices) * 20)
    X_fine = np.full((len(y_fine), X.shape[1]), np.nan)
    Y_fine = np.tile(y_fine, (X.shape[1], 1)).T
    Z_fine = np.full((len(y_fine), Z.shape[1]), np.nan)
    for j in range(Z.shape[1]):
        col = Z[:, j]
        good = ~np.isnan(col)
        if good.sum() >= 2:
            Z_fine[:, j] = np.interp(y_fine, z_arr[good], col[good])
            X_fine[:, j] = np.interp(y_fine, z_arr[good], X[good, j])
        elif good.sum() == 1:
            Z_fine[:, j] = col[good][0]
            X_fine[:, j] = X[good, j].mean()
        else:
            Z_fine[:, j] = np.nan
            X_fine[:, j] = np.nan
    return X_fine, Y_fine, Z_fine
