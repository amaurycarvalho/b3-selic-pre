"""Testes do subcomando ``feriados`` da CLI."""

from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from b3_selic_pre.application.calendar.ports import YearHolidays
from b3_selic_pre.application.calendar.service import CalendarService
from b3_selic_pre.domain.calendar import Holiday
from b3_selic_pre.infrastructure.calendar.cache import HolidayCache
from b3_selic_pre.presentation.cli_feriados import feriados


class FakeSource:
    def __init__(self, holidays):
        self.holidays = holidays
        self.calls = []

    def fetch_year(self, year):
        self.calls.append(year)
        return YearHolidays(
            year=year,
            holidays=tuple(self.holidays),
            source_url=f"url/{year}",
            fetched_at="2026-10-30T12:00:00+00:00",
        )


def _args(**overrides):
    values = {
        "ano": 2026,
        "data": None,
        "formato": "csv",
        "saida": None,
        "atualizar": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def _holidays():
    return (
        Holiday(date(2026, 1, 1), "Confraternizacao Universal"),
        Holiday(date(2026, 4, 3), "Sexta-feira Santa"),
    )


def _run(args, cache, service):
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = feriados(args, cache, service)
    return code, stdout.getvalue()


def test_listing_reads_cache(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)
    service.ensure_year(2026)

    code, output = _run(_args(), cache, service)

    assert code == 0
    assert "DATA;DIA_SEMANA;NOME;ORIGEM" in output
    assert "2026-04-03;sex;Sexta-feira Santa;ANBIMA" in output


def test_listing_json(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)
    service.ensure_year(2026)

    code, output = _run(_args(formato="json"), cache, service)

    assert code == 0
    assert '"ano": 2026' in output
    assert '"feriados"' in output


def test_query_holiday(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)
    service.ensure_year(2026)

    code, output = _run(_args(ano=None, data="2026-04-03"), cache, service)

    assert code == 0
    assert "Dia útil: não" in output
    assert "Data ajustada de 2026-04-03 para 2026-04-02" in output


def test_query_business_day(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)
    service.ensure_year(2026)

    code, output = _run(_args(ano=None, data="2026-04-06"), cache, service)

    assert code == 0
    assert "Dia útil: sim" in output


def test_export_to_file(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)
    service.ensure_year(2026)
    target = tmp_path / "feriados.csv"

    code, output = _run(_args(saida=str(target)), cache, service)

    assert code == 0
    assert output == ""
    assert target.read_text(encoding="utf-8").startswith("DATA;")


def test_export_to_directory(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)
    service.ensure_year(2026)
    target = tmp_path / "saida"
    target.mkdir()

    code, output = _run(_args(saida=str(target)), cache, service)

    assert code == 0
    assert output == ""
    assert (target / "feriados-2026.csv").exists()


def test_year_without_cache_returns_one(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)

    code, output = _run(_args(), cache, service)

    assert code == 1
    assert output == ""


def test_update_before_listing(tmp_path):
    cache = HolidayCache(tmp_path)
    source = FakeSource(_holidays())
    service = CalendarService(source, cache)

    code, output = _run(_args(atualizar=True), cache, service)

    assert code == 0
    assert source.calls == [2026]
    assert "2026-01-01" in output


def test_ano_and_data_are_mutually_exclusive(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)

    code, _ = _run(_args(data="2026-04-03"), cache, service)

    assert code == 2


def test_invalid_data_is_rejected(tmp_path):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)

    code, _ = _run(_args(ano=None, data="03/04/2026"), cache, service)

    assert code == 2


def test_default_year_is_current(tmp_path):
    cache = HolidayCache(tmp_path)
    source = FakeSource(_holidays())
    service = CalendarService(source, cache)

    code, _ = _run(_args(ano=None, atualizar=True), cache, service)

    assert code == 0
    assert source.calls[0] > 2000


def test_missing_year_hint_is_written_to_stderr(tmp_path, capsys):
    cache = HolidayCache(tmp_path)
    service = CalendarService(FakeSource(_holidays()), cache)

    with redirect_stdout(io.StringIO()):
        code = feriados(_args(), cache, service)

    stderr = capsys.readouterr().err
    assert code == 1
    assert "--atualizar" in stderr
