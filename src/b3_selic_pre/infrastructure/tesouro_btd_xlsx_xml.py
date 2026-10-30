"""Leitura estrutural de planilhas XLSX sem dependências externas."""

from __future__ import annotations

import zipfile
from xml.etree import ElementTree

from b3_selic_pre.application.tesouro import TesouroDataError, normalizar_texto

_SHEET_NUMBER = "anexo 2.1"
_SHEET_STOCK = "estoque por titulo"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in element.iter() if _local(child.tag) == name]


def _cell_text(element: ElementTree.Element) -> str:
    return "".join(
        child.text or "" for child in _find(element, "t")
    )


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        data = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ElementTree.fromstring(data)
    return [_cell_text(item) for item in _find(root, "si")]


def _relationship_targets(archive: zipfile.ZipFile) -> dict[str, str]:
    try:
        data = archive.read("xl/_rels/workbook.xml.rels")
    except KeyError:
        return {}
    root = ElementTree.fromstring(data)
    targets: dict[str, str] = {}
    for item in _find(root, "Relationship"):
        identifier = item.get("Id")
        target = item.get("Target")
        if identifier and target:
            targets[identifier] = target
    return targets


def _worksheet_path(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return f"xl/{target}"


def _sheet_candidates(
    archive: zipfile.ZipFile,
) -> list[tuple[str, str]]:
    try:
        data = archive.read("xl/workbook.xml")
    except KeyError as exc:
        raise TesouroDataError("Workbook do BTD ausente.") from exc
    root = ElementTree.fromstring(data)
    targets = _relationship_targets(archive)
    result: list[tuple[str, str]] = []
    for sheet in _find(root, "sheet"):
        name = sheet.get("name") or ""
        relation = next(
            (
                value
                for key, value in sheet.attrib.items()
                if _local(key) == "id"
            ),
            "",
        )
        target = targets.get(relation)
        if target:
            result.append((name, _worksheet_path(target)))
    return result


def _first_cell_text(
    archive: zipfile.ZipFile, path: str, shared: list[str]
) -> str:
    try:
        root = ElementTree.fromstring(archive.read(path))
    except (KeyError, ElementTree.ParseError):
        return ""
    cells = _find(root, "c")
    if not cells:
        return ""
    return _cell_value(cells[0], shared)


def _is_stock_label(value: str) -> bool:
    text = normalizar_texto(value)
    return _SHEET_NUMBER in text and _SHEET_STOCK in text


def _stock_sheet(
    archive: zipfile.ZipFile, shared: list[str]
) -> bytes:
    candidates = _sheet_candidates(archive)
    for name, path in candidates:
        if _is_stock_label(name):
            return archive.read(path)
    for _name, path in candidates:
        if _is_stock_label(_first_cell_text(archive, path, shared)):
            return archive.read(path)
    raise TesouroDataError("Aba de estoque por título do BTD não encontrada.")


def _column_index(reference: str) -> int:
    letters = "".join(char for char in reference if char.isalpha())
    value = 0
    for char in letters.upper():
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value - 1


def _cell_value(cell: ElementTree.Element, shared: list[str]) -> str:
    kind = cell.get("t", "")
    if kind == "inlineStr":
        return _cell_text(cell)
    values = _find(cell, "v")
    if not values:
        return ""
    text = values[0].text or ""
    if kind == "s":
        try:
            return shared[int(text)]
        except (ValueError, IndexError):
            return ""
    return text


def _rows(data: bytes, shared: list[str]) -> list[dict[int, str]]:
    """Return the sheet cells grouped by row and column index."""
    root = ElementTree.fromstring(data)
    rows: list[dict[int, str]] = []
    for row in _find(root, "row"):
        cells = {
            _column_index(cell.get("r") or ""): _cell_value(cell, shared)
            for cell in _find(row, "c")
        }
        if cells:
            rows.append(cells)
    return rows


def read_stock_rows(archive: zipfile.ZipFile) -> list[dict[int, str]]:
    """Return the cells of the BTD stock worksheet, keyed by column."""
    try:
        shared = _shared_strings(archive)
        sheet = _stock_sheet(archive, shared)
        return _rows(sheet, shared)
    except (KeyError, ElementTree.ParseError) as exc:
        raise TesouroDataError(
            "XLSX do BTD em formato inesperado."
        ) from exc


__all__ = ["read_stock_rows"]
