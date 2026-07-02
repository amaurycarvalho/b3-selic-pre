from __future__ import annotations

from dataclasses import dataclass, field

from b3_selic_pre.application.analyze._config import CurvaJurosConfig
from b3_selic_pre.domain.models import RateRecord


@dataclass
class AnalysisReport:
    statements: list[str] = field(default_factory=list)
    score: int = 0
    score_label: str = ""


@dataclass
class Indicadores:
    taxa_curta: float
    taxa_longa: float
    inclinacao_bps: float
    juro_real: float


def extrair_indicadores(
    records: list[RateRecord], config: CurvaJurosConfig
) -> Indicadores:
    rates = [float(r.rate.replace(",", ".")) for r in records]
    taxa_curta = rates[0]
    taxa_longa = rates[-1]
    inclinacao_bps = (taxa_longa - taxa_curta) * 100
    juro_real = taxa_curta - config.expected_inflation
    return Indicadores(
        taxa_curta=taxa_curta,
        taxa_longa=taxa_longa,
        inclinacao_bps=inclinacao_bps,
        juro_real=juro_real,
    )


def classificar_nominal(taxa_curta: float, config: CurvaJurosConfig) -> str:
    f = config.faixas_nominais
    if taxa_curta < f[0]:
        return "Muito Baixos"
    if taxa_curta < f[1]:
        return "Baixos"
    if taxa_curta < f[2]:
        return "Moderados"
    if taxa_curta < f[3]:
        return "Altos"
    return "Muito Altos"


def classificar_restricao(juro_real: float, config: CurvaJurosConfig) -> str:
    f = config.faixas_juro_real
    if juro_real < f[0]:
        return "Expansionista"
    if juro_real < f[1]:
        return "Neutra"
    if juro_real < f[2]:
        return "Restritiva"
    return "Muito Restritiva"


def classificar_premio(inclinacao_bps: float, config: CurvaJurosConfig) -> str:
    if inclinacao_bps < 20:
        return "Muito Baixo"
    if inclinacao_bps < 50:
        return "Baixo"
    if inclinacao_bps < 90:
        return "Normal"
    if inclinacao_bps < 150:
        return "Elevado"
    return "Muito Elevado"


def classificar_inclinacao(inclinacao_bps: float) -> str:
    if inclinacao_bps < 10:
        return "Quase Plana"
    if inclinacao_bps < 30:
        return "Muito Plana"
    if inclinacao_bps < 60:
        return "Plana"
    if inclinacao_bps < 100:
        return "Moderadamente Inclinada"
    return "Muito Inclinada"


def calcular_estabilidade(
    historical_data: dict[str, list[RateRecord]] | None,
    records: list[RateRecord],
    config: CurvaJurosConfig,
) -> dict | None:
    if not historical_data or len(historical_data) < config.stability_window:
        return _estabilidade_fallback(config)

    sorted_dates = sorted(historical_data.keys())
    window_dates = sorted_dates[-config.stability_window:]

    slopes = []
    for date in window_dates:
        date_records = historical_data[date]
        if not date_records:
            continue
        rates = [float(r.rate.replace(",", ".")) for r in date_records]
        if len(rates) < 2:
            continue
        slope = (rates[-1] - rates[0]) * 100
        slopes.append(slope)

    if len(slopes) < 2:
        return _estabilidade_fallback(config)

    mean_slope = sum(slopes) / len(slopes)
    deviations = [abs(s - mean_slope) for s in slopes]
    mean_dev = sum(deviations) / len(deviations)

    return _classificar_estabilidade(mean_dev, config, estimado=False)


def _estabilidade_fallback(config: CurvaJurosConfig) -> dict | None:
    if config.stability_fallback == "unavailable":
        return None
    if config.stability_fallback == "auto":
        mean_dev = config.default_mean_deviation_bps
    else:
        mean_dev = config.default_mean_deviation_bps
    return _classificar_estabilidade(mean_dev, config, estimado=True)


def _classificar_estabilidade(
    deviation_bps: float, config: CurvaJurosConfig, estimado: bool = False
) -> dict:
    f = config.faixas_estabilidade
    if deviation_bps < f[0]:
        nivel = "Muito Alta"
    elif deviation_bps < f[1]:
        nivel = "Alta"
    elif deviation_bps < f[2]:
        nivel = "Média"
    elif deviation_bps < f[3]:
        nivel = "Baixa"
    else:
        nivel = "Muito Baixa"
    return {"deviation_bps": round(deviation_bps, 2), "nivel": nivel, "estimado": estimado}


def _calc_slope_from_records(records: list[RateRecord]) -> float | None:
    if not records or len(records) < 2:
        return None
    rates = [float(r.rate.replace(",", ".")) for r in records]
    return (rates[-1] - rates[0]) * 100


def calcular_steepening(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None,
    config: CurvaJurosConfig,
) -> dict | None:
    current_slope = _calc_slope_from_records(records)
    if current_slope is None:
        return None

    previous_slope = None
    if historical_data and len(historical_data) >= 2:
        sorted_dates = sorted(historical_data.keys())
        prev_date = sorted_dates[-2]
        prev_records = historical_data[prev_date]
        previous_slope = _calc_slope_from_records(prev_records)

    if previous_slope is None:
        return _steepening_fallback(current_slope, config)

    delta = current_slope - previous_slope
    return _classificar_steepening(delta, config)


def _steepening_fallback(current_slope: float, config: CurvaJurosConfig) -> dict | None:
    if config.steepening_fallback == "unavailable":
        return None
    if config.steepening_fallback == "auto":
        delta = abs(current_slope) / 5
    else:
        delta = config.estimated_delta_slope_bps
    return _classificar_steepening(delta, config)


def _classificar_steepening(delta_bps: float, config: CurvaJurosConfig) -> dict:
    s = config.steepening_small_bps
    m = config.steepening_medium_bps
    l_val = config.steepening_large_bps
    abs_delta = abs(delta_bps)

    if abs_delta < s:
        magnitude = "Leve"
    elif abs_delta < m:
        magnitude = "Moderado"
    elif abs_delta < l_val:
        magnitude = "Forte"
    else:
        magnitude = "Muito Forte"

    if delta_bps > config.steepening_threshold_bps:
        direcao = "Steepening"
    elif delta_bps < -config.steepening_threshold_bps:
        direcao = "Flattening"
    else:
        return {"direcao": "Estavel", "delta_bps": 0.0, "magnitude": "Nenhuma"}

    return {
        "direcao": direcao,
        "delta_bps": round(delta_bps, 2),
        "magnitude": magnitude,
    }
