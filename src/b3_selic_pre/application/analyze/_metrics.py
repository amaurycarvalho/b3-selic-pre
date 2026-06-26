from dataclasses import dataclass
from typing import Optional

import numpy as np

from b3_selic_pre.domain.models import RateRecord


@dataclass
class SegmentMetrics:
    taxa_inicial: float = 0.0
    taxa_final: float = 0.0
    delta: float = 0.0
    slope: Optional[float] = None


@dataclass
class DetailedMetrics:
    taxa_inicial: float
    taxa_final: float
    taxa_minima: float
    taxa_maxima: float
    amplitude: float
    delta_final: float
    slope_global: float
    curto: SegmentMetrics
    medio: SegmentMetrics
    longo: SegmentMetrics
    indice_suavidade: float
    indice_minimo_global: int
    indice_maximo_global: int
    maximos_locais: list[int]
    minimos_locais: list[int]
    qtd_maximos: int
    qtd_minimos: int
    qtd_mudancas: int
    qtd_inflexoes: int
    indice_oscilacao: float
    indice_monotonia: float
    indice_convexidade: float
    indice_volatilidade: float


def _smooth_rates(rates: list[float], window: int = 5) -> list[float]:
    if len(rates) < window:
        return list(rates)
    arr = np.array(rates)
    kernel = np.ones(window) / window
    smoothed = np.convolve(arr, kernel, mode="same")
    return [float(x) for x in smoothed]


def _rates_from_records(records: list[RateRecord]) -> list[float]:
    return [float(r.rate.replace(",", ".")) for r in records]


def _days_from_records(records: list[RateRecord]) -> list[int]:
    return [r.day252 for r in records]


def _segment_metrics(
    rates: list[float],
    days: list[int],
    start_du: int,
    end_du: int,
) -> SegmentMetrics:
    indices = [i for i, d in enumerate(days) if start_du <= d <= end_du]
    if not indices:
        return SegmentMetrics()
    seg_rates = [rates[i] for i in indices]
    taxa_inicial = seg_rates[0]
    taxa_final = seg_rates[-1]
    delta = taxa_final - taxa_inicial
    slope = None
    if len(seg_rates) >= 2:
        x = np.arange(len(seg_rates))
        coef = np.polyfit(x, seg_rates, 1)
        slope = float(coef[0])
    return SegmentMetrics(
        taxa_inicial=taxa_inicial,
        taxa_final=taxa_final,
        delta=delta,
        slope=slope,
    )


def extract_detailed_metrics(
    records: list[RateRecord],
) -> DetailedMetrics:
    if not records:
        return DetailedMetrics(
            taxa_inicial=0.0,
            taxa_final=0.0,
            taxa_minima=0.0,
            taxa_maxima=0.0,
            amplitude=0.0,
            delta_final=0.0,
            slope_global=0.0,
            curto=SegmentMetrics(),
            medio=SegmentMetrics(),
            longo=SegmentMetrics(),
            indice_suavidade=0.0,
            indice_minimo_global=0,
            indice_maximo_global=0,
            maximos_locais=[],
            minimos_locais=[],
            qtd_maximos=0,
            qtd_minimos=0,
            qtd_mudancas=0,
            qtd_inflexoes=0,
            indice_oscilacao=0.0,
            indice_monotonia=0.0,
            indice_convexidade=0.0,
            indice_volatilidade=0.0,
        )

    rates = _rates_from_records(records)
    days = _days_from_records(records)
    n = len(rates)

    taxa_inicial = rates[0]
    taxa_final = rates[-1]
    taxa_maxima = max(rates)
    taxa_minima = min(rates)
    indice_minimo_global = rates.index(taxa_minima)
    indice_maximo_global = rates.index(taxa_maxima)
    amplitude = taxa_maxima - taxa_minima
    delta_final = taxa_final - taxa_inicial
    slope_global = 0.0
    if n >= 2:
        slope_global = float(np.polyfit(days, rates, 1)[0])

    max_du = max(days)
    curto = _segment_metrics(rates, days, 0, 252)
    medio = _segment_metrics(rates, days, 253, 504)
    longo = _segment_metrics(rates, days, 505, max_du)

    indice_suavidade = 0.0
    if n >= 2:
        diffs = np.diff(rates)
        indice_suavidade = float(np.std(diffs, ddof=0))

    smooth = _smooth_rates(rates)

    maximos = []
    minimos = []
    if n >= 5:
        w = max(5, min(n // 20, 11))
        half = w // 2
        for i in range(half, n - half):
            window = smooth[i - half : i + half + 1]
            if smooth[i] == max(window):
                maximos.append(i)
            if smooth[i] == min(window):
                minimos.append(i)

    qtd_mudancas = 0
    if n >= 3:
        slopes = [rates[i + 1] - rates[i] for i in range(n - 1)]
        for i in range(1, len(slopes)):
            if slopes[i] * slopes[i - 1] < 0:
                qtd_mudancas += 1

    qtd_inflexoes = 0
    if n >= 4:
        slopes = [rates[i + 1] - rates[i] for i in range(n - 1)]
        curvaturas = [slopes[i + 1] - slopes[i] for i in range(len(slopes) - 1)]
        for i in range(1, len(curvaturas)):
            if curvaturas[i] * curvaturas[i - 1] < 0:
                qtd_inflexoes += 1

    indice_oscilacao = 0.0
    if n > 2:
        indice_oscilacao = qtd_mudancas / (n - 2)

    indice_monotonia = 0.0
    if n >= 3:
        deltas = [rates[i + 1] - rates[i] for i in range(n - 1)]
        pos = sum(1 for d in deltas if d > 0)
        neg = sum(1 for d in deltas if d < 0)
        total_diffs = len(deltas)
        if total_diffs > 0:
            indice_monotonia = max(pos, neg) / total_diffs

    indice_convexidade = 0.0
    if n >= 3:
        try:
            x_norm = np.linspace(0.0, 1.0, n)
            coef = np.polyfit(x_norm, rates, 2)
            indice_convexidade = float(coef[0])
        except np.linalg.LinAlgError:
            indice_convexidade = 0.0

    indice_volatilidade = 0.0
    if amplitude < 1e-9:
        indice_volatilidade = 0.0
    else:
        indice_volatilidade = indice_suavidade / amplitude

    return DetailedMetrics(
        taxa_inicial=taxa_inicial,
        taxa_final=taxa_final,
        taxa_minima=taxa_minima,
        taxa_maxima=taxa_maxima,
        amplitude=amplitude,
        delta_final=delta_final,
        slope_global=slope_global,
        curto=curto,
        medio=medio,
        longo=longo,
        indice_suavidade=indice_suavidade,
        indice_minimo_global=indice_minimo_global,
        indice_maximo_global=indice_maximo_global,
        maximos_locais=maximos,
        minimos_locais=minimos,
        qtd_maximos=len(maximos),
        qtd_minimos=len(minimos),
        qtd_mudancas=qtd_mudancas,
        qtd_inflexoes=qtd_inflexoes,
        indice_oscilacao=indice_oscilacao,
        indice_monotonia=indice_monotonia,
        indice_convexidade=indice_convexidade,
        indice_volatilidade=indice_volatilidade,
    )
