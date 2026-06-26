from dataclasses import dataclass
from typing import Optional

import numpy as np

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.application.analyze._thresholds import AnalysisThresholds


@dataclass
class DetailedMetrics:
    taxa_inicial: float
    taxa_final: float
    taxa_maxima: float
    taxa_minima: float
    slope: Optional[float]
    convexidade: Optional[float]
    volatilidade: Optional[float]
    oscilacoes: int


def extract_detailed_metrics(
    records: list[RateRecord],
    thresholds: AnalysisThresholds,
) -> DetailedMetrics:
    if not records:
        return DetailedMetrics(
            taxa_inicial=0.0,
            taxa_final=0.0,
            taxa_maxima=0.0,
            taxa_minima=0.0,
            slope=None,
            convexidade=None,
            volatilidade=None,
            oscilacoes=0,
        )

    rates = [float(r.rate.replace(",", ".")) for r in records]
    taxa_inicial = rates[0]
    taxa_final = rates[-1]
    taxa_maxima = max(rates)
    taxa_minima = min(rates)

    x = np.arange(len(rates))
    slope = None
    convexidade = None
    if len(rates) >= 2:
        coef_linear = np.polyfit(x, rates, 1)
        slope = float(coef_linear[0])
    if len(rates) >= 3:
        coef_quad = np.polyfit(x, rates, 2)
        convexidade = float(coef_quad[0])

    volatilidade = None
    if len(rates) >= 2:
        diffs = np.diff(rates)
        volatilidade = float(np.std(diffs, ddof=0))

    oscilacoes = 0
    if len(rates) >= 3:
        for i in range(1, len(rates) - 1):
            if (rates[i] - rates[i - 1]) * (rates[i + 1] - rates[i]) < 0:
                oscilacoes += 1

    return DetailedMetrics(
        taxa_inicial=taxa_inicial,
        taxa_final=taxa_final,
        taxa_maxima=taxa_maxima,
        taxa_minima=taxa_minima,
        slope=slope,
        convexidade=convexidade,
        volatilidade=volatilidade,
        oscilacoes=oscilacoes,
    )
