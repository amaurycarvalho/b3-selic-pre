"""Testes da fonte ANBIMA, do cache e do housekeeping de feriados."""

from __future__ import annotations

import json
import threading
import urllib.error
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from b3_selic_pre.application.calendar.config import CalendarConfig
from b3_selic_pre.application.calendar.ports import (
    HolidaySourceError,
    HolidayYearUnavailable,
    YearHolidays,
)
from b3_selic_pre.domain.calendar import Holiday
from b3_selic_pre.infrastructure.calendar.cache import HolidayCache
from b3_selic_pre.infrastructure.calendar.housekeeping import run_housekeeping
from b3_selic_pre.infrastructure.calendar.source import (
    AnbimaHolidaySource,
    normalize_text,
    source_url,
)


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def _page(rows):
    body = "".join(
        f"<tr><td>{day}</td><td>{weekday}</td><td>{name}</td></tr>"
        for day, weekday, name in rows
    )
    return f"<html><table><tr><td>Data</td><td>Dia</td><td>Feriado</td></tr>{body}</table></html>".encode("iso-8859-1")


FIXTURES = {
    2024: [
        ("1/1/24", "Segunda-feira", "Confraternização Universal"),
        ("12/2/24", "Segunda-feira", "Carnaval"),
        ("13/2/24", "Terça-feira", "Carnaval"),
        ("15/11/24", "Sexta-feira", "Proclamação da República"),
        ("25/12/24", "Quarta-feira", "Natal"),
    ],
    2025: [
        ("1/1/25", "Quarta-feira", "Confraternização Universal"),
        ("3/3/25", "Segunda-feira", "Carnaval"),
        ("4/3/25", "Terça-feira", "Carnaval"),
        ("18/4/25", "Sexta-feira", "Paixão de Cristo"),
        ("25/12/25", "Quinta-feira", "Natal"),
    ],
    2026: [
        ("1/1/26", "Quinta-feira", "Confraternização Universal"),
        ("16/2/26", "Segunda-feira", "Carnaval"),
        ("17/2/26", "Terça-feira", "Carnaval"),
        ("3/4/26", "Sexta-feira", "Sexta-feira Santa"),
        ("25/12/26", "Sexta-feira", "Natal"),
    ],
}


def _source(year, rows=None):
    body = _page(rows if rows is not None else FIXTURES[year])
    return AnbimaHolidaySource(opener=lambda *a, **k: FakeResponse(body))


def test_source_url_contains_year():
    assert source_url(2026).endswith("/feriados/fer_nacionais/2026.asp")


def test_normalize_text_removes_accents_entities_and_tags():
    assert normalize_text("<b>Confraterniza&ccedil;&atilde;o</b>") == (
        "Confraternizacao"
    )


@pytest.mark.parametrize("year", [2024, 2025, 2026])
def test_source_normalizes_fixture(year):
    data = _source(year).fetch_year(year)

    assert data.year == year
    assert data.source == "ANBIMA"
    assert data.source_url.endswith(f"{year}.asp")
    assert data.fetched_at
    assert all(holiday.date.year == year for holiday in data.holidays)


def test_source_normalizes_short_date():
    data = _source(2026, [("1/1/26", "Quinta-feira", "Confraternização")]).fetch_year(2026)
    assert data.holidays[0].date == date(2026, 1, 1)


def test_source_adds_b3_recess_complement():
    data = _source(2026).fetch_year(2026)
    names = {holiday.date: holiday.name for holiday in data.holidays}
    assert names[date(2026, 12, 24)] == "Vespera de Natal"
    assert names[date(2026, 12, 31)] == "Vespera de Ano-Novo"


def test_source_rejects_weekday_divergence():
    with pytest.raises(HolidaySourceError):
        _source(2026, [("1/1/26", "Segunda-feira", "Errado")]).fetch_year(2026)


def test_source_rejects_unexpected_page():
    with pytest.raises(HolidaySourceError):
        AnbimaHolidaySource(
            opener=lambda *a, **k: FakeResponse(b"sem tabela")
        ).fetch_year(2026)


def test_source_rejects_invalid_html():
    with pytest.raises(HolidaySourceError):
        _source(2026, [("invalida", "Quinta-feira", "X")]).fetch_year(2026)


def test_source_classifies_404_as_unavailable():
    def _raise(*args, **kwargs):
        raise urllib.error.HTTPError("url", 404, "not found", {}, None)

    with pytest.raises(HolidayYearUnavailable):
        AnbimaHolidaySource(opener=_raise).fetch_year(2099)


def test_source_classifies_timeout_as_source_failure():
    def _raise(*args, **kwargs):
        raise TimeoutError("timed out")

    with pytest.raises(HolidaySourceError):
        AnbimaHolidaySource(opener=_raise).fetch_year(2026)


def _set_fetched_at(cache, year, value):
    path = cache.path(year)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["fetched_at"] = value
    path.write_text(json.dumps(data), encoding="utf-8")


def _year(year, days, published=True):
    return YearHolidays(
        year=year,
        holidays=tuple(Holiday(day, "Feriado") for day in days),
        fetched_at=datetime.now(UTC).isoformat(timespec="seconds"),
        published=published,
    )


def test_cache_roundtrip_and_read_only(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [date(2026, 1, 1)]))

    data = cache.read(2026)
    assert data is not None
    assert data.holidays[0].date == date(2026, 1, 1)
    assert cache.years() == [2026]
    assert (tmp_path / "holidays" / "2026.json").exists()


def test_cache_ignores_corrupted_file(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.holidays_dir.mkdir(parents=True)
    (cache.holidays_dir / "2026.json").write_text("{invalido", encoding="utf-8")

    assert cache.read(2026) is None
    assert cache.years() == []


def test_fresh_cache_and_expired_current_year(tmp_path):
    cache = HolidayCache(tmp_path, CalendarConfig(ttl_corrente_segundos=3600))
    cache.write(_year(2026, [date(2026, 1, 1)]))
    _set_fetched_at(cache, 2026, "2026-10-30T12:00:00+00:00")
    now = datetime(2026, 10, 30, 12, tzinfo=UTC)

    assert cache.is_fresh(2026, now) is True
    assert cache.is_fresh(2026, now + timedelta(hours=2)) is False


def test_past_year_is_immutable(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2025, [date(2025, 1, 1)]))

    assert cache.is_fresh(2025, datetime(2027, 1, 1, tzinfo=UTC)) is True


def test_negative_cache_uses_short_ttl(tmp_path):
    cache = HolidayCache(tmp_path, CalendarConfig(ttl_negativo_segundos=60))
    cache.write(_year(2099, [], published=False))
    _set_fetched_at(cache, 2099, "2026-10-30T12:00:00+00:00")
    now = datetime(2026, 10, 30, 12, tzinfo=UTC)

    assert cache.is_fresh(2099, now) is True
    assert cache.is_fresh(2099, now + timedelta(minutes=2)) is False


def test_concurrent_writes_leave_valid_file(tmp_path):
    cache = HolidayCache(tmp_path)
    errors = []

    def _write(day):
        try:
            cache.write(_year(2026, [date(2026, 1, day)]))
        except Exception as exc:  # pragma: no cover - surfaced by the assert
            errors.append(exc)

    threads = [
        threading.Thread(target=_write, args=(day,)) for day in range(1, 6)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    data = cache.read(2026)
    assert data is not None
    assert len(data.holidays) == 1


def test_housekeeping_removes_old_and_keeps_window(tmp_path):
    holidays_dir = tmp_path / "holidays"
    holidays_dir.mkdir()
    for year in (2021, 2023, 2024, 2025, 2026, 2027, 2029):
        (holidays_dir / f"{year}.json").write_text(
            json.dumps({"schema_version": 1, "year": year}),
            encoding="utf-8",
        )

    removed = run_housekeeping(holidays_dir, 2026)

    assert removed == [2021, 2029]
    assert sorted(path.stem for path in holidays_dir.glob("*.json")) == [
        "2023",
        "2024",
        "2025",
        "2026",
        "2027",
    ]


def test_housekeeping_ignores_corrupted_file(tmp_path):
    holidays_dir = tmp_path / "holidays"
    holidays_dir.mkdir()
    (holidays_dir / "2021.json").write_text("{invalido", encoding="utf-8")

    assert run_housekeeping(holidays_dir, 2026) == []
    assert (holidays_dir / "2021.json").exists()


def test_housekeeping_without_directory_is_noop(tmp_path):
    assert run_housekeeping(tmp_path / "missing", 2026) == []
