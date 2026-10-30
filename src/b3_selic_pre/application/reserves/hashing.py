"""Hash canônico dos pontos e dos parâmetros de reservas."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from b3_selic_pre.application.reserves.config import (
    RETENCAO_ANOS,
    SCHEMA_VERSION,
    ReservesConfig,
)
from b3_selic_pre.application.reserves.parsing import sort_points
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import FONTE_RESERVAS, UNIDADE_RESERVAS


def canonical_pairs(
    points: Sequence[MarketQuote],
) -> list[tuple[str, str]]:
    """Return canonical ``(date, value)`` pairs for hashing."""
    return [
        (point.data, f"{point.valor:.10f}")
        for point in sort_points(points)
    ]


def points_hash(points: Sequence[MarketQuote]) -> str:
    """Return a stable SHA-256 over the canonical date/value pairs."""
    content = "\n".join(
        f"{day}|{value}" for day, value in canonical_pairs(points)
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _config_params(config: object | None) -> dict[str, object]:
    if config is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "retencao_anos": RETENCAO_ANOS,
        }
    parametros = getattr(config, "parametros", None)
    if callable(parametros):
        return dict(parametros())
    if isinstance(config, Mapping):
        return dict(config)
    return {}


def snapshot_hash(
    points: Sequence[MarketQuote],
    config: ReservesConfig | Mapping[str, object] | None = None,
    reference: str | None = None,
    years: int | None = None,
) -> str:
    """Return the precompute hash over the retained canonical points."""
    from b3_selic_pre.application.reserves.series import retained_points

    params = _config_params(config)
    retention = (
        years
        if years is not None
        else int(params.get("retencao_anos", RETENCAO_ANOS))
    )
    retained = retained_points(points, reference, retention)
    payload = {
        "schema_version": int(
            params.get("schema_version", SCHEMA_VERSION)
        ),
        "fonte": FONTE_RESERVAS,
        "unidade": UNIDADE_RESERVAS,
        "pares": canonical_pairs(retained),
        "parametros": params,
    }
    content = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


__all__ = [
    "canonical_pairs",
    "points_hash",
    "snapshot_hash",
]
