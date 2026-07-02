import json
import unittest
from datetime import date, datetime, timedelta, timezone
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
        old_date = (date.today() - timedelta(days=400)).isoformat()
        self.cache.put(old_date, self.records)
        recent_date = (date.today() - timedelta(days=10)).isoformat()
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
        ):
            with mock.patch(
                "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
                return_value=[],
            ):
                with mock.patch(
                    "b3_selic_pre.infrastructure.cached_client._today_date",
                ) as mock_today:
                    mock_today.today.return_value.isoformat.return_value = "2026-06-17"
                    result = self.client.fetch_historical_rates("2026-06-17")
        self.assertIn("2026-06-17", result)


class CLICacheIntegrationTest(unittest.TestCase):
    def test_main_with_no_cache_flag(self):
        records_arg = []

        def fake_cached_fetch(date, force=False, **kwargs):
            records_arg.append((date, force))
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
