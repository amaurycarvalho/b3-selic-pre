"""Persistência headless da data de referência usada pela GUI."""

from __future__ import annotations


def record_reference(
    settings: object,
    date: str,
    has_data: bool,
) -> None:
    """Persist ``date`` as the last loaded reference when data exists."""
    if has_data and date:
        settings["data_referencia"] = date
