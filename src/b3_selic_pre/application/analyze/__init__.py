from b3_selic_pre.application.analyze._thresholds import AnalysisThresholds
from b3_selic_pre.application.analyze._metrics import (
    DetailedMetrics,
    extract_detailed_metrics,
)
from b3_selic_pre.application.analyze._metrics_evolution import (
    EnvelopeMetrics,
    EvolutionMetrics,
    extract_envelope_metrics,
    extract_evolution_metrics,
)
from b3_selic_pre.application.analyze._rules import (
    regra_convexidade,
    regra_difusao,
    regra_forma_curva,
    regra_inclinacao,
    regra_intensidade,
    regra_oscilacoes,
    regra_rotacao,
    regra_score_agregado,
    regra_spread_envelope,
    regra_tendencia_envelope,
    regra_tendencia_evolucao,
    regra_volatilidade,
)
from b3_selic_pre.application.analyze._report import (
    AnalysisReport,
    build_report,
    format_report,
)
from b3_selic_pre.domain.models import RateRecord


def analyze(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None = None,
    view_mode: str = "raw",
    evolution_active: bool = False,
    thresholds: AnalysisThresholds | None = None,
) -> AnalysisReport:
    if thresholds is None:
        thresholds = AnalysisThresholds()

    if not records:
        return AnalysisReport()

    statements: list[str] = []
    score = 0

    if evolution_active and historical_data:
        evolution = extract_evolution_metrics(historical_data)

        r = regra_tendencia_evolucao(evolution, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        r = regra_difusao(evolution, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        r = regra_rotacao(evolution, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        r = regra_intensidade(evolution, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        if view_mode == "consolidated":
            envelope = extract_envelope_metrics(records, thresholds)
            r = regra_spread_envelope(envelope, thresholds)
            if r.text:
                statements.append(r.text)
                score += r.weight
            r = regra_tendencia_envelope(envelope, thresholds)
            if r.text:
                statements.append(r.text)
                score += r.weight
    elif view_mode == "consolidated":
        envelope = extract_envelope_metrics(records, thresholds)
        r = regra_spread_envelope(envelope, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight
        r = regra_tendencia_envelope(envelope, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight
    else:
        detailed = extract_detailed_metrics(records, thresholds)

        r = regra_forma_curva(detailed, thresholds)
        if r.text:
            statements.insert(0, r.text)
            score += r.weight

        r = regra_inclinacao(detailed, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        r = regra_convexidade(detailed, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        r = regra_volatilidade(detailed, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

        r = regra_oscilacoes(detailed, thresholds)
        if r.text:
            statements.append(r.text)
            score += r.weight

    r = regra_score_agregado(score, thresholds)
    if r.text:
        statements.append(r.text)

    if score >= thresholds.score_expressivo:
        score_label = "Mudança expressiva"
    elif score >= thresholds.score_relevante:
        score_label = "Mudança relevante"
    elif score >= thresholds.score_moderado:
        score_label = "Mudança moderada"
    else:
        score_label = "Mercado estável"

    report = build_report(statements, score, score_label)
    return report


__all__ = [
    "AnalysisReport",
    "AnalysisThresholds",
    "analyze",
]
