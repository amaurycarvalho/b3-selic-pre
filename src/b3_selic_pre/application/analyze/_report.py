from dataclasses import dataclass, field


@dataclass
class AnalysisReport:
    statements: list[str] = field(default_factory=list)
    score: int = 0
    score_label: str = ""


_SECOES = [
    "Formato da Curva",
    "Dispersão e Consenso",
    "Evolução Recente",
    "Qualidade do Movimento",
    "Conclusão",
]


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


def format_report(report: AnalysisReport) -> str:
    if not report.statements:
        return "Sem dados para análise."

    linhas: list[str] = []
    secoes_agrupadas: dict[str, list[str]] = {s: [] for s in _SECOES}

    current_section = _SECOES[0]
    for frase in report.statements:
        if frase in _SECOES:
            current_section = frase
        elif frase.strip():
            secoes_agrupadas[current_section].append(frase)

    for secao in _SECOES:
        frases = secoes_agrupadas[secao]
        if frases:
            linhas.append(f"{secao}")
            linhas.append("─" * len(secao))
            for f in frases:
                linhas.append(f"  • {f}")
            linhas.append("")

    if report.score_label:
        score_display = f"Score: {report.score} — {report.score_label}"
        linhas.append(score_display)

    return "\n".join(linhas).strip()
