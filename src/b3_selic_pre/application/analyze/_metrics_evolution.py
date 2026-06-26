from dataclasses import dataclass

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.application.use_cases import average_rate_by_year


@dataclass
class EnvelopeMetrics:
    spread_medio: float
    spread_tendencia: str


@dataclass
class EvolutionMetrics:
    deltas: list[float]
    tendencia: str
    difusao: str
    rotacao: str
    intensidade: float


def extract_envelope_metrics(
    records: list[RateRecord],
    thresholds: object,
) -> EnvelopeMetrics:
    from b3_selic_pre.application.use_cases import consolidate_by_year

    if not records:
        return EnvelopeMetrics(spread_medio=0.0, spread_tendencia="estável")

    consolidated = consolidate_by_year(records)
    if not consolidated:
        return EnvelopeMetrics(spread_medio=0.0, spread_tendencia="estável")

    spreads = [g["max_rate"] - g["min_rate"] for g in consolidated]
    spread_medio = sum(spreads) / len(spreads)

    if len(spreads) >= 3:
        first_half = spreads[: len(spreads) // 2]
        second_half = spreads[len(spreads) // 2 :]
        media_primeira = sum(first_half) / len(first_half)
        media_segunda = sum(second_half) / len(second_half)
        if media_segunda > media_primeira * 1.1:
            spread_tendencia = "crescente"
        elif media_segunda < media_primeira * 0.9:
            spread_tendencia = "decrescente"
        else:
            spread_tendencia = "estável"
    else:
        spread_tendencia = "estável"

    return EnvelopeMetrics(spread_medio=spread_medio, spread_tendencia=spread_tendencia)


def _compute_yearly_averages(
    historical_data: dict[str, list[RateRecord]],
) -> dict[str, dict[int, float]]:
    return {
        date: average_rate_by_year(records)
        for date, records in sorted(historical_data.items())
    }


def extract_evolution_metrics(
    historical_data: dict[str, list[RateRecord]],
) -> EvolutionMetrics:
    if not historical_data or len(historical_data) < 2:
        return EvolutionMetrics(
            deltas=[],
            tendencia="instabilidade",
            difusao="sem dados",
            rotacao="sem movimento",
            intensidade=0.0,
        )

    yearly_avg = _compute_yearly_averages(historical_data)
    dates = sorted(yearly_avg.keys())
    all_years = sorted(
        {y for d in dates for y in yearly_avg[d]}
    )

    deltas = []
    for year in all_years:
        rates_por_data = [yearly_avg[d].get(year) for d in dates]
        rates_por_data = [r for r in rates_por_data if r is not None]
        if len(rates_por_data) >= 2:
            delta = rates_por_data[-1] - rates_por_data[0]
            deltas.append(delta)

    if not deltas:
        return EvolutionMetrics(
            deltas=[],
            tendencia="instabilidade",
            difusao="sem dados",
            rotacao="sem movimento",
            intensidade=0.0,
        )

    positivos = sum(1 for d in deltas if d > 0)
    negativos = sum(1 for d in deltas if d < 0)
    total = len(deltas)

    if positivos == total:
        tendencia = "alta_continua"
    elif negativos == total:
        tendencia = "queda_continua"
    else:
        tendencia = "instabilidade"

    difusao_ratio = max(positivos, negativos) / total if total > 0 else 0
    if difusao_ratio >= 0.80:
        difusao = "disseminado"
    elif positivos > negativos:
        difusao = "concentrado_longo"
    else:
        difusao = "concentrado_curto"

    anos_curtos = [y for y in all_years if y <= 5]
    anos_longos = [y for y in all_years if y > 5]
    delta_curto = 0.0
    delta_longo = 0.0
    if anos_curtos and dates:
        taxas_curta = [yearly_avg[dates[-1]].get(y) for y in anos_curtos]
        taxas_curta_inicial = [yearly_avg[dates[0]].get(y) for y in anos_curtos]
        taxas_curta = [r for r in taxas_curta if r is not None]
        taxas_curta_inicial = [r for r in taxas_curta_inicial if r is not None]
        if taxas_curta and taxas_curta_inicial:
            delta_curto = sum(taxas_curta) / len(taxas_curta) - sum(taxas_curta_inicial) / len(taxas_curta_inicial)
    if anos_longos and dates:
        taxas_longa = [yearly_avg[dates[-1]].get(y) for y in anos_longos]
        taxas_longa_inicial = [yearly_avg[dates[0]].get(y) for y in anos_longos]
        taxas_longa = [r for r in taxas_longa if r is not None]
        taxas_longa_inicial = [r for r in taxas_longa_inicial if r is not None]
        if taxas_longa and taxas_longa_inicial:
            delta_longo = sum(taxas_longa) / len(taxas_longa) - sum(taxas_longa_inicial) / len(taxas_longa_inicial)

    if delta_curto > 0 and delta_longo > 0:
        if delta_longo > delta_curto:
            rotacao = "bear_steepening"
        elif delta_curto > delta_longo:
            rotacao = "bear_flattening"
        else:
            rotacao = "movimento_uniforme"
    elif delta_curto < 0 and delta_longo < 0:
        if abs(delta_curto) > abs(delta_longo):
            rotacao = "bull_steepening"
        elif abs(delta_longo) > abs(delta_curto):
            rotacao = "bull_flattening"
        else:
            rotacao = "movimento_uniforme"
    elif delta_curto >= 0 and delta_longo <= 0:
        rotacao = "bear_flattening"
    elif delta_curto <= 0 and delta_longo >= 0:
        rotacao = "bear_steepening"
    else:
        rotacao = "movimento_uniforme"

    intensidade = sum(abs(d) for d in deltas) / len(deltas) if deltas else 0.0

    return EvolutionMetrics(
        deltas=deltas,
        tendencia=tendencia,
        difusao=difusao,
        rotacao=rotacao,
        intensidade=intensidade,
    )
