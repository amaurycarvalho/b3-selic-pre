"""Serviços headless usados pelos comandos de atualização e exportação da CLI."""

from __future__ import annotations

from dataclasses import dataclass

from b3_selic_pre.application.analyze import (
    CurvaJurosConfig,
    analyze,
    analyze_evolution,
    montar_evolucao_resumo,
)
from b3_selic_pre.application.formatting import (
    format_detailed_evolution_csv,
    format_evolution_csv,
)
from b3_selic_pre.application.use_cases import (
    to_curve_longa,
    to_curve_longa_historical,
)
from b3_selic_pre.domain.models import RateRecord


@dataclass(frozen=True)
class ExportArtifact:
    """Conteúdo nomeado que a apresentação pode imprimir ou gravar."""

    name: str
    content: str


@dataclass(frozen=True)
class PrecomputedAnalysis:
    """Texto de análise já calculado para uma representação de curva."""

    curva: str
    texto: str


def build_analysis_text(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None = None,
    config: CurvaJurosConfig | None = None,
    curva: str = "curta",
    precomputed: PrecomputedAnalysis | None = None,
) -> str:
    """Monta o texto determinístico da análise da curva."""
    if precomputed is not None and precomputed.curva == curva:
        return precomputed.texto
    if not records:
        return ""
    if curva == "longa":
        records = to_curve_longa(records)
        historical_data = to_curve_longa_historical(historical_data)
    report = analyze(
        records=records,
        historical_data=historical_data,
        config=config,
    )
    return "\n\n".join(report.statements)


def build_evolution_text(
    current: list[RateRecord],
    previous: list[RateRecord],
    config: CurvaJurosConfig | None = None,
    curva: str = "curta",
) -> str:
    """Monta o texto da evolução entre a curva atual e a anterior."""
    if not current or not previous:
        return ""
    if curva == "longa":
        current = to_curve_longa(current)
        previous = to_curve_longa(previous)
    report = analyze_evolution(current, previous, config=config)
    if report is None:
        return ""
    evolution_config = (config or CurvaJurosConfig()).evolucao
    return "\n\n".join(montar_evolucao_resumo(report, evolution_config))


def _has_records(
    historical_data: dict[str, list[RateRecord]] | None,
) -> bool:
    return any(bool(records) for records in (historical_data or {}).values())


def _previous_records(
    historical_data: dict[str, list[RateRecord]] | None,
) -> list[RateRecord] | None:
    if not historical_data:
        return None
    dates = sorted(date for date, records in historical_data.items() if records)
    if len(dates) < 2:
        return None
    return historical_data[dates[-2]]


def _build_combined_analysis_text(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None,
    config: CurvaJurosConfig | None,
    analise_curva: str = "curta",
    precomputed: PrecomputedAnalysis | None = None,
) -> str:
    parts: list[str] = []
    analysis = build_analysis_text(
        records,
        historical_data,
        config,
        curva=analise_curva,
        precomputed=precomputed,
    )
    analysis_title = (
        "Análise da Curva Longa (taxa média por ano)"
        if analise_curva == "longa"
        else "Análise da Curva"
    )
    if analysis:
        parts.append(f"{analysis_title}\n\n{analysis}")
    previous = _previous_records(historical_data)
    if previous is not None:
        evolution = build_evolution_text(
            records, previous, config, curva=analise_curva
        )
        evolution_title = (
            "Evolução da Curva Longa (taxa média por ano)"
            if analise_curva == "longa"
            else "Evolução da Curva"
        )
        if evolution:
            parts.append(f"{evolution_title}\n\n{evolution}")
    return "\n\n".join(parts)


def build_export_artifacts(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None = None,
    curva: str | None = None,
    include_analise: bool = False,
    log_text: str | None = None,
    config: CurvaJurosConfig | None = None,
    analise_curva: str = "curta",
    precomputed: PrecomputedAnalysis | None = None,
) -> list[ExportArtifact]:
    """Seleciona os artefatos de exportação a partir do conteúdo solicitado."""
    artifacts: list[ExportArtifact] = []
    if curva in ("curta", "ambas") and _has_records(historical_data):
        artifacts.append(
            ExportArtifact(
                "curva-curta.csv",
                format_detailed_evolution_csv(historical_data or {}),
            )
        )
    if curva in ("longa", "ambas") and _has_records(historical_data):
        artifacts.append(
            ExportArtifact(
                "curva-longa.csv",
                format_evolution_csv(historical_data or {}),
            )
        )
    if include_analise:
        analysis = _build_combined_analysis_text(
            records,
            historical_data,
            config,
            analise_curva=analise_curva,
            precomputed=precomputed,
        )
        if analysis:
            artifacts.append(ExportArtifact("analise.txt", analysis))
    if log_text is not None:
        artifacts.append(ExportArtifact("b3-selic-pre.log", log_text))
    return artifacts
