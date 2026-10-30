"""Handler do subcomando ``feriados`` da CLI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime

from b3_selic_pre.application.calendar.service import CalendarService
from b3_selic_pre.application.cli_services import ExportArtifact
from b3_selic_pre.presentation.calendar_text import (
    adjustment_message,
    weekday_abbreviation,
)
from b3_selic_pre.presentation.cli_data import print_artifact, write_artifacts


def _year(args: argparse.Namespace) -> int:
    if args.ano is not None:
        return int(args.ano)
    if args.data is not None:
        return date.fromisoformat(args.data).year
    return datetime.now(UTC).year


def _parse_data(value: str) -> str | None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        print("Data inválida: use o formato AAAA-MM-DD.", file=sys.stderr)
        return None
    if parsed.isoformat() != value:
        print("Data inválida: use o formato AAAA-MM-DD.", file=sys.stderr)
        return None
    return value


def _cache_for(cache: object, year: int) -> object | None:
    data = cache.read(year)  # type: ignore[attr-defined]
    if data is None or not getattr(data, "published", False):
        print(
            f"Não há feriados em cache para {year}. "
            f"Use --atualizar para consultar a ANBIMA.",
            file=sys.stderr,
        )
        return None
    return data


def _items(data: object) -> list[dict[str, str]]:
    origin = str(getattr(data, "source", "ANBIMA"))
    return [
        {
            "data": holiday.date.isoformat(),
            "dia_semana": weekday_abbreviation(holiday.date),
            "nome": holiday.name,
            "origem": origin,
        }
        for holiday in getattr(data, "holidays", ())
    ]


def _csv(items: list[dict[str, str]]) -> str:
    lines = ["DATA;DIA_SEMANA;NOME;ORIGEM"]
    lines.extend(
        f"{item['data']};{item['dia_semana']};{item['nome']};{item['origem']}"
        for item in items
    )
    return "\n".join(lines) + "\n"


def _json(data: object, year: int, items: list[dict[str, str]]) -> str:
    return json.dumps(
        {
            "ano": year,
            "origem": getattr(data, "source", "ANBIMA"),
            "extraido_em": getattr(data, "fetched_at", ""),
            "feriados": items,
        },
        ensure_ascii=False,
    )


def _listing_artifact(
    data: object, year: int, formato: str
) -> ExportArtifact:
    items = _items(data)
    if formato == "json":
        return ExportArtifact(
            name=f"feriados-{year}.json",
            content=_json(data, year, items) + "\n",
        )
    return ExportArtifact(
        name=f"feriados-{year}.csv",
        content=_csv(items),
    )


def _query(
    data: object, value: str, service: CalendarService
) -> int:
    resolution = service.resolve_business_day(value)
    calendar = service.calendar_for(date.fromisoformat(value).year)
    parsed = date.fromisoformat(value)
    business = calendar.is_business_day(parsed)
    print(f"{value} ({weekday_abbreviation(parsed)})")
    print(f"Dia útil: {'sim' if business else 'não'}")
    if resolution.ajustada:
        print(adjustment_message(resolution))
    print(f"Origem: {getattr(data, 'source', 'ANBIMA')}")
    return 0


def _update(
    cache: object, service: CalendarService, years: list[int]
) -> None:
    for year in years:
        service.ensure_year(year, force=True)


def feriados(
    args: argparse.Namespace,
    cache: object,
    service: CalendarService,
) -> int:
    """List, query or export the holiday calendar from the CLI."""
    if args.ano is not None and args.data is not None:
        print("Informe --ano ou --data, não ambos.", file=sys.stderr)
        return 2
    data_value = None
    if args.data is not None:
        data_value = _parse_data(args.data)
        if data_value is None:
            return 2
    year = _year(args)
    if args.atualizar:
        _update(cache, service, [year])
    data = _cache_for(cache, year)
    if data is None:
        return 1
    if data_value is not None:
        return _query(data, data_value, service)
    artifact = _listing_artifact(data, year, args.formato)
    if args.saida is None:
        print_artifact(artifact)
        return 0
    return write_artifacts([artifact], args.saida)


__all__ = ["feriados"]
