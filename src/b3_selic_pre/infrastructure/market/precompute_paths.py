"""Resolução dos caminhos do pré-cálculo, com namespace opcional."""

from __future__ import annotations

from pathlib import Path

MANIFEST_NAME = "manifest.json"


def base_dir(cache_dir: Path, namespace: str | None) -> Path:
    """Return the namespace root, or the cache root when unscoped."""
    return cache_dir / namespace if namespace else cache_dir


def manifest_path(cache_dir: Path, namespace: str | None) -> Path:
    """Return the manifest path for a namespace."""
    return base_dir(cache_dir, namespace) / MANIFEST_NAME


def derived_path(
    cache_dir: Path, namespace: str | None, key: str
) -> Path:
    """Return the derived series path for a key."""
    return base_dir(cache_dir, namespace) / "derived" / key / "series.json"


def artifact_path(
    cache_dir: Path, namespace: str | None, key: str
) -> Path:
    """Return the precomputed artifact path for a key."""
    return (
        base_dir(cache_dir, namespace)
        / "precomputed"
        / key
        / "artifact.json"
    )


__all__ = [
    "MANIFEST_NAME",
    "artifact_path",
    "base_dir",
    "derived_path",
    "manifest_path",
]
