from dataclasses import dataclass, field

from b3_selic_pre.application.analyze._classifier import Fact
from b3_selic_pre.application.analyze._registry import FactType
from b3_selic_pre.application.analyze._templates import resolve_template

ENGINE_VERSION = "2.0.0"
RULESET_VERSION = "1.1.0"


@dataclass
class AnalysisResult:
    engine_version: str
    ruleset_version: str
    generated_at: str
    facts: list[Fact]
    score: int
    intensity_label: str
    confidence: dict[str, float]


@dataclass
class AnalysisReport:
    statements: list[str] = field(default_factory=list)
    score: int = 0
    score_label: str = ""


def build_report(
    statements: list[str],
    score: int,
    score_label: str,
) -> AnalysisReport:
    return AnalysisReport(
        statements=statements,
        score=score,
        score_label=score_label,
    )


_BLOCOS = [
    ("CLASSE PRIMARIA", FactType.CLASSIFICATION),
    ("ESTRUTURA", FactType.STRUCTURE),
    ("QUALIDADE", FactType.QUALITY),
    ("INTENSIDADE", FactType.INTENSITY),
    ("RESUMO", None),
]


def _facts_by_type(facts: list[Fact]) -> dict[FactType, list[Fact]]:
    grouped: dict[FactType, list[Fact]] = {
        FactType.CLASSIFICATION: [],
        FactType.STRUCTURE: [],
        FactType.QUALITY: [],
    }
    for fact in facts:
        if fact.fact_type in grouped:
            grouped[fact.fact_type].append(fact)
    return grouped


def build_statements_from_facts(
    facts: list[Fact],
    score: int,
    intensity_label: str,
    confidence: dict[str, float],
    locale: str = "pt",
) -> list[str]:
    statements: list[str] = []
    grouped = _facts_by_type(facts)

    for nome_bloco, fact_type in _BLOCOS:
        if fact_type is None:
            continue
        items = grouped.get(fact_type, [])
        if not items:
            continue
        statements.append(nome_bloco)
        statements.append("─" * len(nome_bloco))
        for fact in items:
            text = resolve_template(fact.template_id, locale)
            if not text:
                continue
            if fact.template_id == "fallback_primary":
                text = text.replace("{classe}", fact.id)
                text = text.replace("{pct}", f"{fact.confidence:.0%}")
            derived_str = ", ".join(fact.derived_from_features) if fact.derived_from_features else "—"
            conf_pct = f"{fact.confidence:.0%}"
            statements.append(f"  • {text}")
            statements.append(f"    Confianca: {conf_pct} | Features: [{derived_str}]")
        statements.append("")

    statements.append("INTENSIDADE")
    statements.append("─" * len("INTENSIDADE"))
    conf_parts = []
    for k, v in confidence.items():
        conf_parts.append(f"Nivel {k}: {v:.0%}")
    statements.append(f"  • Score: {score}")
    statements.append(f"  • {intensity_label}")
    if conf_parts:
        statements.append(f"  • Confianca: {' | '.join(conf_parts)}")
    statements.append("")

    return statements


def format_report(report: AnalysisReport) -> str:
    if not report.statements:
        return "Sem dados para analise."
    return "\n".join(report.statements).strip()


# Backward compatibility
def build_statements_from_inference(result: AnalysisResult) -> list[str]:
    return build_statements_from_facts(
        result.facts,
        result.score,
        result.intensity_label,
        result.confidence,
    )
