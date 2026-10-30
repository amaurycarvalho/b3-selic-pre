import threading

from b3_selic_pre.infrastructure.tesouro_analytics_cache import (
    MANIFEST_NAME,
    TesouroAnalyticsCache,
    analytics_cache_dir,
    analytics_lock,
    default_analytics_lock_path,
)


def _write(
    cache,
    name,
    content=b"data",
    *,
    source_sha256="hash-1",
    latest_data_date="2026-09",
    period=None,
):
    cache.write_partition(
        name,
        content,
        source_sha256=source_sha256,
        latest_data_date=latest_data_date,
        period=period,
    )


class TestAnalyticsCache:
    def test_write_and_read_partition(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)

        _write(cache, "composicao-estoque/2026-09", b"conteudo")
        result = cache.read_partition(
            "composicao-estoque/2026-09",
            source_sha256="hash-1",
            latest_data_date="2026-09",
        )

        assert result == b"conteudo"
        assert cache.manifest_path.name == MANIFEST_NAME
        assert (
            tmp_path / "composicao-estoque" / "2026-09.json"
        ).read_bytes() == b"conteudo"
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_read_only_miss_does_not_change_files(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "p", b"data")
        cache.manifest_path.write_text("not json", encoding="utf-8")

        assert cache.read_partition("p") is None
        assert cache.manifest_path.exists()
        assert (tmp_path / "p.json").exists()

    def test_source_hash_change_invalidates_partition(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "p", b"old", source_sha256="old-hash")

        assert (
            cache.read_partition("p", source_sha256="new-hash") is None
        )
        assert cache.stale_partitions(source_sha256="new-hash") == ["p"]
        assert (tmp_path / "p.json").exists()

    def test_latest_date_change_invalidates_partition(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "p", b"old", latest_data_date="2026-08")

        assert (
            cache.read_partition("p", latest_data_date="2026-09") is None
        )
        assert cache.stale_partitions(latest_data_date="2026-09") == ["p"]

    def test_source_change_recomputes_affected_partition(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "p", b"old", source_sha256="old-hash")

        content, recomputed = cache.read_or_compute(
            "p",
            lambda: b"new",
            source_sha256="new-hash",
            latest_data_date="2026-09",
        )

        assert recomputed is True
        assert content == b"new"
        assert cache.read_partition(
            "p", source_sha256="new-hash"
        ) == b"new"
        assert cache.stale_partitions(source_sha256="new-hash") == []

    def test_concurrent_reader_sees_old_or_new_content(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "p", b"old")
        finished = threading.Event()
        readings = []

        def writer():
            for index in range(20):
                _write(cache, "p", b"new" if index % 2 else b"old")
            finished.set()

        def reader():
            while not finished.is_set():
                readings.append(cache.read_partition("p"))

        thread = threading.Thread(target=writer)
        thread.start()
        reader()
        thread.join()

        assert readings
        assert all(value in (b"old", b"new") for value in readings)

    def test_housekeeping_uses_latest_data_date_for_monthly(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "m/2023-08", period="2023-08")
        _write(cache, "m/2023-09", period="2023-09")
        _write(cache, "m/2026-09", period="2026-09")

        removed = cache.housekeeping("2026-09")

        assert removed == ["m/2023-08"]
        assert not (tmp_path / "m" / "2023-08.json").exists()
        assert (tmp_path / "m" / "2023-09.json").exists()
        assert (tmp_path / "m" / "2026-09.json").exists()

    def test_housekeeping_is_anchored_on_source_date(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "m/2020-12", period="2020-12")
        _write(cache, "m/2021-01", period="2021-01")
        _write(cache, "m/2024-01", period="2024-01")

        removed = cache.housekeeping("2024-01")

        assert removed == ["m/2020-12"]
        assert (tmp_path / "m" / "2021-01.json").exists()

    def test_housekeeping_daily_uses_same_date(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "d/2023-10-01", period="2023-10-01")
        _write(cache, "d/2023-10-02", period="2023-10-02")

        removed = cache.housekeeping("2026-10-02")

        assert removed == ["d/2023-10-01"]
        assert (tmp_path / "d" / "2023-10-02.json").exists()

    def test_corrupted_manifest_is_a_miss_without_deletion(self, tmp_path):
        cache = TesouroAnalyticsCache(tmp_path)
        _write(cache, "p", b"data")
        cache.manifest_path.write_text("{", encoding="utf-8")

        assert cache.load_manifest() is None
        assert cache.read_partition("p") is None
        assert cache.housekeeping("2026-09") == []
        assert (tmp_path / "p.json").exists()
        assert cache.manifest_path.exists()

    def test_default_paths(self):
        assert analytics_cache_dir().name == "analytics"
        assert default_analytics_lock_path().name == "analytics.lock"
        assert default_analytics_lock_path().parent.name == "locks"
        assert (
            default_analytics_lock_path().parent.parent
            == analytics_cache_dir().parent
        )

    def test_analytics_lock_can_be_acquired(self, tmp_path):
        path = tmp_path / "analytics.lock"
        with analytics_lock(path=path):
            assert path.exists()
