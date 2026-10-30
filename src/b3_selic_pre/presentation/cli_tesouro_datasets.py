"""Handlers headless de resgates e estoque do Tesouro Direto."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from b3_selic_pre.application.cli_services import ExportArtifact
from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import (
    PeriodoInvalidoError,
    TesouroDataError,
    agregar_estoque,
    agregar_resgates,
    build_estoque_agregados_payload,
    build_estoque_payload,
    build_resgates_agregados_payload,
    build_resgates_payload,
    filtrar_estoque_por_periodo,
    filtrar_estoque_por_titulo,
    filtrar_resgates_por_periodo,
    filtrar_resgates_por_tipo,
    filtrar_resgates_por_titulo,
    format_estoque_agregados_csv,
    format_estoque_csv,
    format_resgates_agregados_csv,
    format_resgates_csv,
    meses_presentes,
    ordenar_estoque,
    ordenar_resgates,
    resolver_periodo_estoque,
    resolver_periodo_resgates,
    validar_meses,
    validar_periodo,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
)
from b3_selic_pre.presentation.cli_data import print_artifact, write_artifacts

logger = logging.getLogger(__name__)


def _artifact(
    name: str, content: str, *, agregado: bool, json_output: bool
) -> ExportArtifact:
    if agregado:
        name += "-agregado"
    return ExportArtifact(name + (".json" if json_output else ".csv"), content)


def _resgates_artifact(
    args: argparse.Namespace,
    records: list[ResgateTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
) -> ExportArtifact:
    if args.agregar:
        aggregates = agregar_resgates(records)
        if args.json:
            payload = build_resgates_agregados_payload(
                aggregates, metadata, periodo, len(records)
            )
            return _artifact(
                "tesouro-resgates",
                json.dumps(payload, ensure_ascii=False),
                agregado=True,
                json_output=True,
            )
        return _artifact(
            "tesouro-resgates",
            format_resgates_agregados_csv(aggregates),
            agregado=True,
            json_output=False,
        )
    if args.json:
        payload = build_resgates_payload(records, metadata, periodo)
        return _artifact(
            "tesouro-resgates",
            json.dumps(payload, ensure_ascii=False),
            agregado=False,
            json_output=True,
        )
    return _artifact(
        "tesouro-resgates",
        format_resgates_csv(records),
        agregado=False,
        json_output=False,
    )


def _estoque_artifact(
    args: argparse.Namespace,
    records: list[EstoqueTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
) -> ExportArtifact:
    if args.agregar:
        aggregates = agregar_estoque(records)
        if args.json:
            payload = build_estoque_agregados_payload(
                aggregates, metadata, periodo, len(records)
            )
            return _artifact(
                "tesouro-estoque",
                json.dumps(payload, ensure_ascii=False),
                agregado=True,
                json_output=True,
            )
        return _artifact(
            "tesouro-estoque",
            format_estoque_agregados_csv(aggregates),
            agregado=True,
            json_output=False,
        )
    if args.json:
        payload = build_estoque_payload(records, metadata, periodo)
        return _artifact(
            "tesouro-estoque",
            json.dumps(payload, ensure_ascii=False),
            agregado=False,
            json_output=True,
        )
    return _artifact(
        "tesouro-estoque",
        format_estoque_csv(records),
        agregado=False,
        json_output=False,
    )


def _finish(
    args: argparse.Namespace, artifact: ExportArtifact
) -> int:
    if args.saida is None:
        print_artifact(artifact)
        return 0
    try:
        return write_artifacts([artifact], args.saida)
    except OSError as exc:
        logger.warning("Falha ao gravar a saída do Tesouro: %s", exc)
        print(f"Falha ao gravar a saída: {exc}", file=sys.stderr)
        return 1


def tesouro_resgates(args: argparse.Namespace, client: object) -> int:
    """Consulta, filtra, agrega e exporta os resgates do Tesouro."""
    try:
        validar_periodo(args.inicio, args.fim)
    except PeriodoInvalidoError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        records, metadata, _origem = client.fetch_resgates(
            force=args.no_cache
        )
    except (CommunicationError, TesouroDataError) as exc:
        logger.warning("Erro ao consultar o Tesouro: %s", exc)
        print(f"Erro ao consultar o Tesouro: {exc}", file=sys.stderr)
        return 1
    filtered = filtrar_resgates_por_tipo(records, args.tipo)
    filtered = filtrar_resgates_por_titulo(filtered, args.titulo)
    inicio, fim = resolver_periodo_resgates(records, args.inicio, args.fim)
    ordered = ordenar_resgates(
        filtrar_resgates_por_periodo(filtered, inicio, fim)
    )
    artifact = _resgates_artifact(
        args, ordered, metadata, {"inicio": inicio, "fim": fim}
    )
    return _finish(args, artifact)


def tesouro_estoque(args: argparse.Namespace, client: object) -> int:
    """Consulta, filtra, agrega e exporta o estoque do Tesouro."""
    try:
        validar_meses(args.inicio, args.fim)
        if args.mes is not None:
            validar_meses(args.mes, None)
    except PeriodoInvalidoError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        records, metadata, _origem = client.fetch_estoque(
            force=args.no_cache
        )
    except (CommunicationError, TesouroDataError) as exc:
        logger.warning("Erro ao consultar o Tesouro: %s", exc)
        print(f"Erro ao consultar o Tesouro: {exc}", file=sys.stderr)
        return 1
    filtered = filtrar_estoque_por_titulo(records, args.titulo)
    inicio, fim = resolver_periodo_estoque(
        records, args.inicio, args.fim, args.mes
    )
    filtered = ordenar_estoque(
        filtrar_estoque_por_periodo(filtered, inicio, fim)
    )
    if args.agregar and len(meses_presentes(filtered)) > 1:
        print(
            "A agregação de estoque exige um único mês.",
            file=sys.stderr,
        )
        return 2
    artifact = _estoque_artifact(
        args,
        filtered,
        metadata,
        {"inicio": inicio, "fim": fim, "mes": args.mes},
    )
    return _finish(args, artifact)
