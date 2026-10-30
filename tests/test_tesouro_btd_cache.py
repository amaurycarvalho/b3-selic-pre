import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from b3_selic_pre.domain.models import EstoqueMensalTitulo
from b3_selic_pre.infrastructure.tesouro_btd_cache import (
    CACHE_FILENAME,
    SCHEMA_VERSION,
    TTL,
    TesouroBtdCache,
)


def _records():
    return (
        EstoqueMensalTitulo(
            "Tesouro Selic 2029", "2026-09", Decimal("120000000")
        ),
    )


def _metadata(checked_at="2026-10-30T12:00:00+00:00"):
    return {
        "reference_month": "2026-09",
        "published_at": "2026-10-29",
        "page_url": "https://example.test/btd/2026/9",
        "attachment_url": "https://example.test/anexo/1",
        "sha256": "abc",
        "size_bytes": 10,
        "checked_at": checked_at,
    }


def test_round_trip_keeps_decimals_and_metadata(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    cache.save(_records(), _metadata())

    entry = cache.read()

    assert entry is not None
    assert entry.records == _records()
    assert entry.metadata["reference_month"] == "2026-09"
    assert entry.metadata["sha256"] == "abc"


def test_ttl_is_24_hours(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    checked = datetime(2026, 10, 30, 12, tzinfo=UTC)

    assert TTL == timedelta(hours=24)
    assert cache.is_fresh(_metadata(), checked + timedelta(hours=23))
    assert not cache.is_fresh(_metadata(), checked + timedelta(hours=24))


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    cache.save(_records(), _metadata())

    payload = json.loads(cache.path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["records"][0]["mes"] == "2026-09"
    assert list(tmp_path.glob(".estoque-btd*")) == []


def test_read_only_does_not_modify_the_cache(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    cache.save(_records(), _metadata())
    before = cache.path.read_bytes()

    cache.read()
    cache.read()

    assert cache.path.read_bytes() == before


def test_corrupt_cache_is_ignored_but_preserved(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    cache.path.write_text("{", encoding="utf-8")

    assert cache.read() is None
    assert cache.path.exists()


def test_cache_with_wrong_schema_is_ignored(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    cache.path.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION - 1,
                "reference_month": "2026-09",
                "checked_at": "2026-10-30T12:00:00+00:00",
                "records": [],
            }
        ),
        encoding="utf-8",
    )

    assert cache.read() is None


def test_cache_without_records_is_ignored(tmp_path):
    cache = TesouroBtdCache(tmp_path)
    payload = _metadata()
    payload.update({"schema_version": SCHEMA_VERSION, "records": []})
    cache.path.write_text(json.dumps(payload), encoding="utf-8")

    assert cache.read() is None


def test_default_filename(tmp_path):
    assert TesouroBtdCache(tmp_path).path.name == CACHE_FILENAME
