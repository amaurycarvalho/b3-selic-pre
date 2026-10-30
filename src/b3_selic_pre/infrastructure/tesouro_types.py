"""Tipos de dados compartilhados pelo cliente CKAN do Tesouro."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TesouroResource:
    """CKAN dataset/resource metadata needed by the downloader."""

    dataset_name: str
    dataset_id: str
    resource_id: str
    resource_url: str
    last_modified: str | None


@dataclass(frozen=True)
class TesouroDownload:
    """Result of a conditional CSV download."""

    status: int
    data: bytes | None
    etag: str | None
    last_modified: str | None
