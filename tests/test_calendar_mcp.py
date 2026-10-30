"""Testes das tools MCP de feriados e do ajuste de data."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import pytest

from b3_selic_pre.application import mcp_services
from b3_selic_pre.application.calendar.ports import YearHolidays
from b3_selic_pre.application.calendar.service import CalendarService
from b3_selic_pre.domain.calendar import Holiday
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.calendar.cache import HolidayCache
from b3_selic_pre.infrastructure.disk_cache import DiskCache
from b3_selic_pre.presentation.mcp import curve_handlers
from b3_selic_pre.presentation.mcp.context import ToolContext
from b3_selic_pre.presentation.mcp.feriados_handlers import (
    feriados_consultar,
    feriados_exportar,
    feriados_listar,
)


class UnusedSource:
    def fetch_year(self, year):
        raise AssertionError("a fonte não pode ser chamada em modo somente cache")


def _year_2026():
    return YearHolidays(
        year=2026,
        holidays=(
            Holiday(date(2026, 1, 1), "Confraternizacao Universal"),
            Holiday(date(2026, 4, 3), "Sexta-feira Santa"),
        ),
        fetched_at="2026-10-30T12:00:00+00:00",
    )


def _context(tmp_path, with_data=True):
    cache = HolidayCache(tmp_path)
    if with_data:
        cache.write(_year_2026())
    service = CalendarService(UnusedSource(), cache)
    return ToolContext(
        cache=DiskCache(tmp_path / "rates"),
        settings_factory=lambda: type(
            "Settings", (), {"get": lambda self, key, default=None: ""}
        )(),
        holiday_cache=cache,
        calendar_service=service,
    )


def test_listar_reads_cache_only(tmp_path):
    ctx = _context(tmp_path)

    payload = feriados_listar({"ano": 2026}, ctx)

    assert payload["ano"] == 2026
    assert payload["itens"][0]["data"] == "2026-01-01"
    assert payload["itens"][0]["origem"] == "ANBIMA"


def test_listar_paginates(tmp_path):
    ctx = _context(tmp_path)

    payload = feriados_listar({"ano": 2026, "limite": 1}, ctx)

    assert len(payload["itens"]) == 1
    assert "nextCursor" in payload


def test_listar_without_year_returns_sem_dados(tmp_path):
    ctx = _context(tmp_path, with_data=False)

    with pytest.raises(mcp_services.DomainError) as exc:
        feriados_listar({"ano": 2026}, ctx)

    assert exc.value.motivo == "sem_dados"
    assert "--atualizar" in exc.value.payload()["dica"]


def test_consultar_holiday(tmp_path):
    ctx = _context(tmp_path)

    payload = feriados_consultar({"data": "2026-04-03"}, ctx)

    assert payload["dia_util"] is False
    assert payload["motivo"] == "feriado"
    assert payload["feriado"] == "Sexta-feira Santa"
    assert payload["data_resolvida"] == "2026-04-02"
    assert payload["ajustada"] is True


def test_consultar_business_day_preserves(tmp_path):
    ctx = _context(tmp_path)

    payload = feriados_consultar({"data": "2026-04-06"}, ctx)

    assert payload["dia_util"] is True
    assert payload["data_resolvida"] == "2026-04-06"
    assert payload["ajustada"] is False


def test_consultar_missing_year(tmp_path):
    ctx = _context(tmp_path, with_data=False)

    with pytest.raises(mcp_services.DomainError):
        feriados_consultar({"data": "2026-04-03"}, ctx)


def test_exportar_json_without_writing(tmp_path):
    ctx = _context(tmp_path)

    payload = feriados_exportar({"ano": 2026, "formato": "json"}, ctx)

    parsed = json.loads(payload["conteudo"])
    assert parsed["feriados"][0]["data"] == "2026-01-01"
    assert not list(tmp_path.glob("feriados-2026.json"))


def test_exportar_csv_format(tmp_path):
    ctx = _context(tmp_path)

    payload = feriados_exportar({"ano": 2026, "formato": "csv"}, ctx)

    assert payload["conteudo"].startswith("DATA;DIA_SEMANA;NOME;ORIGEM\n")


def test_consultar_curva_payload_reports_adjustment(tmp_path):
    today = datetime.now(UTC).date()
    holiday = today - timedelta(days=1)
    while holiday.weekday() != 4:
        holiday -= timedelta(days=1)
    resolved = holiday - timedelta(days=1)
    holiday_cache = HolidayCache(tmp_path / "calendar")
    holiday_cache.write(
        YearHolidays(
            year=holiday.year,
            holidays=(Holiday(holiday, "Feriado de teste"),),
            fetched_at="2026-10-30T12:00:00+00:00",
        )
    )
    service = CalendarService(UnusedSource(), holiday_cache)
    rates = DiskCache(tmp_path / "rates")
    rates.put(
        resolved.isoformat(),
        [RateRecord(day252=1, day360=30, rate="14,50")],
        complete=True,
        expected_count=1,
        source="GetList",
    )
    ctx = ToolContext(
        cache=rates,
        settings_factory=lambda: type(
            "Settings", (), {"get": lambda self, key, default=None: ""}
        )(),
        holiday_cache=holiday_cache,
        calendar_service=service,
    )

    payload = curve_handlers.consultar_curva(
        {"data": holiday.isoformat()}, ctx
    )

    assert payload["data_solicitada"] == holiday.isoformat()
    assert payload["data_resolvida"] == resolved.isoformat()
    assert payload["ajustada"] is True
    assert payload["motivo"] == "feriado"
    assert payload["feriado"] == "Feriado de teste"


def test_catalog_contains_holiday_tools():
    from b3_selic_pre.presentation.mcp.catalog import TOOL_NAMES

    assert {
        "feriados_listar",
        "feriados_consultar",
        "feriados_exportar",
    } <= TOOL_NAMES
