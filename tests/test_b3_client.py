import base64
import json
import unittest
from unittest import mock

from b3_selic_pre.infrastructure.b3_client import (
    encode_payload,
    fetch_historical_rates,
    fetch_rates_download,
    fetch_reference_rates,
    fetch_reference_rates_page,
)
from b3_selic_pre.domain.models import RateRecord


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        return False

    def read(self):
        return json.dumps(self.data).encode("utf-8")


class DownloadResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


def _download_b64():
    csv_text = (
        "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\n"
        "Selic x pré;1;1;14,40\n"
    )
    return base64.b64encode(csv_text.encode("latin-1")).decode("latin-1")


class EncodePayloadTest(unittest.TestCase):
    def test_encode_payload_uses_compact_json(self):
        payload = {"language": "pt-br", "date": "2026-06-10", "id": "SLP"}
        expected = base64.b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")
        self.assertEqual(encode_payload(payload), expected)


class FetchReferenceRatesPageTest(unittest.TestCase):
    def test_page_passes_timeout_to_opener(self):
        calls = []

        def opener(url, timeout):
            calls.append((url, timeout))
            return FakeResponse({"results": [], "totalCount": 0})

        fetch_reference_rates_page("2026-06-10", opener=opener)
        self.assertEqual(calls[0][1], 30)

    def test_page_returns_total_count(self):
        data = {
            "results": [{"day252": "1", "day360": "2", "rate": "14.65"}],
            "totalCount": 42,
        }
        records, total_count = fetch_reference_rates_page(
            "2026-06-10", opener=lambda url, **k: FakeResponse(data)
        )
        self.assertEqual(total_count, 42)
        self.assertEqual(
            records, [RateRecord(day252=1, day360=2, rate="14.65")]
        )

    def test_page_missing_total_count_returns_none(self):
        data = {"results": []}
        records, total_count = fetch_reference_rates_page(
            "2026-06-10", opener=lambda url, **k: FakeResponse(data)
        )
        self.assertIsNone(total_count)

    def test_page_uses_default_opener(self):
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                b'{"results": []}'
            )
            records, total_count = fetch_reference_rates_page("2026-06-10")
        self.assertEqual(records, [])
        self.assertIsNone(total_count)


class FetchReferenceRatesTest(unittest.TestCase):
    def test_zero_page_size_raises(self):
        called = []

        def opener(u, **k):
            called.append(u)
            return FakeResponse({"results": []})

        with self.assertRaises(ValueError):
            fetch_reference_rates("2026-06-10", page_size=0, opener=opener)
        self.assertEqual(called, [])
    def test_one_page_size_is_accepted(self):
        data = {"results": [], "totalCount": 1}
        records = fetch_reference_rates("2026-06-10", page_size=1, max_pages=1, opener=lambda u, **k: FakeResponse(data))
        self.assertEqual(records, [])

    def test_zero_max_pages_raises(self):
        called = []

        def opener(u, **k):
            called.append(u)
            return FakeResponse({"results": []})

        with self.assertRaisesRegex(
            ValueError, "Quantidade máxima de páginas deve ser maior que zero"
        ):
            fetch_reference_rates("2026-06-10", max_pages=0, opener=opener)
        self.assertEqual(called, [])

    def test_one_max_page_returns_first_page(self):
        data = {"results": [{"day252": "1", "day360": "2", "rate": "14.65"}]}
        records = fetch_reference_rates("2026-06-10", max_pages=1, opener=lambda u, **k: FakeResponse(data))
        self.assertEqual(len(records), 1)

    def test_progress_callback_receives_page_and_total_pages(self):
        pages = {
            1: {"results": [{"day252": str(i), "day360": str(i), "rate": "14.65"} for i in range(1, 6)], "totalCount": 10},
            2: {"results": [{"day252": "6", "day360": "7", "rate": "14.65"}], "totalCount": 10},
        }

        def opener(url, **k):
            encoded = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            return FakeResponse(pages[payload["pageNumber"]])

        progress = []
        fetch_reference_rates(
            "2026-06-10",
            page_size=5,
            opener=opener,
            progress_callback=lambda p, tp: progress.append((p, tp)),
        )
        self.assertEqual(progress, [(1, 2), (2, 2)])

    def test_stops_when_page_shorter_than_size(self):
        pages = {
            1: {"results": [{"day252": "1", "day360": "2", "rate": "14.65"}], "totalCount": 1},
        }

        def opener(url, timeout):
            encoded = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            return FakeResponse(pages[payload["pageNumber"]])

        records = fetch_reference_rates("2026-06-10", page_size=5, opener=opener)
        self.assertEqual(len(records), 1)

    def test_exceeding_max_pages_raises(self):
        data = {
            "results": [{"day252": str(i), "day360": str(i), "rate": "14.65"} for i in range(1, 6)],
            "totalCount": 100,
        }
        calls = []

        def opener(url, **k):
            calls.append(url)
            return FakeResponse(data)

        with self.assertRaises(ValueError):
            fetch_reference_rates(
                "2026-06-10",
                page_size=5,
                max_pages=1,
                opener=opener,
            )
        self.assertEqual(len(calls), 1)

    def test_page_size_one_computes_total_pages(self):
        pages = {
            1: {"results": [{"day252": "1", "day360": "2", "rate": "14.65"}], "totalCount": 10},
            2: {"results": [], "totalCount": 10},
        }

        def opener(url, **k):
            encoded = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            return FakeResponse(pages[payload["pageNumber"]])

        progress = []
        fetch_reference_rates(
            "2026-06-10",
            page_size=1,
            opener=opener,
            progress_callback=lambda p, tp: progress.append((p, tp)),
        )
        self.assertEqual(progress, [(1, 10), (2, 10)])

    def test_forwards_timeout_to_page_fetcher(self):
        data = {"results": [], "totalCount": 0}
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates_page",
            return_value=([], 0),
        ) as mock_page:
            fetch_reference_rates("2026-06-10", opener=lambda u, **k: FakeResponse(data))
        self.assertEqual(mock_page.call_args.kwargs["timeout"], 30)

    def test_pagination_uses_computed_total_pages(self):
        pages = {
            1: {"results": [{"day252": str(i), "day360": str(i), "rate": "14.65"} for i in range(1, 6)], "totalCount": 10},
            2: {"results": [{"day252": "6", "day360": "7", "rate": "14.65"}], "totalCount": 10},
        }

        def opener(url, **k):
            encoded = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            return FakeResponse(pages[payload["pageNumber"]])

        progress = []
        fetch_reference_rates(
            "2026-06-10",
            page_size=5,
            max_pages=2,
            opener=opener,
            progress_callback=lambda p, tp: progress.append((p, tp)),
        )
        self.assertEqual(progress, [(1, 2), (2, 2)])


class FetchRatesDownloadTest(unittest.TestCase):
    def test_builds_exact_payload(self):
        captured = {}

        def opener(url, timeout):
            captured["url"] = url
            captured["timeout"] = timeout
            return DownloadResponse(_download_b64().encode("latin-1"))

        with mock.patch("urllib.request.urlopen", opener):
            records = fetch_rates_download("2026-06-10")
        self.assertEqual(len(records), 1)
        self.assertEqual(captured["timeout"], 30)
        encoded = captured["url"].rsplit("/", 1)[-1]
        payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
        self.assertEqual(
            payload, {"language": "pt-br", "date": "2026-06-10", "id": "SLP"}
        )
        expected_compact = base64.b64encode(
            json.dumps(
                {"language": "pt-br", "date": "2026-06-10", "id": "SLP"},
                separators=(",", ":"),
            ).encode("utf-8")
        ).decode("utf-8")
        self.assertEqual(encoded, expected_compact)

    def test_empty_response_returns_empty(self):
        with mock.patch("urllib.request.urlopen", lambda u, **k: DownloadResponse(b"")):
            self.assertEqual(fetch_rates_download("2026-06-10"), [])

    def test_whitespace_only_response_returns_empty(self):
        with mock.patch("urllib.request.urlopen", lambda u, **k: DownloadResponse(b"   \n  ")):
            self.assertEqual(fetch_rates_download("2026-06-10"), [])


class FetchHistoricalRatesTest(unittest.TestCase):
    @staticmethod
    def _dates():
        from b3_selic_pre.application.use_cases import _days_ago
        from b3_selic_pre.domain.constants import EVOLUTION_DAYS
        today = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).date().isoformat()
        return [_days_ago(today, d) for d in EVOLUTION_DAYS], today

    def test_today_uses_reference_rates(self):
        dates, today = self._dates()
        reference = [RateRecord(day252=1, day360=1, rate="14.65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=reference,
        ) as mock_ref, mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=[],
        ):
            result = fetch_historical_rates(today)
        self.assertEqual(result[today], reference)
        self.assertIn(mock.call(today, page_size=100), mock_ref.call_args_list)

    def test_past_uses_download_when_available(self):
        dates, today = self._dates()
        past = dates[0]
        download = [RateRecord(day252=1, day360=1, rate="14.40")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=download,
        ) as mock_dl, mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=[],
        ) as mock_ref:
            result = fetch_historical_rates(today)
        self.assertEqual(result[past], download)
        mock_dl.assert_any_call(past)
        self.assertNotIn(mock.call(past, page_size=100), mock_ref.call_args_list)

    def test_past_empty_download_falls_back_to_reference(self):
        dates, today = self._dates()
        past = dates[0]
        fallback = [RateRecord(day252=1, day360=1, rate="14.65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=fallback,
        ) as mock_ref:
            result = fetch_historical_rates(today)
        self.assertEqual(result[past], fallback)
        mock_ref.assert_any_call(past, page_size=100)

    def test_today_uses_reference_rates_not_download(self):
        dates, today = self._dates()
        reference = [RateRecord(day252=1, day360=1, rate="14.65")]
        download_sentinel = [RateRecord(day252=999, day360=999, rate="99.99")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=reference,
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=download_sentinel,
        ):
            result = fetch_historical_rates(today)
        self.assertEqual(result[today], reference)
        self.assertNotEqual(result[today], download_sentinel)

    def test_uses_five_workers(self):
        dates, today = self._dates()
        submitted = []

        class _FakeFuture:
            def __init__(self, fn):
                self.fn = fn

            def result(self):
                return self.fn()

        class _FakePool:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.submitted = []

            def with_kwargs(self, kwargs):
                self.kwargs = kwargs
                return self

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def submit(self, fn, *args):
                fut = _FakeFuture(lambda: fn(*args))
                self.submitted.append(fut)
                return fut

        pool = _FakePool()
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.concurrent.futures.ThreadPoolExecutor",
            side_effect=lambda **kwargs: pool.with_kwargs(kwargs),
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.concurrent.futures.as_completed",
            side_effect=lambda futures: futures,
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=[],
        ):
            fetch_historical_rates(today)
        self.assertEqual(pool.kwargs["max_workers"], 5)

    def test_progress_callback_values(self):
        dates, today = self._dates()
        progress = []
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=[],
        ):
            fetch_historical_rates(today, progress_callback=lambda d, t: progress.append((d, t)))
        self.assertEqual(progress[-1], (5, 5))


if __name__ == "__main__":
    unittest.main()
