"""Testes headless da aba Feriados e do seu controlador."""

from __future__ import annotations

from datetime import date

from b3_selic_pre.application.calendar.ports import YearHolidays
from b3_selic_pre.domain.calendar import Holiday
from b3_selic_pre.infrastructure.calendar.cache import HolidayCache
from b3_selic_pre.presentation.feriados_controller import FeriadosController
from b3_selic_pre.presentation.feriados_view_model import (
    EMPTY_TEXT,
    FeriadosViewModel,
)


class FakeService:
    def __init__(self, cache, state="ok"):
        self.cache = cache
        self.state = state
        self.calls = []

    def ensure_year(self, year, force=False):
        self.calls.append((year, force))
        return self.state


def _year(year, days, source="ANBIMA", published=True):
    return YearHolidays(
        year=year,
        holidays=tuple(Holiday(day, f"Feriado {day.day}") for day in days),
        source=source,
        fetched_at="2026-10-30T12:00:00+00:00",
        published=published,
    )


def test_tree_orders_years_descending_and_months_ascending():
    model = FeriadosViewModel(
        [
            _year(2025, [date(2025, 12, 25)]),
            _year(
                2026,
                [date(2026, 2, 16), date(2026, 1, 1), date(2026, 2, 17)],
            ),
        ]
    )

    years = [row.text for row in model.rows if row.kind == "year"]
    months = [row.text for row in model.rows if row.kind == "month"]
    days = [row.text for row in model.rows if row.kind == "day"]

    assert years == ["2026", "2025"]
    assert months == ["01 - Janeiro", "02 - Fevereiro", "12 - Dezembro"]
    assert days[:3] == ["01 (qui)", "16 (seg)", "17 (ter)"]


def test_day_label_uses_weekday_abbreviation():
    model = FeriadosViewModel([_year(2026, [date(2026, 4, 3)])])
    day = next(row for row in model.rows if row.kind == "day")

    assert day.text == "03 (sex)"


def test_year_text_groups_by_month():
    model = FeriadosViewModel(
        [_year(2026, [date(2026, 1, 1), date(2026, 2, 16)])]
    )

    text = model.text_for("y2026")

    assert "01 - Janeiro" in text
    assert "01 (qui) - Feriado 1" in text
    assert "02 - Fevereiro" in text


def test_month_and_day_texts():
    model = FeriadosViewModel([_year(2026, [date(2026, 4, 3)])])

    assert "03 (sex) - Feriado 3" in model.text_for("y2026m04")
    assert model.text_for("y2026m04d03") == (
        "2026-04-03 (sex) - Feriado 3"
    )


def test_empty_view_model():
    model = FeriadosViewModel([])

    assert model.is_empty
    assert model.rows == ()
    assert model.text_for("missing") == EMPTY_TEXT


def test_controller_loads_only_cache(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [date(2026, 1, 1)]))
    service = FakeService(cache)

    controller = FeriadosController(cache, service, current_year=2026)

    assert controller.model.rows
    assert service.calls == []


def test_refresh_success_rebuilds_and_preserves_selection(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [date(2026, 1, 1)]))
    service = FakeService(cache)
    controller = FeriadosController(cache, service, current_year=2026)
    previous = controller.model

    outcome = controller.refresh((2026,))

    assert outcome.refreshed is True
    assert service.calls == [(2026, True)]
    assert controller.model.contains("y2026m01d01")
    assert outcome.model is not previous


def test_refresh_failure_preserves_previous_content(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [date(2026, 1, 1)]))
    service = FakeService(cache, state="defasado")
    controller = FeriadosController(cache, service, current_year=2026)
    previous = controller.model

    outcome = controller.refresh((2026,))

    assert outcome.refreshed is False
    assert outcome.failed_years == (2026,)
    assert outcome.model is previous


def test_empty_tree_refresh_uses_current_year(tmp_path):
    cache = HolidayCache(tmp_path)
    service = FakeService(cache)
    controller = FeriadosController(cache, service, current_year=2026)

    controller.refresh()

    assert service.calls == [(2026, True)]


def test_empty_year_is_not_shown(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [], published=False))
    service = FakeService(cache)

    controller = FeriadosController(cache, service, current_year=2026)

    assert controller.model.is_empty
