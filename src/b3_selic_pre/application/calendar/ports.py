"""Portas e modelos da camada de aplicação para o calendário."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from b3_selic_pre.domain.calendar import Holiday, HolidayCalendar


class HolidaySourceError(RuntimeError):
    """Falha ao obter o calendário de feriados da fonte."""


class HolidayYearUnavailable(HolidaySourceError):
    """O ano ainda não foi publicado pela fonte."""


@dataclass(frozen=True)
class YearHolidays:
    """Feriados de um ano com os metadados de origem."""

    year: int
    holidays: tuple[Holiday, ...]
    source: str = "ANBIMA"
    source_url: str = ""
    fetched_at: str = ""
    ttl_seconds: int | None = None
    published: bool = True
    stale: bool = False

    def to_calendar(self: YearHolidays) -> HolidayCalendar:
        """Return a pure calendar with this year's holidays."""
        return HolidayCalendar(holidays=self.holidays)


class HolidaySource(Protocol):
    """Fonte externa de feriados por ano."""

    def fetch_year(self: HolidaySource, year: int) -> YearHolidays:
        """Fetch the holidays of ``year`` or raise a source error."""


class HolidayRepository(Protocol):
    """Repositório local de feriados por ano."""

    def read(self: HolidayRepository, year: int) -> YearHolidays | None:
        """Read one year without modifying anything."""

    def years(self: HolidayRepository) -> list[int]:
        """Return the years available in the cache."""

    def is_fresh(
        self: HolidayRepository,
        year: int,
        now: datetime | None = None,
    ) -> bool:
        """Return whether the cached year is inside its TTL."""

    def write(self: HolidayRepository, data: YearHolidays) -> None:
        """Write one year atomically under the dedicated lock."""

    def housekeeping(self: HolidayRepository, reference_year: int) -> None:
        """Remove cached years outside the retention window."""
