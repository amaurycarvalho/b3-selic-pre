"""Casos de uso da camada de aplicação para taxas de juros prefixados."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from b3_selic_pre.application.formatting import (
    format_cli_rows,
    format_evolution_csv,
    format_yearly_rows,
)
from b3_selic_pre.domain.constants import EVOLUTION_DAYS
from b3_selic_pre.domain.models import RateRecord


class QueryDateError(ValueError):
    """Erro de validação de uma data de consulta."""


class FutureQueryDateError(QueryDateError):
    """A data informada está no futuro."""


class OldQueryDateError(QueryDateError):
    """A data informada está fora da janela de histórico disponível."""


@dataclass(frozen=True)
class RateStatistics:
    """Menor e maior taxa observadas em um conjunto de registros."""

    min_rate: float
    max_rate: float


def default_reference_date() -> str:
    """Retorna a data de referência atual no formato YYYY-MM-DD."""
    return datetime.now(UTC).date().isoformat()


def validate_reference_date(reference_date: str) -> str:
    """Valida e normaliza uma data de referência para o formato YYYY-MM-DD."""
    try:
        parsed = datetime.strptime(reference_date, "%Y-%m-%d").replace(tzinfo=UTC).date()
    except ValueError as exc:
        raise ValueError("Use uma data no formato YYYY-MM-DD.") from exc
    return parsed.isoformat()


def validate_query_date(
    reference_date: str,
    today: str | None = None,
    max_age_days: int = 30,
) -> str:
    """Valida formato, data futura e janela máxima de histórico da consulta."""
    normalized = validate_reference_date(reference_date)
    current = validate_reference_date(today or default_reference_date())
    parsed = datetime.strptime(normalized, "%Y-%m-%d").replace(
        tzinfo=UTC
    ).date()
    current_date = datetime.strptime(current, "%Y-%m-%d").replace(
        tzinfo=UTC
    ).date()
    if parsed > current_date:
        raise FutureQueryDateError("Data futura. Informe uma data até hoje.")
    cutoff = current_date - timedelta(days=max_age_days)
    if parsed < cutoff:
        raise OldQueryDateError(
            "Data muito antiga. O histórico disponível cobre apenas os "
            "últimos 30 dias. Informe uma data mais recente."
        )
    return normalized


def nearest_business_day(date_str: str) -> str:
    """Retorna a data útil mais próxima (retrocede fins de semana)."""
    normalized = validate_reference_date(date_str)
    parsed = datetime.strptime(normalized, "%Y-%m-%d").replace(
        tzinfo=UTC
    ).date()
    while parsed.weekday() >= 5:
        parsed -= timedelta(days=1)
    return parsed.isoformat()


def days_ago(base_date: str, days: int) -> str:
    """Retorna a data ``days`` dias antes de ``base_date`` no formato ISO."""
    parsed = datetime.strptime(base_date, "%Y-%m-%d").replace(tzinfo=UTC).date()
    return (parsed - timedelta(days=days)).isoformat()


def evolution_dates(base_date: str) -> list[str]:
    """Retorna as datas da janela de evolução relativas a ``base_date``."""
    return [days_ago(base_date, days) for days in EVOLUTION_DAYS]


def resolve_reference_date(
    explicit_date: str | None = None,
    use_today: bool = False,
) -> str:
    """Resolve a data de referência a partir de uma opção de CLI."""
    if use_today:
        return default_reference_date()
    return explicit_date or default_reference_date()


def consolidate_by_year(records: list[RateRecord]) -> list[dict[str, int | float]]:
    """Consolida as taxas por ano, com as taxas mínima e máxima de cada ano."""
    groups: dict[int, dict[str, int | float]] = {}
    for r in records:
        year = r.day360 // 365
        rate = float(r.rate.replace(",", "."))
        if year in groups:
            g = groups[year]
            g["min_rate"] = min(g["min_rate"], rate)
            g["max_rate"] = max(g["max_rate"], rate)
        else:
            groups[year] = {"year": year, "min_rate": rate, "max_rate": rate}
    return [groups[y] for y in sorted(groups)]


def average_rate_by_year(records: list[RateRecord]) -> dict[int, float]:
    """Calcula a taxa média por ano a partir das taxas mínima e máxima."""
    consolidated = consolidate_by_year(records)
    return {g["year"]: (g["min_rate"] + g["max_rate"]) / 2 for g in consolidated}


def to_curve_longa(records: list[RateRecord]) -> list[RateRecord]:
    """Converta uma curva bruta na série de taxas médias por ano."""
    averages = average_rate_by_year(records)
    return [
        RateRecord(
            day252=year * 252,
            day360=year * 365,
            rate=f"{averages[year]:.2f}".replace(".", ","),
        )
        for year in sorted(averages)
    ]


def to_curve_longa_historical(
    historical_data: dict[str, list[RateRecord]] | None,
) -> dict[str, list[RateRecord]] | None:
    """Converta cada curva de um histórico para a série de médias anuais."""
    if historical_data is None:
        return None
    return {
        date_str: to_curve_longa(records)
        for date_str, records in historical_data.items()
    }


def rate_statistics(records: list[RateRecord]) -> RateStatistics | None:
    """Calcula a menor e a maior taxa dos registros, ou ``None`` sem dados."""
    if not records:
        return None
    rates = [float(r.rate.replace(",", ".")) for r in records]
    return RateStatistics(min_rate=min(rates), max_rate=max(rates))


def build_rates_table(records: list[RateRecord], yearly: bool = False) -> str:
    """Formata a tabela CSV de taxas para a CLI, bruta ou consolidada por ano."""
    if yearly:
        return format_yearly_rows(consolidate_by_year(records))
    return format_cli_rows(records)


def build_export_text(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None = None,
    view_mode: str = "raw",
    evolution_active: bool = False,
) -> str | None:
    """Seleciona o conteúdo CSV a exportar, ou ``None`` quando não há dados."""
    if evolution_active and historical_data:
        return format_evolution_csv(historical_data)
    if not records:
        return None
    return build_rates_table(records, yearly=view_mode == "consolidated")


def create_shortcut_with_message(create_shortcut: Callable[[], None]) -> str:
    """Executa a criação do atalho e devolve a mensagem de sucesso."""
    create_shortcut()
    return "Atalho criado em ~/Desktop/ e ~/.local/share/applications/."
