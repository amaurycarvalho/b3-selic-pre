"""Fixtures compartilhadas para os testes do BTD."""

from __future__ import annotations

import io
import zipfile
from xml.sax.saxutils import escape

SHEET_NAME = "ANEXO 2.1 - ESTOQUE POR TÍTULO"

_WORKBOOK = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/'
    'spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/'
    '2006/relationships">'
    "<sheets>"
    f'<sheet name="{escape(SHEET_NAME)}" sheetId="1" r:id="rId1"/>'
    "</sheets></workbook>"
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
    '2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    "</Relationships>"
)


def _text_cell(reference: str, value: str) -> str:
    return (
        f'<c r="{reference}" t="inlineStr"><is><t>'
        f"{escape(value)}</t></is></c>"
    )


def _number_cell(reference: str, value: str) -> str:
    return f'<c r="{reference}"><v>{value}</v></c>'


def _row(number: int, cells: list[str]) -> str:
    return f'<row r="{number}">{"".join(cells)}</row>'


def stock_rows() -> str:
    rows = [
        _row(1, [_text_cell("A1", SHEET_NAME)]),
        _row(3, [_text_cell("A3", "ESTOQUE POR TÍTULO (R$ MILHÕES)")]),
        _row(
            4,
            [
                _text_cell("A4", "Título"),
                _text_cell("B4", "Ago/26"),
                _text_cell("C4", "Set/26"),
            ],
        ),
        _row(
            5,
            [
                _text_cell("A5", "Estoque"),
                _number_cell("B5", "150"),
                _number_cell("C5", "150"),
            ],
        ),
        _row(
            6,
            [
                _text_cell("A6", "Tesouro Selic 2029"),
                _number_cell("B6", "100"),
                _number_cell("C6", "120"),
            ],
        ),
        _row(
            7,
            [
                _text_cell("A7", "Tesouro IPCA+ 2035"),
                _number_cell("B7", "50"),
                _number_cell("C7", "30"),
            ],
        ),
        _row(9, [_text_cell("A9", "PARTICIPAÇÃO PERCENTUAL (%)")]),
        _row(
            10,
            [
                _text_cell("A10", "Título"),
                _text_cell("B10", "Ago/26"),
                _text_cell("C10", "Set/26"),
            ],
        ),
        _row(
            11,
            [
                _text_cell("A11", "Tesouro Selic 2029"),
                _number_cell("B11", "0.66"),
                _number_cell("C11", "0.8"),
            ],
        ),
    ]
    return "".join(rows)


def xlsx_bytes(rows: str | None = None) -> bytes:
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main">'
        f"<sheetData>{rows or stock_rows()}</sheetData></worksheet>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", _WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", _RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return buffer.getvalue()


def xlsx_renamed_sheet() -> bytes:
    buffer = io.BytesIO()
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main">'
        f"<sheetData>{stock_rows()}</sheetData></worksheet>"
    )
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "xl/workbook.xml", _WORKBOOK.replace(SHEET_NAME, "Índice")
        )
        archive.writestr("xl/_rels/workbook.xml.rels", _RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return buffer.getvalue()


def xlsx_without_stock_sheet() -> bytes:
    workbook = _WORKBOOK.replace(SHEET_NAME, "Índice")
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main"><sheetData>'
        '<row r="1"><c r="A1" t="inlineStr"><is><t>Índice</t></is></c></row>'
        "</sheetData></worksheet>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", _RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return buffer.getvalue()


def xlsx_without_values() -> bytes:
    rows = _row(1, [_text_cell("A1", SHEET_NAME)]) + _row(
        4,
        [
            _text_cell("A4", "Título"),
            _text_cell("B4", "Set/26"),
        ],
    )
    return xlsx_bytes(rows)
