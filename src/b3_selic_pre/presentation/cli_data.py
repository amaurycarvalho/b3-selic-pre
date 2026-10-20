"""Resolução de dados, configuração e escrita de artefatos da CLI."""

from __future__ import annotations

import sys
from pathlib import Path

from b3_selic_pre.application.analyze import CurvaJurosConfig
from b3_selic_pre.application.cli_services import ExportArtifact
from b3_selic_pre.application.use_cases import (
    default_reference_date,
    nearest_business_day,
    validate_query_date,
)
from b3_selic_pre.presentation.settings import Settings


def resolve_data(value: str | None) -> str:
    """Resolve, valida e ajusta a data de referência informada."""
    raw = (value or default_reference_date()).strip()
    return nearest_business_day(validate_query_date(raw))


def config_from_settings(settings: Settings) -> CurvaJurosConfig:
    """Monta a configuração da análise a partir das preferências persistidas."""
    return CurvaJurosConfig.from_mapping(
        settings.get("curva_juros", {}),
        settings.get("curva_evolucao", {}),
    )


def print_artifact(artifact: ExportArtifact) -> None:
    """Imprime um artefato no stdout preservando a quebra de linha final."""
    print(
        artifact.content,
        end="" if artifact.content.endswith("\n") else "\n",
    )


def _write_to_stdout(artifacts: list[ExportArtifact]) -> int:
    if len(artifacts) != 1:
        print(
            "Informe --saida como diretório para múltiplos artefatos.",
            file=sys.stderr,
        )
        return 2
    print_artifact(artifacts[0])
    return 0


def _write_many(artifacts: list[ExportArtifact], target: Path) -> int:
    if target.exists() and not target.is_dir():
        print(
            "--saida deve ser um diretório para múltiplos artefatos.",
            file=sys.stderr,
        )
        return 2
    target.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        (target / artifact.name).write_text(
            artifact.content, encoding="utf-8"
        )
    return 0


def _write_one(artifact: ExportArtifact, target: Path) -> int:
    if target.exists() and target.is_dir():
        target = target / artifact.name
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(artifact.content, encoding="utf-8")
    return 0


def write_artifacts(
    artifacts: list[ExportArtifact], saida: str | None
) -> int:
    """Grava os artefatos em stdout, arquivo ou diretório conforme ``saida``."""
    if saida is None:
        return _write_to_stdout(artifacts)
    target = Path(saida)
    if len(artifacts) > 1:
        return _write_many(artifacts, target)
    return _write_one(artifacts[0], target)
