"""Parsing e validação do CSV de vendas do Tesouro Direto."""

from __future__ import annotations

import csv
import io
import logging
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation

from b3_selic_pre.application.tesouro._errors import TesouroDataError
from b3_selic_pre.domain.models import VendaTesouroDireto

logger = logging.getLogger(__name__)

DELIMITER = ";"
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")
REQUIRED_COLUMNS = (
    "Tipo Titulo",
    "Vencimento do Titulo",
    "Data de Liquidacao da Venda",
    "PU",
    "Quantidade",
    "Valor",
)


def normalizar_texto(value: str) -> str:
    """Remove caixa e acentos para comparações e mapeamento de colunas."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(without_marks.casefold().split())


def _decodificar(data: bytes) -> str:
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise TesouroDataError("Não foi possível decodificar o CSV do Tesouro.")


def _mapear_cabecalho(header: list[str]) -> dict[str, int]:
    normalized = {normalizar_texto(name): index for index, name in enumerate(header)}
    expected = {normalizar_texto(name): name for name in REQUIRED_COLUMNS}
    missing = [
        original for key, original in expected.items() if key not in normalized
    ]
    if missing:
        raise TesouroDataError(
            "Colunas obrigatórias ausentes no CSV do Tesouro: "
            + ", ".join(missing)
        )
    unknown = [
        name
        for name in header
        if normalizar_texto(name) not in expected
    ]
    if unknown:
        logger.warning(
            "Colunas desconhecidas ignoradas no CSV do Tesouro: %s",
            ", ".join(unknown),
        )
    return {key: normalized[key] for key in expected}


def _cell(row: list[str], index: int, line: int, column: str) -> str:
    try:
        return row[index].strip()
    except IndexError as exc:
        raise TesouroDataError(
            f"Linha {line}: coluna '{column}' ausente."
        ) from exc


def _parse_date(value: str, line: int, column: str) -> str:
    parts = value.split("/")
    if len(parts) != 3:
        raise TesouroDataError(
            f"Linha {line}, coluna '{column}': data inválida '{value}'."
        )
    try:
        return date(int(parts[2]), int(parts[1]), int(parts[0])).isoformat()
    except ValueError as exc:
        raise TesouroDataError(
            f"Linha {line}, coluna '{column}': data inválida '{value}'."
        ) from exc


def _parse_decimal(value: str, line: int, column: str) -> Decimal:
    raw = value.strip()
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise TesouroDataError(
            f"Linha {line}, coluna '{column}': valor inválido '{value}'."
        ) from exc


def _parse_row(
    row: list[str], columns: dict[str, int], line: int
) -> VendaTesouroDireto:
    tipo = _cell(row, columns[normalizar_texto("Tipo Titulo")], line, "Tipo Titulo")
    if not tipo:
        raise TesouroDataError(
            f"Linha {line}, coluna 'Tipo Titulo': valor vazio."
        )
    vencimento = _parse_date(
        _cell(
            row,
            columns[normalizar_texto("Vencimento do Titulo")],
            line,
            "Vencimento do Titulo",
        ),
        line,
        "Vencimento do Titulo",
    )
    liquidacao = _parse_date(
        _cell(
            row,
            columns[normalizar_texto("Data de Liquidacao da Venda")],
            line,
            "Data de Liquidacao da Venda",
        ),
        line,
        "Data de Liquidacao da Venda",
    )
    return VendaTesouroDireto(
        tipo_titulo=tipo,
        vencimento=vencimento,
        data_liquidacao=liquidacao,
        pu=_parse_decimal(
            _cell(row, columns["pu"], line, "PU"), line, "PU"
        ),
        quantidade=_parse_decimal(
            _cell(row, columns["quantidade"], line, "Quantidade"),
            line,
            "Quantidade",
        ),
        valor=_parse_decimal(
            _cell(row, columns["valor"], line, "Valor"), line, "Valor"
        ),
    )


def parse_vendas(data: bytes) -> list[VendaTesouroDireto]:
    """Parse the downloaded CSV bytes into sale records without any I/O."""
    text = _decodificar(data)
    reader = csv.reader(io.StringIO(text), delimiter=DELIMITER)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise TesouroDataError("CSV do Tesouro vazio.") from exc
    columns = _mapear_cabecalho(header)
    sales: list[VendaTesouroDireto] = []
    for line, row in enumerate(reader, start=2):
        if not any(cell.strip() for cell in row):
            continue
        sales.append(_parse_row(row, columns, line))
    if not sales:
        raise TesouroDataError("CSV do Tesouro sem registros.")
    return sales
