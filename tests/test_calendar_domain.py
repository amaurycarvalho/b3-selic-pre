"""Testes do calendário puro de dias úteis."""

from datetime import date

from b3_selic_pre.domain.calendar import Holiday, HolidayCalendar


def _calendar(*days: tuple[date, str]) -> HolidayCalendar:
    return HolidayCalendar(tuple(Holiday(day, name) for day, name in days))


def test_business_day_is_preserved():
    calendar = _calendar()
    assert calendar.is_business_day(date(2026, 6, 15))
    assert calendar.previous_business_day(date(2026, 6, 15)) == date(
        2026, 6, 15
    )


def test_saturday_and_sunday_retreat_to_friday():
    calendar = _calendar()
    assert not calendar.is_business_day(date(2026, 6, 13))
    assert not calendar.is_business_day(date(2026, 6, 14))
    assert calendar.previous_business_day(date(2026, 6, 13)) == date(
        2026, 6, 12
    )
    assert calendar.previous_business_day(date(2026, 6, 14)) == date(
        2026, 6, 12
    )


def test_holiday_retreats_to_previous_business_day():
    calendar = _calendar((date(2026, 1, 1), "Confraternizacao Universal"))
    assert not calendar.is_business_day(date(2026, 1, 1))
    assert calendar.previous_business_day(date(2026, 1, 1)) == date(
        2025, 12, 31
    )


def test_consecutive_holiday_block_is_crossed():
    calendar = _calendar(
        (date(2026, 2, 16), "Carnaval"),
        (date(2026, 2, 17), "Carnaval"),
    )
    assert calendar.previous_business_day(date(2026, 2, 17)) == date(
        2026, 2, 13
    )


def test_year_boundary_uses_previous_year_holiday():
    calendar = _calendar(
        (date(2025, 12, 31), "Vespera de Ano-Novo"),
        (date(2026, 1, 1), "Confraternizacao Universal"),
    )
    assert calendar.previous_business_day(date(2026, 1, 1)) == date(
        2025, 12, 30
    )


def test_next_business_day_skips_weekend_and_holiday():
    calendar = _calendar((date(2026, 2, 16), "Carnaval"))
    assert calendar.next_business_day(date(2026, 2, 14)) == date(
        2026, 2, 17
    )


def test_business_days_between_is_inclusive():
    calendar = _calendar((date(2026, 2, 16), "Carnaval"))
    assert calendar.business_days_between(
        date(2026, 2, 13), date(2026, 2, 18)
    ) == 3
    assert calendar.business_days_between(
        date(2026, 2, 18), date(2026, 2, 13)
    ) == 0
