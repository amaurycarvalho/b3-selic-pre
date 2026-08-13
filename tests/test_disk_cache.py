import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.disk_cache import DiskCache


class DiskCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__cache_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.cache = DiskCache(cache_dir=str(self.tmpdir))
        self.records = [
            RateRecord(day252=1, day360=1, rate="14,65"),
            RateRecord(day252=365, day360=365, rate="14,50"),
        ]

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_miss_returns_none(self):
        result = self.cache.get("2099-01-01")
        self.assertIsNone(result)

    def test_put_and_get_hit_returns_records(self):
        self.cache.put("2026-06-17", self.records)
        result = self.cache.get("2026-06-17")
        self.assertEqual(result, self.records)

    def test_get_corrupted_json_deletes_and_returns_none(self):
        path = self.cache._cache_path("2026-06-17")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json", encoding="utf-8")
        result = self.cache.get("2026-06-17")
        self.assertIsNone(result)
        self.assertFalse(path.exists())

    def test_get_corrupted_records_deletes_and_returns_none(self):
        path = self.cache._cache_path("2026-06-17")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({    "cached_at": datetime.now(timezone.utc).isoformat(), "records": [{"bad": "data"}]}),
            encoding="utf-8",
        )
        result = self.cache.get("2026-06-17")
        self.assertIsNone(result)
        self.assertFalse(path.exists())

    def test_is_valid_no_ttl(self):
        self.assertTrue(self.cache._is_valid(datetime.now(timezone.utc).isoformat(), None))
        self.assertTrue(self.cache._is_valid("2020-01-01T00:00:00", None))
        self.assertTrue(self.cache._is_valid(datetime.now(timezone.utc).isoformat(), 0))

    def test_is_valid_with_ttl_not_expired(self):
        now = datetime.now(timezone.utc).isoformat()
        self.assertTrue(self.cache._is_valid(now, 30))

    def test_is_valid_with_ttl_expired(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        self.assertFalse(self.cache._is_valid(past, 30))

    def test_housekeeping_removes_old_files(self):
        old_date = (datetime.now(timezone.utc).date() - timedelta(days=400)).isoformat()
        self.cache.put(old_date, self.records)
        recent_date = (datetime.now(timezone.utc).date() - timedelta(days=10)).isoformat()
        self.cache.put(recent_date, self.records)
        self.cache.housekeeping(max_age_days=365)
        self.assertFalse(self.cache._cache_path(old_date).exists())
        self.assertTrue(self.cache._cache_path(recent_date).exists())

    def test_get_with_expired_ttl_returns_none_and_deletes(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        path = self.cache._cache_path("2026-06-17")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "cached_at": past,
            "ttl_minutes": 30,
            "records": [{"day252": 1, "day360": 1, "rate": "14,65"}],
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        result = self.cache.get("2026-06-17")
        self.assertIsNone(result)
        self.assertFalse(path.exists())


class DiskCacheIsExpiredTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__cache_expired_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.cache = DiskCache(cache_dir=str(self.tmpdir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_is_expired_fresh_stored_ttl_is_false(self):
        data = {"cached_at": datetime.now(timezone.utc).isoformat(), "ttl_minutes": 30}
        self.assertFalse(self.cache._is_expired(data, None))

    def test_is_expired_stored_ttl_without_cached_at_is_false(self):
        data = {"cached_at": None, "ttl_minutes": 30}
        self.assertFalse(self.cache._is_expired(data, None))

    def test_is_expired_old_stored_ttl_is_true(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        data = {"cached_at": past, "ttl_minutes": 30}
        self.assertTrue(self.cache._is_expired(data, None))

    def test_is_expired_fresh_data_with_arg_ttl_is_false(self):
        data = {"cached_at": datetime.now(timezone.utc).isoformat(), "ttl_minutes": None}
        self.assertFalse(self.cache._is_expired(data, 30))

    def test_is_expired_old_data_with_arg_ttl_is_true(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        data = {"cached_at": past, "ttl_minutes": None}
        self.assertTrue(self.cache._is_expired(data, 30))

    def test_get_with_arg_ttl_expires_when_no_stored_ttl(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        path = self.cache._cache_path("2026-06-17")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "cached_at": past,
            "ttl_minutes": None,
            "records": [{"day252": 1, "day360": 1, "rate": "14,65"}],
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIsNone(self.cache.get("2026-06-17", ttl_minutes=30))

    def test_is_valid_ttl_of_one_with_expired_timestamp(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        self.assertFalse(self.cache._is_valid(past, 1))

    def test_is_valid_invalid_timestamp_returns_false(self):
        self.assertFalse(self.cache._is_valid("not-a-date", 30))

    def test_is_valid_equal_age_returns_false(self):
        fixed = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        with mock.patch("b3_selic_pre.infrastructure.disk_cache.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.timedelta = timedelta
            cached = (fixed - timedelta(minutes=30)).isoformat()
            self.assertFalse(self.cache._is_valid(cached, 30))

    def test_put_creates_nested_cache_dir(self):
        cache = DiskCache(cache_dir=str(self.tmpdir / "nested" / "deep"))
        records = [RateRecord(day252=1, day360=1, rate="14,65")]
        cache.put("2026-06-17", records)
        self.assertEqual(cache.get("2026-06-17"), records)

    def test_put_writes_cached_at_and_ttl_keys(self):
        self.cache.put("2026-06-17", self._records(), ttl_minutes=30)
        data = json.loads(
            self.cache._cache_path("2026-06-17").read_text(encoding="utf-8")
        )
        self.assertIn("cached_at", data)
        self.assertIn("ttl_minutes", data)
        self.assertEqual(data["ttl_minutes"], 30)

    def _records(self):
        return [RateRecord(day252=1, day360=1, rate="14,65")]

    def test_put_aware_cached_at_roundtrip_with_ttl(self):
        self.cache.put("2026-06-17", self._records(), ttl_minutes=30)
        self.assertEqual(self.cache.get("2026-06-17", ttl_minutes=30), self._records())

    def test_housekeeping_skips_invalid_filename_and_removes_old(self):
        old_date = (datetime.now(timezone.utc).date() - timedelta(days=400)).isoformat()
        old_path = self.cache._cache_path(old_date)
        old_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "records": []}),
            encoding="utf-8",
        )
        invalid = self.cache._cache_path("notadate")
        invalid.write_text("{}", encoding="utf-8")

        class _FakeDir:
            def glob(self, pattern):
                return [invalid, old_path]

        self.cache.cache_dir = _FakeDir()
        self.cache.housekeeping(max_age_days=365)
        self.assertFalse(old_path.exists())

    def test_housekeeping_keeps_file_at_exact_cutoff(self):
        fixed = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        exact = (fixed - timedelta(days=365)).date().isoformat()
        path = self.cache._cache_path(exact)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"cached_at": fixed.isoformat(), "ttl_minutes": None, "records": []}),
            encoding="utf-8",
        )
        with mock.patch("b3_selic_pre.infrastructure.disk_cache.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            mock_dt.timedelta = timedelta
            self.cache.housekeeping(max_age_days=365)
        self.assertTrue(path.exists())
    def test_housekeeping_uses_utc_now(self):
        import b3_selic_pre.infrastructure.disk_cache as dkc
        real_datetime = dkc.datetime
        calls = []

        class _FakeDatetime:
            @staticmethod
            def now(tz=None):
                calls.append(tz)
                return real_datetime.now(tz)

            fromisoformat = staticmethod(real_datetime.fromisoformat)

        with mock.patch.object(dkc, "datetime", _FakeDatetime):
            self.cache.housekeeping(max_age_days=365)
        self.assertIn(timezone.utc, calls)

    def test_housekeeping_default_max_age_removes_one_year_old(self):
        fixed = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        old = (fixed - timedelta(days=366)).date().isoformat()
        path = self.cache._cache_path(old)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"cached_at": fixed.isoformat(), "ttl_minutes": None, "records": []}),
            encoding="utf-8",
        )
        with mock.patch("b3_selic_pre.infrastructure.disk_cache.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            mock_dt.timedelta = timedelta
            self.cache.housekeeping()
        self.assertFalse(path.exists())


class CachedB3ClientTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__cache_client_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.cache_patcher = mock.patch(
            "b3_selic_pre.infrastructure.cached_client.DiskCache",
            return_value=mock.Mock(spec=DiskCache),
        )
        self.mock_cache_cls = self.cache_patcher.start()
        self.mock_cache = self.mock_cache_cls.return_value
        self.mock_cache.get.return_value = None
        self.mock_cache._cache_path.return_value = self.tmpdir / "test.json"

        from b3_selic_pre.infrastructure.cached_client import CachedB3Client
        self.client = CachedB3Client(cache_dir=str(self.tmpdir))

    def tearDown(self):
        self.cache_patcher.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_fetch_reference_rates_cache_hit(self):
        self.mock_cache.get.return_value = [
            RateRecord(day252=1, day360=1, rate="14,65"),
        ]
        with mock.patch("b3_selic_pre.infrastructure.cached_client.b3_client") as mock_b3:
            result = self.client.fetch_reference_rates("2026-06-17")
        self.assertEqual(len(result), 1)
        mock_b3.fetch_reference_rates.assert_not_called()

    def test_fetch_reference_rates_cache_miss_fetches(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ) as mock_fetch:
            result = self.client.fetch_reference_rates("2026-06-17")
        self.assertEqual(result, expected)
        mock_fetch.assert_called_once_with("2026-06-17")

    def test_fetch_reference_rates_force_skips_cache(self):
        self.mock_cache.get.return_value = [
            RateRecord(day252=1, day360=1, rate="14,65"),
        ]
        expected = [RateRecord(day252=2, day360=2, rate="15,00")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ) as mock_fetch:
            result = self.client.fetch_reference_rates("2026-06-17", force=True)
        self.assertEqual(result, expected)
        mock_fetch.assert_called_once()

    def test_fetch_rates_download_cache_hit(self):
        self.mock_cache.get.return_value = [
            RateRecord(day252=1, day360=1, rate="14,65"),
        ]
        with mock.patch("b3_selic_pre.infrastructure.cached_client.b3_client") as mock_b3:
            result = self.client.fetch_rates_download("2026-06-17")
        self.assertEqual(len(result), 1)
        mock_b3.fetch_rates_download.assert_not_called()

    def test_fetch_rates_download_cache_miss_fetches(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=expected,
        ) as mock_fetch:
            result = self.client.fetch_rates_download("2026-06-17")
        self.assertEqual(result, expected)
        mock_fetch.assert_called_once_with("2026-06-17")

    def test_fetch_historical_rates_uses_per_date_cache(self):
        self.mock_cache.get.return_value = None
        date_records = {
            "2026-06-17": [RateRecord(day252=1, day360=1, rate="14,65")],
            "2026-06-10": [RateRecord(day252=1, day360=1, rate="14,50")],
        }

        def fake_download(date_str):
            return date_records.get(date_str, [])

        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            side_effect=fake_download,
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            result = self.client.fetch_historical_rates("2026-06-17")
        self.assertIn("2026-06-17", result)

    def test_init_stores_defaults(self):
        from b3_selic_pre.infrastructure.cached_client import CachedB3Client
        client = CachedB3Client()
        self.assertEqual(client._ttl_minutes, 30)
        self.assertEqual(client._max_age_days, 365)

    def test_init_passes_cache_dir_to_disk_cache(self):
        from b3_selic_pre.infrastructure.cached_client import CachedB3Client
        self.mock_cache_cls.reset_mock()
        CachedB3Client(cache_dir="/custom/cache")
        self.mock_cache_cls.assert_called_once_with("/custom/cache")

    def test_fetch_from_api_today_uses_reference(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ) as mock_ref, mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
        ) as mock_dl:
            result = self.client._fetch_from_api("2026-06-17", "2026-06-17")
        self.assertEqual(result, expected)
        mock_ref.assert_called_once_with("2026-06-17", page_size=100)
        mock_dl.assert_not_called()

    def test_fetch_from_api_past_uses_download(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=expected,
        ) as mock_dl, mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
        ) as mock_ref:
            result = self.client._fetch_from_api("2026-06-10", "2026-06-17")
        self.assertEqual(result, expected)
        mock_dl.assert_called_once_with("2026-06-10")
        mock_ref.assert_not_called()

    def test_fetch_from_api_empty_download_falls_back_to_reference(self):
        fallback = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=fallback,
        ) as mock_ref:
            result = self.client._fetch_from_api("2026-06-10", "2026-06-17")
        self.assertEqual(result, fallback)
        mock_ref.assert_called_once_with("2026-06-10", page_size=100)

    def test_fetch_one_cache_hit_returns_cached(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        self.mock_cache.get.return_value = expected
        date_str, records, from_cache = self.client._fetch_one("2026-06-17", False, "2026-06-17")
        self.assertEqual(records, expected)
        self.assertTrue(from_cache)
        self.mock_cache.get.assert_called_once_with("2026-06-17", ttl_minutes=30)

    def test_fetch_one_past_date_uses_none_ttl(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        self.mock_cache.get.return_value = expected
        self.client._fetch_one("2026-06-10", False, "2026-06-17")
        self.mock_cache.get.assert_called_once_with("2026-06-10", ttl_minutes=None)

    def test_fetch_one_cache_miss_fetches_and_puts(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.CachedB3Client._fetch_from_api",
            return_value=expected,
        ) as mock_api:
            date_str, records, from_cache = self.client._fetch_one("2026-06-17", False, "2026-06-17")
        self.assertEqual(records, expected)
        self.assertFalse(from_cache)
        mock_api.assert_called_once_with("2026-06-17", "2026-06-17")
        self.mock_cache.put.assert_called_once_with("2026-06-17", expected, ttl_minutes=30)

    def test_fetch_one_force_skips_cache(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.CachedB3Client._fetch_from_api",
            return_value=expected,
        ):
            self.client._fetch_one("2026-06-17", True, "2026-06-17")
        self.mock_cache.get.assert_not_called()

    def test_fetch_reference_rates_put_with_ttl_for_today(self):
        today = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = today
            self.client.fetch_reference_rates("2026-06-17")
        self.mock_cache.put.assert_called_once_with("2026-06-17", expected, ttl_minutes=30)

    def test_fetch_reference_rates_put_without_ttl_for_past(self):
        today = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = today
            self.client.fetch_reference_rates("2026-06-10")
        self.mock_cache.put.assert_called_once_with("2026-06-10", expected, ttl_minutes=None)

    def test_fetch_reference_rates_uses_utc_now(self):
        import b3_selic_pre.infrastructure.cached_client as cc
        real_datetime = cc.datetime
        calls = []

        class _FakeDatetime:
            @staticmethod
            def now(tz=None):
                calls.append(tz)
                return real_datetime.now(tz)

        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ), mock.patch.object(cc, "datetime", _FakeDatetime):
            self.client.fetch_reference_rates("2026-06-17")
        self.assertIn(timezone.utc, calls)

    def test_fetch_reference_rates_hit_calls_source_callback(self):
        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        messages = []
        with mock.patch("b3_selic_pre.infrastructure.cached_client.b3_client") as mock_b3:
            self.client.fetch_reference_rates("2026-06-17", source_callback=messages.append)
        self.assertEqual(messages, ["Cache (2026-06-17)"])
        mock_b3.fetch_reference_rates.assert_not_called()

    def test_fetch_reference_rates_miss_calls_source_callback(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        messages = []
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ):
            self.client.fetch_reference_rates("2026-06-17", source_callback=messages.append)
        self.assertEqual(messages, ["API B3"])

    def test_fetch_reference_rates_forwards_extra_kwargs(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=expected,
        ) as mock_fetch:
            self.client.fetch_reference_rates("2026-06-17", page_size=7)
        mock_fetch.assert_called_once_with("2026-06-17", page_size=7)

    def test_fetch_reference_rates_hit_passes_date_and_no_ttl(self):
        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch("b3_selic_pre.infrastructure.cached_client.b3_client") as mock_b3:
            self.client.fetch_reference_rates("2026-06-17")
        self.mock_cache.get.assert_called_once_with("2026-06-17", ttl_minutes=None)

    def test_fetch_rates_download_miss_puts_and_notifies(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        messages = []
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=expected,
        ):
            self.client.fetch_rates_download("2026-06-17", source_callback=messages.append)
        self.assertEqual(messages, ["Arquivo oficial B3"])
        self.mock_cache.put.assert_called_once_with("2026-06-17", expected, ttl_minutes=None)

    def test_fetch_rates_download_hit_notifies_cache(self):
        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        messages = []
        with mock.patch("b3_selic_pre.infrastructure.cached_client.b3_client") as mock_b3:
            self.client.fetch_rates_download("2026-06-17", source_callback=messages.append)
        self.assertEqual(messages, ["Cache (2026-06-17)"])
        mock_b3.fetch_rates_download.assert_not_called()

    def test_fetch_rates_download_hit_passes_date(self):
        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch("b3_selic_pre.infrastructure.cached_client.b3_client"):
            self.client.fetch_rates_download("2026-06-17")
        self.mock_cache.get.assert_called_once_with("2026-06-17", ttl_minutes=None)

    def test_notify_source_all_cached(self):
        messages = []
        self.client._notify_source(messages.append, 5, 5)
        self.assertEqual(messages, ["Cache (5 datas)"])

    def test_notify_source_partial(self):
        messages = []
        self.client._notify_source(messages.append, 3, 5)
        self.assertEqual(messages, ["Cache (3/5 datas) + B3"])

    def test_notify_source_one_cached(self):
        messages = []
        self.client._notify_source(messages.append, 1, 5)
        self.assertEqual(messages, ["Cache (1/5 datas) + B3"])

    def test_notify_source_none_cached(self):
        messages = []
        self.client._notify_source(messages.append, 0, 5)
        self.assertEqual(messages, ["Histórico B3"])

    def test_notify_source_no_callback(self):
        self.client._notify_source(None, 0, 5)
        self.client._notify_source(None, 5, 5)

    def test_fetch_historical_rates_all_cached_notifies(self):
        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        messages = []
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            result = self.client.fetch_historical_rates(
                "2026-06-17", source_callback=messages.append
            )
        self.assertEqual(len(result), 5)
        self.assertEqual(messages, ["Cache (5 datas)"])

    def test_fetch_historical_rates_none_cached_notifies_historico(self):
        self.mock_cache.get.return_value = None
        messages = []
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            result = self.client.fetch_historical_rates(
                "2026-06-17", source_callback=messages.append
            )
        self.assertEqual(len(result), 5)
        self.assertEqual(messages, ["Histórico B3"])

    def test_fetch_historical_rates_uses_utc_now(self):
        import b3_selic_pre.infrastructure.cached_client as cc
        real_datetime = cc.datetime
        calls = []

        class _FakeDatetime:
            @staticmethod
            def now(tz=None):
                calls.append(tz)
                return real_datetime.now(tz)

        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch.object(cc, "datetime", _FakeDatetime):
            self.client.fetch_historical_rates("2026-06-17")
        self.assertIn(timezone.utc, calls)

    def test_fetch_historical_rates_progress_callback(self):
        self.mock_cache.get.return_value = None
        progress = []
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            self.client.fetch_historical_rates(
                "2026-06-17",
                progress_callback=lambda done, total: progress.append((done, total)),
            )
        self.assertEqual(progress[-1], (5, 5))
        self.assertEqual(progress[0][1], 5)

    def test_fetch_historical_rates_forwards_force(self):
        self.mock_cache.get.return_value = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.CachedB3Client._fetch_one",
            return_value=("2026-06-17", [], False),
        ) as mock_fetch_one, mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            self.client.fetch_historical_rates("2026-06-17", force=True)
        for call in mock_fetch_one.call_args_list:
            self.assertTrue(call[0][1])

    def test_fetch_historical_rates_forwards_today(self):
        self.mock_cache.get.return_value = None
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.CachedB3Client._fetch_one",
            return_value=("2026-06-17", [], False),
        ) as mock_fetch_one, mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            self.client.fetch_historical_rates("2026-06-17")
        for call in mock_fetch_one.call_args_list:
            self.assertEqual(call[0][2], "2026-06-17")

    def test_fetch_historical_rates_housekeeping_called_with_max_age(self):
        self.mock_cache.get.return_value = None
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.cached_client.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
            self.client.fetch_historical_rates("2026-06-17")
        self.mock_cache.housekeeping.assert_called_with(max_age_days=365)


class CLICacheIntegrationTest(unittest.TestCase):
    def test_main_with_no_cache_flag(self):
        records_arg = []

        def fake_cached_fetch(d, force=False, **kwargs):
            records_arg.append((d, force))
            return [RateRecord(day252=1, day360=1, rate="14.65")]

        with mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client",
        ) as mock_client_cls:
            mock_client = mock.Mock()
            mock_client.fetch_reference_rates.side_effect = fake_cached_fetch
            mock_client_cls.return_value = mock_client
            with mock.patch("b3_selic_pre.presentation.cli.print"):
                from b3_selic_pre.presentation.cli import main
                main(["2026-06-17", "--no-cache"])
        self.assertEqual(len(records_arg), 1)
        self.assertEqual(records_arg[0][0], "2026-06-17")
        self.assertTrue(records_arg[0][1])
