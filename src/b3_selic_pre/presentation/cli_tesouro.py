"""Handler headless do subcomando de vendas do Tesouro Direto."""

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
    agregar_por_titulo,
    build_agregados_payload,
    build_vendas_payload,
    filtrar_por_periodo,
    filtrar_por_titulo,
    format_agregados_csv,
    format_vendas_csv,
    ordenar_vendas,
    resolver_periodo,
    validar_periodo,
)
from b3_selic_pre.domain.models import VendaTesouroDireto
from b3_selic_pre.presentation.cli_data import print_artifact, write_artifacts

logger = logging.getLogger(__name__)


def _artifact(
    content: str, *, agregado: bool, json_output: bool
) -> ExportArtifact:
    name = "tesouro-vendas"
    if agregado:
        name += "-agregado"
    return ExportArtifact(name + (".json" if json_output else ".csv"), content)


def _aggregated_artifact(
    args: argparse.Namespace,
    sales: list[VendaTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
) -> ExportArtifact:
    aggregates = agregar_por_titulo(sales)
    if args.json:
        payload = build_agregados_payload(
            aggregates, metadata, periodo, len(sales)
        )
        return _artifact(
            json.dumps(payload, ensure_ascii=False),
            agregado=True,
            json_output=True,
        )
    return _artifact(
        format_agregados_csv(aggregates), agregado=True, json_output=False
    )


def _output_artifact(
    args: argparse.Namespace,
    sales: list[VendaTesouroDireto],
    metadata: dict[str, object],
    periodo: dict[str, str | None],
) -> ExportArtifact:
    if args.agregar:
        return _aggregated_artifact(args, sales, metadata, periodo)
    if args.json:
        payload = build_vendas_payload(sales, metadata, periodo)
        return _artifact(
            json.dumps(payload, ensure_ascii=False),
            agregado=False,
            json_output=True,
        )
    return _artifact(
        format_vendas_csv(sales), agregado=False, json_output=False
    )


def tesouro(args: argparse.Namespace, client: object) -> int:
    """Consulta, filtra, agrega e exporta as vendas do Tesouro Direto."""
    try:
        validar_periodo(args.inicio, args.fim)
    except PeriodoInvalidoError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        sales, metadata, _origem = client.fetch_vendas(force=args.no_cache)
    except (CommunicationError, TesouroDataError) as exc:
        logger.warning("Erro ao consultar o Tesouro: %s", exc)
        print(f"Erro ao consultar o Tesouro: {exc}", file=sys.stderr)
        return 1
    filtered = filtrar_por_titulo(sales, args.titulo)
    inicio, fim = resolver_periodo(sales, args.inicio, args.fim)
    filtered = ordenar_vendas(filtrar_por_periodo(filtered, inicio, fim))
    artifact = _output_artifact(
        args,
        filtered,
        metadata,
        {"inicio": inicio, "fim": fim},
    )
    if args.saida is None:
        print_artifact(artifact)
        return 0
    try:
        return write_artifacts([artifact], args.saida)
    except OSError as exc:
        logger.warning("Falha ao gravar a saída do Tesouro: %s", exc)
        print(f"Falha ao gravar a saída: {exc}", file=sys.stderr)
        return 1
