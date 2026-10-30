"""Chave composta e estável do cache derivado de mercado."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping


def _canonical(payload: object) -> str:
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def composite_key(
    source_hashes: Mapping[str, str],
    resolution: Mapping[str, object],
    projection: Mapping[str, object],
    schema_version: int,
) -> str:
    """Return a stable SHA-256 key from sources and parameters."""
    matrix = "\n".join(
        f"{name}={value}" for name, value in sorted(source_hashes.items())
    )
    payload = {
        "fontes": matrix,
        "resolucao": dict(resolution),
        "projecao": dict(projection),
        "schema_version": schema_version,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def key_from_config(
    source_hashes: Mapping[str, str],
    config: object,
) -> str:
    """Return the composite key for a :class:`MarketConfig` instance."""
    return composite_key(
        source_hashes,
        config.parametros_resolucao(),  # type: ignore[attr-defined]
        config.parametros_projecao(),  # type: ignore[attr-defined]
        config.schema_version,  # type: ignore[attr-defined]
    )
