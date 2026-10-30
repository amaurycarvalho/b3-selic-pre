"""Utilitários compartilhados pelos loaders do Tesouro Direto."""

from __future__ import annotations

from collections.abc import Callable


def emit(callback: Callable[[str], None] | None, stage: str) -> None:
    """Emit a loading stage when a callback was provided."""
    if callback is not None:
        callback(stage)


def metadata_time(metadata: dict[str, object]) -> str | None:
    """Return the cache timestamp used in the status line."""
    for key in ("checked_at", "downloaded_at"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def metadata_date(metadata: dict[str, object]) -> str | None:
    """Return the latest data date recorded in the cache metadata."""
    value = metadata.get("last_data_date")
    return value if isinstance(value, str) and value else None


def source(origin: str) -> str:
    """Map a client origin to the user-facing source label."""
    return "Cache" if origin == "cache" else "Tesouro Transparente"


__all__ = ["emit", "metadata_date", "metadata_time", "source"]
