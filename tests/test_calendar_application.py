"""Testes headless do serviço e da configuração do calendário."""

from datetime import date

import pytest

from b3_selic_pre.application.calendar.config import CalendarConfig
from b3_selic_pre.application.calendar.ports import (
    HolidaySourceError,
    HolidayYearUnavailable,
    YearHolidays,
)
from b3_selic_pre.application.calendar.service import (
    ESTADO_DEFASADO,
    ESTADO_INDISPONIVEL,
    ESTADO_OK,
    CalendarService,
)
from b3_selic_pre.domain.calendar import Holiday


class FakeSource:
    def __init__(self, holidays=(), error=None):
        self.holidays = tuple(holidays)
        self.error = error
        self.calls = []

    def fetch_year(self, year):
        self.calls.append(year)
        if self.error is not None:
            raise self.error
        return YearHolidays(
            year=year,
            holidays=self.holidays,
            source_url=f"url/{year}",
            fetched_at="2026-10-30T00:00:00+00:00",
        )


class FakeRepository:
    def __init__(self, data=None, fresh=False):
        self.data = {item.year: item for item in data or ()}
        self.fresh = fresh
        self.written = []
        self.housekeeping_calls = []

    def read(self, year):
        return self.data.get(year)

    def years(self):
        return sorted(self.data)

    def is_fresh(self, year, now=None):
        return self.fresh and year in self.data

    def write(self, data):
        self.written.append(data)
        self.data[data.year] = data

    def housekeeping(self, reference_year):
        self.housekeeping_calls.append(reference_year)


def _holiday(day, name="Feriado"):
    return Holiday(day, name)


def test_ensure_year_uses_fresh_cache_without_source():
    cached = YearHolidays(2026, (_holiday(date(2026, 1, 1)),))
    repository = FakeRepository([cached], fresh=True)
    source = FakeSource()
    service = CalendarService(source, repository)

    assert service.ensure_year(2026) == ESTADO_OK
    assert source.calls == []


def test_ensure_year_fetches_and_writes_when_stale():
    repository = FakeRepository()
    source = FakeSource((_holiday(date(2026, 1, 1)),))
    service = CalendarService(source, repository)

    assert service.ensure_year(2026) == ESTADO_OK
    assert source.calls == [2026]
    assert repository.written[0].year == 2026
    assert repository.housekeeping_calls == [2026]


def test_ensure_year_falls_back_to_previous_cache():
    cached = YearHolidays(2026, (_holiday(date(2026, 1, 1)),))
    repository = FakeRepository([cached])
    service = CalendarService(
        FakeSource(error=HolidaySourceError("offline")), repository
    )

    assert service.ensure_year(2026) == ESTADO_DEFASADO
    resolution = service.resolve_business_day("2026-01-01")
    assert resolution.calendario_estado == ESTADO_DEFASADO


def test_ensure_year_without_cache_is_degraded():
    service = CalendarService(
        FakeSource(error=HolidaySourceError("offline")), FakeRepository()
    )

    assert service.ensure_year(2026) == ESTADO_INDISPONIVEL
    resolution = service.resolve_business_day("2026-01-01")
    assert resolution.calendario_estado == ESTADO_INDISPONIVEL
    assert resolution.data_resolvida == "2026-01-01"


def test_future_year_unavailable_writes_negative_cache():
    repository = FakeRepository()
    service = CalendarService(
        FakeSource(error=HolidayYearUnavailable("404")), repository
    )

    assert service.ensure_year(2099) == ESTADO_INDISPONIVEL
    assert repository.written[0].published is False


def test_resolve_weekend_reports_motive():
    service = CalendarService(FakeSource(), FakeRepository())
    resolution = service.resolve_business_day("2026-06-14")

    assert resolution.data_resolvida == "2026-06-12"
    assert resolution.ajustada is True
    assert resolution.motivo == "fim_de_semana"
    assert resolution.feriado is None


def test_resolve_holiday_reports_name():
    repository = FakeRepository(
        [YearHolidays(2026, (_holiday(date(2026, 4, 3), "Sexta-feira Santa"),))]
    )
    service = CalendarService(FakeSource(), repository)
    resolution = service.resolve_business_day("2026-04-03")

    assert resolution.data_resolvida == "2026-04-02"
    assert resolution.motivo == "feriado"
    assert resolution.feriado == "Sexta-feira Santa"


def test_resolve_preserves_business_day():
    service = CalendarService(FakeSource(), FakeRepository())
    resolution = service.resolve_business_day("2026-06-15")

    assert resolution.data_resolvida == "2026-06-15"
    assert resolution.ajustada is False
    assert resolution.motivo is None


def test_evolution_targets_resolves_and_deduplicates():
    repository = FakeRepository(
        [YearHolidays(2026, (_holiday(date(2026, 6, 12), "Feriado"),))]
    )
    service = CalendarService(FakeSource(), repository)
    targets = service.evolution_targets("2026-06-17")

    assert targets == [
        "2026-05-20",
        "2026-05-27",
        "2026-06-03",
        "2026-06-10",
        "2026-06-17",
    ]


def test_evolution_targets_collapse_duplicates():
    repository = FakeRepository(
        [
            YearHolidays(
                2026,
                (
                    _holiday(date(2026, 5, 20), "Feriado"),
                    _holiday(date(2026, 5, 27), "Feriado"),
                ),
            )
        ]
    )
    service = CalendarService(FakeSource(), repository)
    targets = service.evolution_targets("2026-06-17")

    assert targets == [
        "2026-05-19",
        "2026-05-26",
        "2026-06-03",
        "2026-06-10",
        "2026-06-17",
    ]


def test_config_defaults_and_override():
    defaults = CalendarConfig.from_mapping(None)
    assert defaults.ttl_corrente_segundos == 86400
    assert defaults.retencao_anos == 3
    assert defaults.sobreposicao_dias == 5

    custom = CalendarConfig.from_mapping(
        {
            "ttl_corrente_segundos": 60,
            "retencao_anos": 2,
            "sobreposicao_dias": 7,
        }
    )
    assert custom.ttl_corrente_segundos == 60
    assert custom.retencao_anos == 2
    assert custom.sobreposicao_dias == 7


def test_housekeeping_failure_does_not_block_ensure():
    class BrokenRepository(FakeRepository):
        def housekeeping(self, reference_year):
            raise OSError("disco")

    repository = BrokenRepository()
    service = CalendarService(FakeSource(), repository)

    assert service.ensure_year(2026) == ESTADO_OK


def test_force_ignores_fresh_cache():
    cached = YearHolidays(2026, (_holiday(date(2026, 1, 1)),))
    repository = FakeRepository([cached], fresh=True)
    source = FakeSource((_holiday(date(2026, 1, 2)),))
    service = CalendarService(source, repository)

    assert service.ensure_year(2026, force=True) == ESTADO_OK
    assert source.calls == [2026]


@pytest.mark.parametrize("value", ["2026-02-30", "invalida"])
def test_resolve_rejects_invalid_date(value):
    service = CalendarService(FakeSource(), FakeRepository())
    with pytest.raises(ValueError):
        service.resolve_business_day(value)


def test_state_of_resolved_previous_year_is_combined():
    repository = FakeRepository(
        [
            YearHolidays(
                2025, (_holiday(date(2025, 12, 31), "Vespera"),)
            ),
            YearHolidays(
                2026, (_holiday(date(2026, 1, 1), "Confraternizacao"),)
            ),
        ]
    )
    service = CalendarService(FakeSource(), repository)
    resolution = service.resolve_business_day("2026-01-01")

    assert resolution.data_resolvida == "2025-12-30"
    assert resolution.motivo == "feriado"
