"""Formatadores CSV/JSON e artefatos de exportação de mercado."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence

from b3_selic_pre.application.cli_services import ExportArtifact
from b3_selic_pre.application.market.payloads import market_payload
from b3_selic_pre.domain.market import (
    ForecastPoint,
    MarketSeries,
    PolicyIndicators,
)

HISTORY_HEADER = ("DATA", "ATIVO", "VALOR", "UNIDADE", "ORIGEM", "METODO")
FORECAST_HEADER = (
    "DATA",
    "ATIVO",
    "CENARIO",
    "INFERIOR_80",
    "SUPERIOR_80",
    "INFERIOR_95",
    "SUPERIOR_95",
    "METODO",
)
DELIMITER = ";"


def _num(value: float | None) -> str:
    if value is None:
        return ""
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def format_history_csv(series: Sequence[MarketSeries]) -> str:
    """Return the history CSV with ISO dates, semicolons and dot decimals."""
    output = io.StringIO()
    writer = csv.writer(
        output, delimiter=DELIMITER, lineterminator="\n"
    )
    writer.writerow(HISTORY_HEADER)
    rows = [
        point
        for item in series
        for point in item.pontos
    ]
    for point in sorted(rows, key=lambda item: (item.data, item.ativo)):
        writer.writerow([
            point.data,
            point.ativo,
            _num(point.valor),
            point.unidade,
            point.origem,
            point.metodo,
        ])
    return output.getvalue()


def _band_points(point: ForecastPoint) -> dict[int, tuple[str, str]]:
    return {
        band.nivel: (_num(band.inferior), _num(band.superior))
        for band in point.bandas
    }


def format_forecast_csv(points: Sequence[ForecastPoint]) -> str:
    """Return the forecast CSV with 80% and 95% bands."""
    output = io.StringIO()
    writer = csv.writer(
        output, delimiter=DELIMITER, lineterminator="\n"
    )
    writer.writerow(FORECAST_HEADER)
    for point in sorted(points, key=lambda item: (item.data, item.ativo)):
        bands = _band_points(point)
        low80, high80 = bands.get(80, ("", ""))
        low95, high95 = bands.get(95, ("", ""))
        writer.writerow([
            point.data,
            point.ativo,
            point.cenario,
            low80,
            high80,
            low95,
            high95,
            point.metodo,
        ])
    return output.getvalue()


def format_market_json(payload: Mapping[str, object]) -> str:
    """Return the structured JSON payload shared with MCP."""
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _payload_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def history_csv_from_payload(payload: Mapping[str, object]) -> str:
    """Return the history CSV from a serialized market payload."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=DELIMITER, lineterminator="\n")
    writer.writerow(HISTORY_HEADER)
    series = _payload_dict(payload.get("series"))
    rows = [
        _payload_dict(item)
        for value in series.values()
        for item in _payload_dict(value).get("itens", []) or []
    ]
    for item in sorted(
        rows, key=lambda row: (str(row.get("data")), str(row.get("ativo")))
    ):
        writer.writerow([
            item.get("data", ""),
            item.get("ativo", ""),
            _num(item.get("valor")),  # type: ignore[arg-type]
            item.get("unidade", ""),
            item.get("origem", ""),
            item.get("metodo", ""),
        ])
    return output.getvalue()


def _bands_by_level(item: dict[str, object]) -> dict[int, dict[str, object]]:
    bands = item.get("bandas")
    result: dict[int, dict[str, object]] = {}
    for raw in bands if isinstance(bands, list) else []:
        band = _payload_dict(raw)
        level = band.get("nivel")
        if isinstance(level, int):
            result[level] = band
    return result


def forecast_csv_from_payload(payload: Mapping[str, object]) -> str:
    """Return the forecast CSV from a serialized market payload."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=DELIMITER, lineterminator="\n")
    writer.writerow(FORECAST_HEADER)
    previsao = _payload_dict(payload.get("previsao"))
    rows = [
        _payload_dict(item)
        for value in previsao.values()
        for item in _payload_dict(value).get("itens", []) or []
    ]
    for item in sorted(
        rows, key=lambda row: (str(row.get("data")), str(row.get("ativo")))
    ):
        bands = _bands_by_level(item)
        band80 = bands.get(80, {})
        band95 = bands.get(95, {})
        writer.writerow([
            item.get("data", ""),
            item.get("ativo", ""),
            item.get("cenario", ""),
            _num(band80.get("inferior")),  # type: ignore[arg-type]
            _num(band80.get("superior")),  # type: ignore[arg-type]
            _num(band95.get("inferior")),  # type: ignore[arg-type]
            _num(band95.get("superior")),  # type: ignore[arg-type]
            item.get("metodo", ""),
        ])
    return output.getvalue()


def history_artifact(series: Sequence[MarketSeries]) -> ExportArtifact:
    """Return the default history CSV artifact."""
    return ExportArtifact(
        "mercado-historico.csv", format_history_csv(series)
    )


def forecast_artifact(points: Sequence[ForecastPoint]) -> ExportArtifact:
    """Return the default forecast CSV artifact."""
    return ExportArtifact("mercado-previsao.csv", format_forecast_csv(points))


def history_artifact_from_payload(
    payload: Mapping[str, object],
) -> ExportArtifact:
    """Return the default history CSV artifact from a payload."""
    return ExportArtifact(
        "mercado-historico.csv", history_csv_from_payload(payload)
    )


def forecast_artifact_from_payload(
    payload: Mapping[str, object],
) -> ExportArtifact:
    """Return the default forecast CSV artifact from a payload."""
    return ExportArtifact(
        "mercado-previsao.csv", forecast_csv_from_payload(payload)
    )


def json_artifact_from_payload(
    payload: Mapping[str, object],
) -> ExportArtifact:
    """Return the default JSON artifact from a payload."""
    return ExportArtifact("mercado.json", format_market_json(payload))


def json_artifact(
    janela: Mapping[str, str],
    series: Mapping[str, MarketSeries],
    forecasts: Mapping[str, object],
    indicators: PolicyIndicators,
    origem: str,
    gerado_em: str,
) -> ExportArtifact:
    """Return the default JSON artifact for the full market payload."""
    payload = market_payload(
        janela,
        series,
        forecasts,  # type: ignore[arg-type]
        indicators,
        origem,
        gerado_em,
    )
    return ExportArtifact("mercado.json", format_market_json(payload))
