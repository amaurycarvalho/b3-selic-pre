"""Parsing e validação dos CSVs do Tesouro Direto."""

from __future__ import annotations

import csv
import io
import logging
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation

from b3_selic_pre.application.tesouro._errors import TesouroDataError
from b3_selic_pre.application.tesouro._resources import (
    RESOURCE_SPECS,
    resource_spec,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)

logger = logging.getLogger(__name__)

DELIMITER = ";"
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")
REQUIRED_COLUMNS = RESOURCE_SPECS["vendas"].required_columns
_TIPO_TITULO = "Tipo Titulo"
_VENCIMENTO = "Vencimento do Titulo"


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


def _mapear_cabecalho(
    header: list[str], required_columns: tuple[str, ...] = REQUIRED_COLUMNS
) -> dict[str, int]:
    normalized = {normalizar_texto(name): index for index, name in enumerate(header)}
    expected = {normalizar_texto(name): name for name in required_columns}
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


def _parse_month(value: str, line: int, column: str) -> str:
    parts = value.split("/")
    if len(parts) != 2:
        raise TesouroDataError(
            f"Linha {line}, coluna '{column}': mês inválido '{value}'."
        )
    try:
        month = int(parts[0])
        year = int(parts[1])
        if not 1 <= month <= 12:
            raise ValueError("month out of range")
    except ValueError as exc:
        raise TesouroDataError(
            f"Linha {line}, coluna '{column}': mês inválido '{value}'."
        ) from exc
    return f"{year:04d}-{month:02d}"


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


def _column(columns: dict[str, int], name: str) -> int:
    return columns[normalizar_texto(name)]


def _titulo(row: list[str], columns: dict[str, int], line: int) -> str:
    value = _cell(row, _column(columns, _TIPO_TITULO), line, _TIPO_TITULO)
    if not value:
        raise TesouroDataError(
            f"Linha {line}, coluna '{_TIPO_TITULO}': valor vazio."
        )
    return value


def _vencimento(row: list[str], columns: dict[str, int], line: int) -> str:
    return _parse_date(
        _cell(row, _column(columns, _VENCIMENTO), line, _VENCIMENTO),
        line,
        _VENCIMENTO,
    )


def _read_rows(
    data: bytes, required_columns: tuple[str, ...]
) -> tuple[dict[str, int], list[tuple[int, list[str]]]]:
    text = _decodificar(data)
    reader = csv.reader(io.StringIO(text), delimiter=DELIMITER)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise TesouroDataError("CSV do Tesouro vazio.") from exc
    columns = _mapear_cabecalho(header, required_columns)
    rows = [
        (line, row)
        for line, row in enumerate(reader, start=2)
        if any(cell.strip() for cell in row)
    ]
    if not rows:
        raise TesouroDataError("CSV do Tesouro sem registros.")
    return columns, rows


def _parse_venda_row(
    row: list[str], columns: dict[str, int], line: int
) -> VendaTesouroDireto:
    liquidacao = _parse_date(
        _cell(
            row,
            _column(columns, "Data de Liquidacao da Venda"),
            line,
            "Data de Liquidacao da Venda",
        ),
        line,
        "Data de Liquidacao da Venda",
    )
    return VendaTesouroDireto(
        tipo_titulo=_titulo(row, columns, line),
        vencimento=_vencimento(row, columns, line),
        data_liquidacao=liquidacao,
        pu=_parse_decimal(
            _cell(row, _column(columns, "PU"), line, "PU"), line, "PU"
        ),
        quantidade=_parse_decimal(
            _cell(row, _column(columns, "Quantidade"), line, "Quantidade"),
            line,
            "Quantidade",
        ),
        valor=_parse_decimal(
            _cell(row, _column(columns, "Valor"), line, "Valor"), line, "Valor"
        ),
    )


def parse_vendas(data: bytes) -> list[VendaTesouroDireto]:
    """Parse the downloaded CSV bytes into sale records without any I/O."""
    columns, rows = _read_rows(data, REQUIRED_COLUMNS)
    return [_parse_venda_row(row, columns, line) for line, row in rows]


def _resgate_columns(tipo_resgate: str) -> tuple[str, ...]:
    spec = resource_spec(tipo_resgate)
    if spec.key == "vendas":
        raise TesouroDataError("Recurso de resgate inválido.")
    return spec.required_columns


def _parse_resgate_row(
    row: list[str],
    columns: dict[str, int],
    line: int,
    tipo_resgate: str,
) -> ResgateTesouroDireto:
    pu = None
    if tipo_resgate != "recompra":
        pu = _parse_decimal(
            _cell(row, _column(columns, "PU"), line, "PU"), line, "PU"
        )
    data_resgate = _parse_date(
        _cell(row, _column(columns, "Data Resgate"), line, "Data Resgate"),
        line,
        "Data Resgate",
    )
    return ResgateTesouroDireto(
        tipo_resgate=tipo_resgate,
        tipo_titulo=_titulo(row, columns, line),
        vencimento=_vencimento(row, columns, line),
        data_resgate=data_resgate,
        pu=pu,
        quantidade=_parse_decimal(
            _cell(row, _column(columns, "Quantidade"), line, "Quantidade"),
            line,
            "Quantidade",
        ),
        valor=_parse_decimal(
            _cell(row, _column(columns, "Valor"), line, "Valor"), line, "Valor"
        ),
    )


def parse_resgates(data: bytes, tipo_resgate: str) -> list[ResgateTesouroDireto]:
    """Parse a redemption resource according to its logical type."""
    if tipo_resgate not in ("recompra", "cupom", "vencimento"):
        raise TesouroDataError(f"Tipo de resgate inválido: {tipo_resgate}.")
    columns, rows = _read_rows(data, _resgate_columns(tipo_resgate))
    return [
        _parse_resgate_row(row, columns, line, tipo_resgate)
        for line, row in rows
    ]


def _parse_estoque_row(
    row: list[str], columns: dict[str, int], line: int
) -> EstoqueTesouroDireto:
    mes = _parse_month(
        _cell(row, _column(columns, "Mes Estoque"), line, "Mes Estoque"),
        line,
        "Mes Estoque",
    )
    return EstoqueTesouroDireto(
        tipo_titulo=_titulo(row, columns, line),
        vencimento=_vencimento(row, columns, line),
        mes=mes,
        pu=_parse_decimal(
            _cell(row, _column(columns, "PU"), line, "PU"), line, "PU"
        ),
        quantidade=_parse_decimal(
            _cell(row, _column(columns, "Quantidade"), line, "Quantidade"),
            line,
            "Quantidade",
        ),
        valor_estoque=_parse_decimal(
            _cell(
                row,
                _column(columns, "Valor Estoque"),
                line,
                "Valor Estoque",
            ),
            line,
            "Valor Estoque",
        ),
    )


def parse_estoque(data: bytes) -> list[EstoqueTesouroDireto]:
    """Parse the monthly stock CSV into snapshot records."""
    columns, rows = _read_rows(data, resource_spec("estoque").required_columns)
    return [_parse_estoque_row(row, columns, line) for line, row in rows]
