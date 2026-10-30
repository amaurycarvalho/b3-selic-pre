"""Testes de integração do calendário com cargas, TTLs e reservas."""

from __future__ import annotations

from datetime import date
from unittest import mock

from b3_selic_pre.application.calendar.ports import YearHolidays
from b3_selic_pre.application.calendar.service import CalendarService
from b3_selic_pre.application.market.config import (
    MarketConfig,
    ResolutionConfig,
)
from b3_selic_pre.application.reserves.series import incremental_start
from b3_selic_pre.application.use_cases import evolution_dates
from b3_selic_pre.domain.calendar import Holiday, HolidayCalendar
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure import b3_client, cached_client
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache
from b3_selic_pre.infrastructure.market.raw_ttl import ttl_minutes
from b3_selic_pre.infrastructure.tesouro_cache import (
    CURRENT_TTL,
    HISTORICAL_TTL,
    TesouroCache,
    is_current,
    ttl_for,
)
from b3_selic_pre.infrastructure.tesouro_calendar_hook import ensure_calendar
from b3_selic_pre.presentation.market_view_model import artifact_is_stale
from b3_selic_pre.presentation.reserves_view_model import last_business_day


class FakeCalendar:
    def __init__(self, holidays):
        self.holidays = tuple(holidays)

    def calendar_for(self, year):
        return HolidayCalendar(self.holidays)


class FakeRepository:
    def __init__(self, data):
        self.data = {item.year: item for item in data}

    def read(self, year):
        return self.data.get(year)

    def years(self):
        return sorted(self.data)

    def is_fresh(self, year, now=None):
        return year in self.data

    def write(self, data):
        self.data[data.year] = data

    def housekeeping(self, reference_year):
        return None


class FakeSource:
    def fetch_year(self, year):
        raise AssertionError("não deve buscar feriados neste teste")


def _service(holidays):
    return CalendarService(
        FakeSource(),
        FakeRepository([YearHolidays(2026, tuple(holidays))]),
    )


def _records():
    return [RateRecord(day252=1, day360=30, rate="14,50")]


def test_evolution_dates_uses_calendar_service():
    service = _service([Holiday(date(2026, 4, 3), "Sexta-feira Santa")])

    assert evolution_dates("2026-04-06", service) == [
        "2026-03-09",
        "2026-03-16",
        "2026-03-23",
        "2026-03-30",
        "2026-04-06",
    ]


def test_b3_client_never_requests_holiday_target():
    calls = []

    def fake_fetch(date_str, **kwargs):
        calls.append(date_str)
        return _records(), "GetDownloadFile"

    class Targets:
        def evolution_targets(self, base):
            return ["2026-04-01", "2026-04-02"]

    with mock.patch.object(
        b3_client, "fetch_rates_for_date", side_effect=fake_fetch
    ):
        result = b3_client.fetch_historical_rates(
            "2026-04-06", calendar=Targets()
        )

    assert calls == ["2026-04-01", "2026-04-02"]
    assert "2026-04-03" not in result


def test_cached_client_uses_injected_calendar(tmp_path):
    calls = []

    def fake_fetch(date_str, today=None, **kwargs):
        calls.append(date_str)
        return _records(), "GetDownloadFile"

    class Targets:
        def evolution_targets(self, base):
            return ["2026-04-01", "2026-04-02"]

    client = cached_client.CachedB3Client(
        cache_dir=str(tmp_path), calendar=Targets()
    )
    with mock.patch.object(
        cached_client.b3_client, "fetch_rates_for_date", side_effect=fake_fetch
    ):
        client.fetch_historical_rates("2026-04-06", force=True)

    assert calls == ["2026-04-01", "2026-04-02"]


def test_tesouro_cache_uses_holiday_calendar():
    calendar = FakeCalendar([Holiday(date(2026, 4, 3), "Feriado")])
    metadata = {"last_data_date": "2026-04-02"}

    assert is_current(metadata, date(2026, 4, 3), calendar)
    assert ttl_for(metadata, date(2026, 4, 3), "vendas", calendar) == (
        CURRENT_TTL
    )
    assert not is_current(metadata, date(2026, 4, 3))
    assert ttl_for(metadata, date(2026, 4, 3), "vendas") == HISTORICAL_TTL


def test_market_ttl_does_not_reset_on_holiday():
    config = MarketConfig(resolucao=ResolutionConfig(diario_dias=0))
    calendar = FakeCalendar([Holiday(date(2026, 4, 3), "Feriado")])

    assert ttl_minutes(
        config, "2026-04-02", "2026-04-03", calendar
    ) == config.cache.recente_minutos
    assert ttl_minutes(
        config, "2026-04-02", "2026-04-03"
    ) == config.cache.mes_horas * 60


def test_market_missing_dates_ignore_holiday_gap(tmp_path):
    calendar = FakeCalendar([Holiday(date(2026, 4, 3), "Feriado")])
    cache = MarketRawCache(tmp_path, calendar=calendar)

    missing = cache.missing_dates("usd", "2026-04-02", "2026-04-06")

    assert missing == ["2026-04-02", "2026-04-06"]


def test_reserves_overlap_crosses_holiday():
    calendar = FakeCalendar(
        [
            Holiday(date(2026, 1, 1), "Confraternizacao"),
            Holiday(date(2025, 12, 31), "Vespera"),
        ]
    )

    assert incremental_start("2026-01-07", 5, calendar) == "2025-12-29"
    assert incremental_start("2026-01-07", 5) == "2025-12-31"


def test_market_artifact_expected_date_ignores_holiday():
    calendar = FakeCalendar([Holiday(date(2026, 4, 3), "Feriado")])

    assert not artifact_is_stale("2026-04-02", date(2026, 4, 3), calendar)
    assert artifact_is_stale("2026-04-02", date(2026, 4, 3))


def test_reserves_last_business_day_ignores_holiday():
    calendar = FakeCalendar([Holiday(date(2026, 4, 3), "Feriado")])

    assert last_business_day(date(2026, 4, 3), calendar) == date(2026, 4, 2)
    assert last_business_day(date(2026, 4, 3)) == date(2026, 4, 3)


def test_tesouro_calendar_failure_does_not_block_the_load(tmp_path):
    class FailingService:
        def ensure_year(self, year):
            raise RuntimeError("ANBIMA offline")

    cache = TesouroCache(tmp_path, calendar=FailingService())

    ensure_calendar(cache)
