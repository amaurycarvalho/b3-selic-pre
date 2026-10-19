import http.client
import tempfile
import unittest
import urllib.error
from unittest import mock

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.infrastructure.cached_client import CachedB3Client


class CommunicationErrorWrapperTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.client = CachedB3Client(cache_dir=self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_url_error_is_wrapped(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            side_effect=urllib.error.URLError("offline"),
        ):
            with self.assertRaises(CommunicationError) as context:
                self.client.fetch_reference_rates("2026-10-19", force=True)
        self.assertIsInstance(context.exception.__cause__, urllib.error.URLError)
        self.assertIn("offline", str(context.exception))

    def test_http_exception_is_wrapped(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            side_effect=http.client.HTTPException("bad response"),
        ):
            with self.assertRaises(CommunicationError) as context:
                self.client.fetch_rates_download("2026-10-19", force=True)
        self.assertIsInstance(
            context.exception.__cause__, http.client.HTTPException
        )

    def test_timeout_is_wrapped(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            side_effect=TimeoutError("timed out"),
        ):
            with self.assertRaises(CommunicationError):
                self.client.fetch_reference_rates("2026-10-19", force=True)

    def test_connection_error_is_wrapped(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            side_effect=ConnectionError("refused"),
        ):
            with self.assertRaises(CommunicationError):
                self.client.fetch_reference_rates("2026-10-19", force=True)

    def test_value_error_is_not_wrapped(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            side_effect=ValueError("invalid"),
        ):
            with self.assertRaises(ValueError):
                self.client.fetch_reference_rates("2026-10-19", force=True)

    def test_plain_os_error_is_not_wrapped(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_reference_rates",
            side_effect=OSError("disk"),
        ):
            with self.assertRaises(OSError) as context:
                self.client.fetch_reference_rates("2026-10-19", force=True)
        self.assertNotIsInstance(context.exception, CommunicationError)

    def test_historical_rates_isolate_download_error(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.cached_client.b3_client.fetch_rates_download",
            side_effect=urllib.error.URLError("offline"),
        ):
            result = self.client.fetch_historical_rates(
                "2020-01-10", force=True
            )
        self.assertEqual(len(result), 5)
        self.assertTrue(all(records == [] for records in result.values()))


if __name__ == "__main__":
    unittest.main()
