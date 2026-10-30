"""Combinação de metadados de múltiplos recursos do Tesouro."""

from __future__ import annotations


def combine_metadata(
    resources: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Combine per-resource metadata into one dataset metadata view."""

    def values(key: str) -> list[str]:
        return [
            str(value[key])
            for value in resources.values()
            if value.get(key)
        ]

    checked = values("checked_at")
    modified = values("last_modified")
    dates = values("last_data_date")
    downloaded = values("downloaded_at")
    return {
        "resource_id": ",".join(values("resource_id")),
        "checked_at": max(checked) if checked else None,
        "downloaded_at": max(downloaded) if downloaded else None,
        "last_modified": max(modified) if modified else None,
        "last_data_date": max(dates) if dates else None,
        "resources": resources,
    }
