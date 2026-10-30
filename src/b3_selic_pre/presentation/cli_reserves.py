"""Handler do subcomando reservas, separado dos comandos da curva."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from b3_selic_pre.application.reserves.config import meses_janela
from b3_selic_pre.application.reserves.export import (
    json_artifact_from_payload,
    series_artifact_from_payload,
)
from b3_selic_pre.application.reserves.payloads import filter_payload_window
from b3_selic_pre.application.reserves.series import shift_months
from b3_selic_pre.presentation.cli_data import write_artifacts


def _items(payload: dict[str, object]) -> list[dict[str, object]]:
    serie = payload.get("serie")
    items = serie.get("itens") if isinstance(serie, dict) else None
    return [
        item for item in (items if isinstance(items, list) else [])
        if isinstance(item, dict)
    ]


def _default_window(
    payload: dict[str, object], janela: str
) -> tuple[str | None, str | None]:
    latest = payload.get("latest_data_date")
    if not isinstance(latest, str) or not latest:
        items = _items(payload)
        latest = str(items[-1].get("data")) if items else None
    if latest is None:
        return None, None
    try:
        start = shift_months(
            date.fromisoformat(latest), -meses_janela(janela)
        )
    except ValueError:
        return None, None
    return start.isoformat(), latest


def _load(
    args: argparse.Namespace, controller: object
) -> tuple[dict[str, object] | None, int]:
    try:
        payload = (
            controller.refresh(force=args.no_cache)  # type: ignore[attr-defined]
            if args.atualizar or args.no_cache
            else controller.load_cache_only()  # type: ignore[attr-defined]
        )
    except Exception as exc:
        print(
            f"Falha ao consultar as reservas: {exc}", file=sys.stderr
        )
        return None, 1
    return payload, 0


def _artifacts(
    filtered: dict[str, object], formato: str
) -> list[object]:
    if formato == "json":
        return [json_artifact_from_payload(filtered)]
    return [series_artifact_from_payload(filtered)]


def _write(
    filtered: dict[str, object], args: argparse.Namespace
) -> int:
    try:
        return write_artifacts(
            _artifacts(filtered, args.formato), args.saida
        )
    except OSError as exc:
        print(f"Falha ao gravar a saída: {exc}", file=sys.stderr)
        return 1


def _validate_window(
    args: argparse.Namespace,
) -> tuple[str | None, str | None, int]:
    from b3_selic_pre.presentation.cli_commands import _market_date

    inicio, code = _market_date(args.inicio, "--inicio")
    if code:
        return None, None, code
    fim, code = _market_date(args.fim, "--fim")
    if code:
        return None, None, code
    if inicio is not None and fim is not None and inicio > fim:
        print("--inicio não pode ser posterior a --fim.", file=sys.stderr)
        return None, None, 2
    return inicio, fim, 0


def reservas(args: argparse.Namespace, controller: object) -> int:
    """Consulta ou exporta a série de reservas internacionais."""
    inicio, fim, code = _validate_window(args)
    if code:
        return code
    payload, code = _load(args, controller)
    if payload is None:
        return code
    if inicio is None and fim is None:
        inicio, fim = _default_window(payload, args.janela)
    filtered = filter_payload_window(payload, inicio, fim)
    if filtered is None:
        print(
            "Não há dados de reservas em cache para a janela solicitada. "
            "Use --atualizar para buscar a série do BCB.",
            file=sys.stderr,
        )
        return 1
    return _write(filtered, args)


__all__ = ["reservas"]
