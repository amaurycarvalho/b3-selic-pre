from datetime import datetime, timezone

from b3_selic_pre.application.analyze._config import InferenceConfig
from b3_selic_pre.application.analyze._metrics import (
    extract_detailed_metrics,
)
from b3_selic_pre.application.analyze._features import compute_features
from b3_selic_pre.application.analyze._classifier import classify, Fact
from b3_selic_pre.application.analyze._scoring import (
    compute_score,
    compute_confidence_per_level,
    classify_intensity,
)
from b3_selic_pre.application.analyze._report import (
    AnalysisReport,
    AnalysisResult,
    build_report,
    build_statements_from_facts,
    format_report,
    ENGINE_VERSION,
    RULESET_VERSION,
)
from b3_selic_pre.domain.models import RateRecord


def _rates_from_records(records: list[RateRecord]) -> list[float]:
    return [float(r.rate.replace(",", ".")) for r in records]


def _direction_from_facts(facts: list[Fact]) -> str:
    asc_facts = {"ASCENDENTE", "VALE"}
    desc_facts = {"DESCENDENTE", "PICO"}
    for fact in facts:
        if fact.id in asc_facts:
            return "asc"
        if fact.id in desc_facts:
            return "desc"
    return "plana"


def analyze(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None = None,
    view_mode: str = "raw",
    evolution_active: bool = False,
    threshold_overrides: dict | None = None,
    config: InferenceConfig | None = None,
    locale: str = "pt",
) -> AnalysisReport:
    if not records:
        return AnalysisReport()

    if evolution_active and historical_data:
        return AnalysisReport(
            statements=["Analise de evolucao ainda nao implementada."],
            score=0,
            score_label="",
        )

    if view_mode == "consolidated":
        return AnalysisReport(
            statements=["Analise consolidada ainda nao implementada."],
            score=0,
            score_label="",
        )

    if config is None:
        config = InferenceConfig()

    if threshold_overrides:
        for key, value in threshold_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

    metrics = extract_detailed_metrics(records)
    rates = _rates_from_records(records)

    features = compute_features(metrics, rates, config)

    facts, _evaluations = classify(features, config)

    score = compute_score(facts)

    direction = _direction_from_facts(facts)
    intensity_label = classify_intensity(score, direction)

    confidence = compute_confidence_per_level(facts)

    statements = build_statements_from_facts(
        facts, score, intensity_label, confidence, locale
    )

    return build_report(statements, score, intensity_label)


__all__ = [
    "AnalysisReport",
    "AnalysisResult",
    "Fact",
    "InferenceConfig",
    "analyze",
]
