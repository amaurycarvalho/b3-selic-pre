"""Opaque cursor pagination used by the MCP tool payloads."""

from __future__ import annotations

import base64
import json

CURSOR_VERSION = 1
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


def encode_cursor(offset: int) -> str:
    """Encode an opaque pagination cursor."""
    raw = json.dumps(
        {"v": CURSOR_VERSION, "o": offset},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    """Decode an opaque cursor, raising when invalid."""
    if cursor is None or cursor == "":
        return 0
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(f"{cursor}{padding}".encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise ValueError("cursor inválido") from exc
    if not isinstance(data, dict):
        raise TypeError("cursor inválido")
    if data.get("v") != CURSOR_VERSION:
        raise ValueError("cursor inválido")
    offset = data.get("o")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("cursor inválido")
    return offset


def paginate(
    items: list[object],
    cursor: str | None,
    limit: int | None,
    default_limit: int = DEFAULT_PAGE_SIZE,
    max_limit: int = MAX_PAGE_SIZE,
) -> tuple[list[object], str | None]:
    """Return one page and the next cursor when there is more content."""
    try:
        offset = decode_cursor(cursor)
    except (ValueError, TypeError) as exc:
        raise ValueError("cursor inválido") from exc
    size = default_limit if limit is None else limit
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("limite inválido")
    size = min(size, max_limit)
    page = items[offset : offset + size]
    next_offset = offset + len(page)
    next_cursor = (
        encode_cursor(next_offset) if next_offset < len(items) else None
    )
    return page, next_cursor
