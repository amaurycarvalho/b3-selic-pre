"""Serviço de garantia do calendário e resolução de dias úteis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from b3_selic_pre.application.calendar.config import CalendarConfig
from b3_selic_pre.application.calendar.ports import (
    HolidayRepository,
    HolidaySource,
    HolidayYearUnavailable,
    YearHolidays,
)
from b3_selic_pre.application.use_cases import days_ago
from b3_selic_pre.domain.calendar import HolidayCalendar
from b3_selic_pre.domain.constants import EVOLUTION_DAYS

ESTADO_OK = "ok"
ESTADO_DEFASADO = "defasado"
ESTADO_INDISPONIVEL = "indisponivel"


@dataclass(frozen=True)
class BusinessDayResolution:
    """Resultado estruturado da resolução de uma data."""

    data_solicitada: str
    data_resolvida: str
    ajustada: bool
    motivo: str | None
    feriado: str | None
    calendario_estado: str

    def as_dict(self: BusinessDayResolution) -> dict[str, object]:
        """Serialize the resolution for payloads."""
        return {
            "data_solicitada": self.data_solicitada,
            "data_resolvida": self.data_resolvida,
            "ajustada": self.ajustada,
            "motivo": self.motivo,
            "feriado": self.feriado,
            "calendario_estado": self.calendario_estado,
        }


def _today() -> date:
    return datetime.now(UTC).date()


class CalendarService:
    """Garante o calendário por ano e resolve datas não úteis."""

    def __init__(
        self: CalendarService,
        source: HolidaySource,
        repository: HolidayRepository,
        config: CalendarConfig | None = None,
    ) -> None:
        """Store the injected source, repository and configuration."""
        self.source = source
        self.repository = repository
        self.config = config or CalendarConfig()
        self._years: dict[int, YearHolidays | None] = {}
        self._states: dict[int, str] = {}

    def ensure_year(
        self: CalendarService, year: int, force: bool = False
    ) -> str:
        """Ensure the calendar of ``year`` using cache, source and fallback."""
        if not force and self.repository.is_fresh(year):
            return self._load_cached(year)
        try:
            data = self.source.fetch_year(year)
        except HolidayYearUnavailable:
            return self._handle_unavailable(year)
        except Exception:
            return self._handle_failure(year)
        self.repository.write(data)
        self._years[year] = data
        self._states[year] = ESTADO_OK
        try:
            self.repository.housekeeping(year)
        except Exception:
            pass
        return ESTADO_OK

    def _load_cached(self: CalendarService, year: int) -> str:
        data = self.repository.read(year)
        if data is None:
            self._years[year] = None
            self._states[year] = ESTADO_INDISPONIVEL
            return ESTADO_INDISPONIVEL
        self._years[year] = data
        self._states[year] = ESTADO_OK
        return ESTADO_OK

    def _handle_unavailable(self: CalendarService, year: int) -> str:
        if year > _today().year:
            marker = YearHolidays(
                year=year,
                holidays=(),
                published=False,
                fetched_at=datetime.now(UTC).isoformat(timespec="seconds"),
                ttl_seconds=self.config.ttl_negativo_segundos,
            )
            try:
                self.repository.write(marker)
            except Exception:
                pass
            self._years[year] = marker
            self._states[year] = ESTADO_INDISPONIVEL
            return ESTADO_INDISPONIVEL
        return self._handle_failure(year)

    def _handle_failure(self: CalendarService, year: int) -> str:
        previous = self.repository.read(year)
        if previous is not None and previous.published:
            self._years[year] = previous
            self._states[year] = ESTADO_DEFASADO
            return ESTADO_DEFASADO
        self._years[year] = None
        self._states[year] = ESTADO_INDISPONIVEL
        return ESTADO_INDISPONIVEL

    def _data(self: CalendarService, year: int) -> YearHolidays | None:
        if year in self._years:
            return self._years[year]
        data = self.repository.read(year)
        self._years[year] = data
        self._states.setdefault(
            year,
            ESTADO_OK if data is not None else ESTADO_INDISPONIVEL,
        )
        return data

    def _state_for(self: CalendarService, year: int) -> str:
        self._data(year)
        return self._states.get(year, ESTADO_INDISPONIVEL)

    def _calendar(self: CalendarService, year: int) -> HolidayCalendar:
        holidays = []
        for candidate in (year - 1, year, year + 1):
            data = self._data(candidate)
            if data is not None and data.published:
                holidays.extend(data.holidays)
        return HolidayCalendar(holidays=tuple(holidays))

    def calendar_for(self: CalendarService, year: int) -> HolidayCalendar:
        """Return the combined calendar around ``year`` without network."""
        return self._calendar(year)

    def resolve_business_day(
        self: CalendarService, date_str: str
    ) -> BusinessDayResolution:
        """Resolve ``date_str`` to the previous business day when needed."""
        requested = date.fromisoformat(date_str)
        calendar = self._calendar(requested.year)
        if calendar.is_business_day(requested):
            return BusinessDayResolution(
                data_solicitada=date_str,
                data_resolvida=date_str,
                ajustada=False,
                motivo=None,
                feriado=None,
                calendario_estado=self._state_for(requested.year),
            )
        motivo = (
            "fim_de_semana"
            if requested.weekday() in calendar.weekend
            else "feriado"
        )
        holiday = calendar.holiday_on(requested)
        resolved = calendar.previous_business_day(requested)
        return BusinessDayResolution(
            data_solicitada=date_str,
            data_resolvida=resolved.isoformat(),
            ajustada=True,
            motivo=motivo,
            feriado=holiday.name if holiday is not None else None,
            calendario_estado=self._state_for(requested.year),
        )

    def evolution_targets(
        self: CalendarService, base_date: str
    ) -> list[str]:
        """Resolve each evolution target and deduplicate by date."""
        targets: list[str] = []
        for offset in EVOLUTION_DAYS:
            target = days_ago(base_date, offset)
            resolved = self.resolve_business_day(target).data_resolvida
            if resolved not in targets:
                targets.append(resolved)
        return targets


__all__ = [
    "ESTADO_DEFASADO",
    "ESTADO_INDISPONIVEL",
    "ESTADO_OK",
    "BusinessDayResolution",
    "CalendarService",
]
