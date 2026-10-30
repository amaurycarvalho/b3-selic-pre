"""Formatadores CSV/JSON e artefatos de exportação de reservas."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence

from b3_selic_pre.application.cli_services import ExportArtifact
from b3_selic_pre.application.market.export import (
    DELIMITER,
    format_market_json,
)
from b3_selic_pre.application.reserves.series import sort_points
from b3_selic_pre.domain.market import MarketQuote

SERIES_HEADER = ("DATA", "VALOR", "UNIDADE", "ORIGEM", "METODO")
SERIES_FILENAME = "reservas-serie.csv"
JSON_FILENAME = "reservas.json"


def _num(value: float | None) -> str:
    if value is None:
        return ""
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def format_series_csv(points: Sequence[MarketQuote]) -> str:
    """Return the reserves CSV in US$ millions with ISO dates."""
    output = io.StringIO()
    writer = csv.writer(
        output, delimiter=DELIMITER, lineterminator="\n"
    )
    writer.writerow(SERIES_HEADER)
    for point in sort_points(points):
        writer.writerow([
            point.data,
            _num(point.valor),
            point.unidade,
            point.origem,
            point.metodo,
        ])
    return output.getvalue()


def _items(payload: Mapping[str, object]) -> list[dict[str, object]]:
    serie = payload.get("serie")
    items = serie.get("itens") if isinstance(serie, dict) else None
    return [
        item for item in (items if isinstance(items, list) else [])
        if isinstance(item, dict)
    ]


def series_csv_from_payload(payload: Mapping[str, object]) -> str:
    """Return the series CSV from a serialized reserves payload."""
    output = io.StringIO()
    writer = csv.writer(
        output, delimiter=DELIMITER, lineterminator="\n"
    )
    writer.writerow(SERIES_HEADER)
    for item in sorted(
        _items(payload), key=lambda row: str(row.get("data"))
    ):
        writer.writerow([
            item.get("data", ""),
            _num(item.get("valor")),  # type: ignore[arg-type]
            item.get("unidade", ""),
            item.get("origem", ""),
            item.get("metodo", ""),
        ])
    return output.getvalue()


def series_artifact(points: Sequence[MarketQuote]) -> ExportArtifact:
    """Return the default reserves series CSV artifact."""
    return ExportArtifact(SERIES_FILENAME, format_series_csv(points))


def series_artifact_from_payload(
    payload: Mapping[str, object],
) -> ExportArtifact:
    """Return the default series CSV artifact from a payload."""
    return ExportArtifact(
        SERIES_FILENAME, series_csv_from_payload(payload)
    )


def json_artifact_from_payload(
    payload: Mapping[str, object],
) -> ExportArtifact:
    """Return the default reserves JSON artifact from a payload."""
    return ExportArtifact(JSON_FILENAME, format_market_json(payload))


__all__ = [
    "JSON_FILENAME",
    "SERIES_FILENAME",
    "SERIES_HEADER",
    "format_series_csv",
    "json_artifact_from_payload",
    "series_artifact",
    "series_artifact_from_payload",
    "series_csv_from_payload",
]
