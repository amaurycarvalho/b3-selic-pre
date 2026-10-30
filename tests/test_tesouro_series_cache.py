import json
import threading
from decimal import Decimal

from b3_selic_pre.application.tesouro import (
    DIMENSAO_FAMILIA,
    METRICA_DEMANDA_PCT,
    SELIC,
    SeriesPoint,
    SeriesSourceSnapshot,
)
from b3_selic_pre.infrastructure.tesouro_analytics_cache import (
    TesouroAnalyticsCache,
)
from b3_selic_pre.infrastructure.tesouro_series_cache import (
    SERIES_SCHEMA_VERSION,
    TesouroSeriesCache,
    composite_hash,
    source_hashes,
)


def _snapshot(name="demanda", period="2026-10-02"):
    return SeriesSourceSnapshot(
        name,
        (
            SeriesPoint(
                period,
                METRICA_DEMANDA_PCT,
                Decimal("60.0"),
                Decimal("100"),
                DIMENSAO_FAMILIA,
                SELIC,
            ),
        ),
        period,
        ("Tesouro Selic 2029",),
    )


def _cache(tmp_path):
    return TesouroSeriesCache(
        TesouroAnalyticsCache(tmp_path / "analytics"),
        raw_dir=tmp_path / "raw",
        lock_path=tmp_path / "locks" / "analytics.lock",
    )


def _write_raw(tmp_path, name="vendastesourodireto.csv", content="data"):
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / name).write_text(content, encoding="utf-8")


def test_write_and_read_round_trip_keeps_decimal(tmp_path):
    _write_raw(tmp_path)
    cache = _cache(tmp_path)
    hashes = cache.expected_hashes("demanda")
    assert hashes is not None

    cache.write(
        _snapshot(),
        source="Cache",
        extracted_at="2026-10-20T00:00:00+00:00",
        expected_hashes=hashes,
    )
    stored = cache.read("demanda", hashes)

    assert stored is not None
    assert stored.points[0].value == Decimal("60.0")
    assert stored.latest_data_date == "2026-10-02"
    assert stored.titles == ("Tesouro Selic 2029",)
    assert stored.source == "Cache"


def test_hash_change_is_a_miss_and_keeps_files(tmp_path):
    _write_raw(tmp_path, content="old")
    cache = _cache(tmp_path)
    old_hashes = cache.expected_hashes("demanda")
    assert old_hashes is not None
    cache.write(
        _snapshot(),
        source="Cache",
        extracted_at=None,
        expected_hashes=old_hashes,
    )

    _write_raw(tmp_path, content="new")
    new_hashes = cache.expected_hashes("demanda")

    assert new_hashes != old_hashes
    assert cache.read("demanda", new_hashes) is None
    assert cache.cache.partition_path("series/demanda").exists()


def test_missing_raw_source_skips_precompute(tmp_path):
    cache = _cache(tmp_path)

    assert cache.expected_hashes("demanda") is None
    assert (
        cache.update_if_changed(
            "demanda",
            None,
            lambda: _snapshot(),
            source="Cache",
            extracted_at=None,
        )
        is False
    )


def test_source_hash_ignores_metadata_changes(tmp_path):
    _write_raw(tmp_path, content="same")
    metadata = tmp_path / "raw" / "metadata.json"
    metadata.write_text("{}", encoding="utf-8")
    first = source_hashes(tmp_path / "raw", ("vendas",))
    metadata.write_text(
        '{"checked_at": "2026-10-30T12:00:00+00:00"}',
        encoding="utf-8",
    )
    second = source_hashes(tmp_path / "raw", ("vendas",))

    assert first == second
    assert composite_hash(first or {}) == composite_hash(second or {})


def test_corrupt_and_old_schema_are_misses(tmp_path):
    _write_raw(tmp_path)
    cache = _cache(tmp_path)
    hashes = cache.expected_hashes("demanda")
    assert hashes is not None
    cache.write(
        _snapshot(),
        source="Cache",
        extracted_at=None,
        expected_hashes=hashes,
    )
    path = cache.cache.partition_path("series/demanda")

    path.write_text("{", encoding="utf-8")
    assert cache.read("demanda", hashes) is None
    assert path.exists()

    payload = {
        "schema_version": SERIES_SCHEMA_VERSION - 1,
        "name": "demanda",
        "source_hashes": hashes,
        "points": [],
        "titles": [],
        "latest_data_date": "2026-10-02",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert cache.read("demanda", hashes) is None
    assert path.exists()


def test_update_if_changed_skips_identical_content(tmp_path):
    _write_raw(tmp_path)
    cache = _cache(tmp_path)
    calls = []

    def build():
        calls.append("build")
        return _snapshot()

    hashes = cache.expected_hashes("demanda")
    assert hashes is not None

    assert cache.update_if_changed(
        "demanda", hashes, build, source="Cache", extracted_at=None
    )
    assert cache.update_if_changed(
        "demanda", hashes, build, source="Cache", extracted_at=None
    ) is False
    assert calls == ["build"]


def test_concurrent_update_builds_once(tmp_path):
    _write_raw(tmp_path)
    cache = _cache(tmp_path)
    hashes = cache.expected_hashes("demanda")
    assert hashes is not None
    calls = []
    lock = threading.Lock()

    def build():
        with lock:
            calls.append("build")
        return _snapshot()

    def worker():
        cache.update_if_changed(
            "demanda", hashes, build, source="Cache", extracted_at=None
        )

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls == ["build"]


def test_housekeeping_does_not_remove_snapshots(tmp_path):
    _write_raw(tmp_path)
    cache = _cache(tmp_path)
    hashes = cache.expected_hashes("demanda")
    assert hashes is not None
    cache.write(
        _snapshot(),
        source="Cache",
        extracted_at=None,
        expected_hashes=hashes,
    )

    removed = cache.cache.housekeeping("2026-10")

    assert removed == []
    assert cache.read("demanda", hashes) is not None
