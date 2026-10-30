"""Parsing da aba de estoque por título do XLSX do BTD."""

from __future__ import annotations

import io
import re
import zipfile
from decimal import Decimal, InvalidOperation

from b3_selic_pre.application.tesouro import TesouroDataError, normalizar_texto
from b3_selic_pre.domain.models import EstoqueMensalTitulo
from b3_selic_pre.infrastructure.tesouro_btd_xlsx_xml import read_stock_rows

_MONTH_NAMES = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}
_MONTH = re.compile(
    r"^(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[/.]?(\d{2})$",
    re.IGNORECASE,
)
_MILLION = Decimal(1000000)
_PERCENT_MARKERS = ("percentual", "participacao", "composicao")
_AGGREGATE_LABELS = ("estoque", "total", "soma")


def _month(value: str) -> str | None:
    match = _MONTH.match(value.strip())
    if match is None:
        return None
    number = _MONTH_NAMES[match.group(1).casefold()]
    return f"20{match.group(2)}-{number:02d}"


def _month_columns(row: dict[int, str]) -> dict[int, str]:
    columns: dict[int, str] = {}
    for index, value in row.items():
        month = _month(value)
        if month is not None:
            columns[index] = month
    return columns


def _marker(row: dict[int, str]) -> bool:
    for value in row.values():
        text = normalizar_texto(value)
        if "%" in value or any(item in text for item in _PERCENT_MARKERS):
            return True
    return False


def _label(row: dict[int, str], first_column: int) -> str:
    left = [
        (index, value.strip())
        for index, value in row.items()
        if index < first_column and value.strip()
    ]
    return min(left)[1] if left else ""


def _aggregate_label(value: str) -> bool:
    text = normalizar_texto(value)
    return text in _AGGREGATE_LABELS or text.startswith("total ")


def _million(value: str) -> Decimal | None:
    text = value.strip()
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite():
        return None
    return number * _MILLION


def _records(
    rows: list[dict[int, str]],
) -> list[EstoqueMensalTitulo]:
    records: list[EstoqueMensalTitulo] = []
    header: dict[int, str] | None = None
    for row in rows:
        months = _month_columns(row)
        if header is None:
            if len(months) >= 2:
                header = months
            continue
        if len(months) >= 2 or _marker(row):
            break
        title = _label(row, min(header))
        if not title or _aggregate_label(title):
            continue
        for column, month in header.items():
            value = _million(row.get(column, ""))
            if value is not None:
                records.append(EstoqueMensalTitulo(title, month, value))
    return records


def parse_btd_xlsx(data: bytes) -> list[EstoqueMensalTitulo]:
    """Parse the stock-by-title worksheet into aggregated monthly records."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise TesouroDataError("Anexo do BTD não é um XLSX válido.") from exc
    with archive:
        records = _records(read_stock_rows(archive))
    if not records:
        raise TesouroDataError("Aba de estoque do BTD sem registros de valor.")
    return records


__all__ = ["parse_btd_xlsx"]
