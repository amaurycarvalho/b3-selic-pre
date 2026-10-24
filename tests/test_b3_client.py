import base64
import json
import unittest
from unittest import mock

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.infrastructure.b3_client import (
    encode_payload,
    fetch_historical_rates,
    fetch_rates_download,
    fetch_rates_for_date,
    fetch_reference_rates,
    fetch_reference_rates_page,
)
from b3_selic_pre.infrastructure.b3_retry import retry_empty


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


def _download_b64(csv_text=None):
    if csv_text is None:
        csv_text = (
            "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\n"
            "Selic x pré;1;1;14,40\n"
        )
    return base64.b64encode(csv_text.encode("latin-1")).decode("latin-1")


def _page(results, total_records, total_pages):
    return {
        "results": results,
        "page": {
            "pageNumber": 1,
            "pageSize": 100,
            "totalRecords": total_records,
            "totalPages": total_pages,
        },
    }


def _records(count, start=1):
    return [
        {"day252": str(i), "day360": str(i), "rate": "14,65"}
        for i in range(start, start + count)
    ]


class RetryEmptyTest(unittest.TestCase):
    def test_uses_six_attempts_with_jittered_backoff(self):
        attempts = []
        sleeps = []

        def operation():
            attempts.append(1)
            return []

        with self.assertRaises(CommunicationError):
            retry_empty(
                operation,
                date="2026-10-19",
                source="GetList",
                result_is_empty=lambda result: not result,
                sleep=sleeps.append,
                random_fn=lambda: 0.5,
            )
        self.assertEqual(len(attempts), 6)
        self.assertEqual(sleeps, [0.25, 0.5, 1.0, 2.0, 2.0])

    def test_returns_after_first_non_empty_result(self):
        results = iter([[], [1]])
        sleeps = []
        value = retry_empty(
            lambda: next(results),
            date="2026-10-19",
            source="GetList",
            result_is_empty=lambda result: not result,
            sleep=sleeps.append,
            random_fn=lambda: 0.5,
        )
        self.assertEqual(value, [1])
        self.assertEqual(sleeps, [0.25])

    def test_data_error_is_not_retried(self):
        attempts = []

        def operation():
            attempts.append(1)
            raise ValueError("invalid")

        with self.assertRaises(ValueError):
            retry_empty(
                operation,
                date="2026-10-19",
                source="GetList",
                result_is_empty=lambda result: not result,
                sleep=lambda _: None,
            )
        self.assertEqual(len(attempts), 1)

    def test_transient_timeout_is_retried_and_succeeds(self):
        results = iter([TimeoutError("timed out"), [1]])
        sleeps = []

        def operation():
            value = next(results)
            if isinstance(value, BaseException):
                raise value
            return value

        value = retry_empty(
            operation,
            date="2026-10-19",
            source="GetList",
            result_is_empty=lambda result: not result,
            sleep=sleeps.append,
            random_fn=lambda: 0.5,
        )
        self.assertEqual(value, [1])
        self.assertEqual(sleeps, [0.25])

    def test_persistent_timeout_uses_three_attempts(self):
        attempts = []
        sleeps = []

        def operation():
            attempts.append(1)
            raise TimeoutError("timed out")

        with self.assertRaises(CommunicationError) as context:
            retry_empty(
                operation,
                date="2026-10-19",
                source="GetList",
                result_is_empty=lambda result: not result,
                sleep=sleeps.append,
                random_fn=lambda: 0.5,
            )
        self.assertEqual(len(attempts), 3)
        self.assertEqual(sleeps, [0.25, 0.5])
        self.assertIsInstance(context.exception.__cause__, TimeoutError)


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
        self.assertEqual(calls[0][1], 60)

    def test_page_returns_total_count(self):
        data = {
            "results": [{"day252": "1", "day360": "2", "rate": "14.65"}],
            "totalCount": 42,
        }
        records, total_records, total_pages = fetch_reference_rates_page(
            "2026-06-10", opener=lambda url, **k: FakeResponse(data)
        )
        self.assertEqual(total_records, 42)
        self.assertEqual(total_pages, 3)
        self.assertEqual(
            records, [RateRecord(day252=1, day360=2, rate="14.65")]
        )

    def test_page_reads_page_metadata(self):
        data = _page(
            [{"day252": "1", "day360": "2", "rate": "14.65"}], 279, 3
        )
        _, total_records, total_pages = fetch_reference_rates_page(
            "2026-06-10", opener=lambda url, **k: FakeResponse(data)
        )
        self.assertEqual((total_records, total_pages), (279, 3))

    def test_page_prefers_page_metadata_over_total_count(self):
        data = _page([], 10, 2)
        data["totalCount"] = 99
        _, total_records, total_pages = fetch_reference_rates_page(
            "2026-06-10", opener=lambda url, **k: FakeResponse(data)
        )
        self.assertEqual((total_records, total_pages), (10, 2))

    def test_page_missing_total_count_returns_none(self):
        data = {"results": []}
        records, total_records, total_pages = fetch_reference_rates_page(
            "2026-06-10", opener=lambda url, **k: FakeResponse(data)
        )
        self.assertEqual(records, [])
        self.assertIsNone(total_records)
        self.assertIsNone(total_pages)

    def test_page_uses_default_opener(self):
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                b'{"results": []}'
            )
            records, total_records, total_pages = fetch_reference_rates_page(
                "2026-06-10"
            )
        self.assertEqual(records, [])
        self.assertIsNone(total_records)
        self.assertIsNone(total_pages)


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
        data = _page(_records(1), 1, 1)
        records = fetch_reference_rates(
            "2026-06-10",
            page_size=1,
            max_pages=1,
            opener=lambda u, **k: FakeResponse(data),
        )
        self.assertEqual(len(records), 1)

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
        data = _page(_records(1), None, None)
        records = fetch_reference_rates(
            "2026-06-10",
            max_pages=1,
            opener=lambda u, **k: FakeResponse(data),
        )
        self.assertEqual(len(records), 1)

    def test_progress_callback_receives_page_and_total_pages(self):
        pages = {
            1: _page(_records(5), 10, 2),
            2: _page(_records(5, start=6), 10, 2),
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
        data = _page(_records(1), 1, 1)
        records = fetch_reference_rates(
            "2026-06-10",
            page_size=5,
            opener=lambda url, **k: FakeResponse(data),
        )
        self.assertEqual(len(records), 1)

    def test_exceeding_max_pages_raises(self):
        data = _page(_records(5), 100, 20)
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
            1: _page(_records(1), 2, 2),
            2: _page(_records(1, start=2), 2, 2),
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
        self.assertEqual(progress, [(1, 2), (2, 2)])

    def test_forwards_timeout_to_page_fetcher(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_list.fetch_reference_rates_page",
            return_value=([RateRecord(day252=1, day360=1, rate="14.65")], 1, 1),
        ) as mock_page:
            fetch_reference_rates(
                "2026-06-10", opener=lambda u, **k: FakeResponse({})
            )
        self.assertEqual(mock_page.call_args.kwargs["timeout"], 60)

    def test_pagination_uses_computed_total_pages(self):
        pages = {
            1: _page(_records(5), 10, 2),
            2: _page(_records(5, start=6), 10, 2),
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

    def test_empty_expected_page_is_retried(self):
        calls = {1: 0, 2: 0}

        def opener(url, **k):
            encoded = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            page_number = payload["pageNumber"]
            calls[page_number] += 1
            if page_number == 2 and calls[page_number] == 1:
                return FakeResponse(_page([], 10, 2))
            start = 1 if page_number == 1 else 6
            return FakeResponse(_page(_records(5, start=start), 10, 2))

        sleeps = []
        records = fetch_reference_rates(
            "2026-06-10",
            page_size=5,
            opener=opener,
            sleep=sleeps.append,
        )
        self.assertEqual(len(records), 10)
        self.assertEqual(calls[2], 2)
        self.assertEqual(len(sleeps), 1)

    def test_incomplete_collection_raises_communication_error(self):
        pages = {
            1: _page(_records(5), 10, 2),
            2: _page(_records(4, start=6), 10, 2),
        }

        def opener(url, **k):
            encoded = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            return FakeResponse(pages[payload["pageNumber"]])

        with self.assertRaisesRegex(CommunicationError, "esperados 10, obtidos 9"):
            fetch_reference_rates(
                "2026-06-10",
                page_size=5,
                opener=opener,
                sleep=lambda _: None,
            )

    def test_empty_response_after_retries_raises_communication_error(self):
        calls = []

        def opener(url, **k):
            calls.append(url)
            return FakeResponse(_page([], 0, 0))

        with self.assertRaises(CommunicationError):
            fetch_reference_rates(
                "2026-06-10",
                opener=opener,
                sleep=lambda _: None,
            )
        self.assertEqual(len(calls), 6)

    def test_timeout_after_retries_raises_communication_error(self):
        calls = []

        def opener(url, **k):
            calls.append(url)
            raise TimeoutError("timed out")

        with self.assertRaises(CommunicationError):
            fetch_reference_rates(
                "2026-06-10",
                opener=opener,
                sleep=lambda _: None,
            )
        self.assertEqual(len(calls), 3)


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
        self.assertEqual(captured["timeout"], 60)
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

    def test_empty_response_raises_communication_error(self):
        calls = []

        def opener(url, **k):
            calls.append(url)
            return DownloadResponse(b"")

        with mock.patch("urllib.request.urlopen", opener):
            with self.assertRaises(CommunicationError):
                fetch_rates_download("2026-06-10", sleep=lambda _: None)
        self.assertEqual(len(calls), 6)

    def test_timeout_after_retries_raises_communication_error(self):
        calls = []

        def opener(url, timeout):
            calls.append(url)
            raise TimeoutError("timed out")

        with self.assertRaises(CommunicationError):
            fetch_rates_download(
                "2026-06-10", opener=opener, sleep=lambda _: None
            )
        self.assertEqual(len(calls), 3)

    def test_whitespace_only_response_raises_communication_error(self):
        with mock.patch(
            "urllib.request.urlopen", lambda u, **k: DownloadResponse(b"   \n  ")
        ):
            with self.assertRaises(CommunicationError):
                fetch_rates_download("2026-06-10", sleep=lambda _: None)

    def test_transient_empty_response_is_retried(self):
        calls = []

        def opener(url, **k):
            calls.append(url)
            if len(calls) == 1:
                return DownloadResponse(b"")
            return DownloadResponse(_download_b64().encode("latin-1"))

        sleeps = []
        with mock.patch("urllib.request.urlopen", opener):
            records = fetch_rates_download("2026-06-10", sleep=sleeps.append)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(sleeps), 1)

    def test_crlf_csv_rate_has_no_carriage_return(self):
        csv_text = (
            "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\r\n"
            "Selic x pré;1;1;14,40\r\n"
        )
        with mock.patch(
            "urllib.request.urlopen",
            lambda u, **k: DownloadResponse(_download_b64(csv_text).encode("latin-1")),
        ):
            records = fetch_rates_download("2026-06-10")
        self.assertEqual(records[0].rate, "14,40")

    def test_blank_lines_are_ignored(self):
        csv_text = (
            "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\n"
            "\n"
            "Selic x pré;1;1;14,40\n"
            "\n"
        )
        with mock.patch(
            "urllib.request.urlopen",
            lambda u, **k: DownloadResponse(_download_b64(csv_text).encode("latin-1")),
        ):
            records = fetch_rates_download("2026-06-10")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].rate, "14,40")

    def test_malformed_csv_raises_data_error_without_retry(self):
        csv_text = (
            "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\n"
            "Selic x pré;oops;2;14,40\n"
        )
        calls = []

        def opener(url, **k):
            calls.append(url)
            return DownloadResponse(_download_b64(csv_text).encode("latin-1"))

        with mock.patch("urllib.request.urlopen", opener):
            with self.assertRaises(ValueError):
                fetch_rates_download("2026-06-10", sleep=lambda _: None)
        self.assertEqual(len(calls), 1)

    def test_invalid_base64_raises_data_error(self):
        with mock.patch(
            "urllib.request.urlopen",
            lambda u, **k: DownloadResponse(b"not base64!!!"),
        ):
            with self.assertRaises(ValueError):
                fetch_rates_download("2026-06-10", sleep=lambda _: None)


class FetchRatesForDateTest(unittest.TestCase):
    def test_today_uses_getlist(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=expected,
        ) as mock_ref, mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
        ) as mock_dl:
            records, source = fetch_rates_for_date(
                "2026-06-10", today="2026-06-10"
            )
        self.assertEqual(records, expected)
        self.assertEqual(source, "GetList")
        mock_ref.assert_called_once()
        mock_dl.assert_not_called()

    def test_past_uses_download(self):
        expected = [RateRecord(day252=1, day360=1, rate="14,40")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=expected,
        ) as mock_dl, mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
        ) as mock_ref:
            records, source = fetch_rates_for_date(
                "2026-06-10", today="2026-06-17"
            )
        self.assertEqual(records, expected)
        self.assertEqual(source, "GetDownloadFile")
        mock_dl.assert_called_once()
        mock_ref.assert_not_called()

    def test_past_empty_download_falls_back_to_getlist(self):
        fallback = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=fallback,
        ) as mock_ref:
            records, source = fetch_rates_for_date(
                "2026-06-10", today="2026-06-17"
            )
        self.assertEqual(records, fallback)
        self.assertEqual(source, "GetList")
        mock_ref.assert_called_once()

    def test_past_download_communication_error_falls_back_to_getlist(self):
        fallback = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            side_effect=CommunicationError("empty"),
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=fallback,
        ) as mock_ref:
            records, source = fetch_rates_for_date(
                "2026-06-10", today="2026-06-17"
            )
        self.assertEqual(records, fallback)
        self.assertEqual(source, "GetList")
        mock_ref.assert_called_once()

    def test_past_download_timeout_falls_back_to_getlist(self):
        calls = []

        def opener(url, timeout):
            calls.append(url)
            if "GetDownloadFile" in url:
                raise TimeoutError("timed out")
            return FakeResponse(_page(_records(1), 1, 1))

        records, source = fetch_rates_for_date(
            "2026-06-10",
            today="2026-06-17",
            opener=opener,
            sleep=lambda _: None,
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(source, "GetList")
        self.assertEqual(len(calls), 4)

    def test_past_data_error_does_not_fall_back(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            side_effect=ValueError("bad csv"),
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
        ) as mock_ref:
            with self.assertRaises(ValueError):
                fetch_rates_for_date("2026-06-10", today="2026-06-17")
        mock_ref.assert_not_called()


class FetchHistoricalRatesTest(unittest.TestCase):
    @staticmethod
    def _dates():
        from b3_selic_pre.application.use_cases import days_ago, evolution_dates

        today = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).date().isoformat()
        dates = evolution_dates(today)
        assert dates == [days_ago(today, d) for d in (28, 21, 14, 7, 0)]
        return dates, today

    def test_today_uses_reference_rates(self):
        dates, today = self._dates()
        reference = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=reference,
        ) as mock_ref, mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=reference,
        ):
            result = fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(result[today], reference)
        self.assertTrue(
            any(call.args[0] == today for call in mock_ref.call_args_list)
        )

    def test_past_uses_download_when_available(self):
        dates, today = self._dates()
        past = dates[0]
        download = [RateRecord(day252=1, day360=1, rate="14,40")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=download,
        ) as mock_dl, mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=download,
        ) as mock_ref:
            result = fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(result[past], download)
        self.assertTrue(
            any(call.args[0] == past for call in mock_dl.call_args_list)
        )
        self.assertFalse(
            any(call.args[0] == past for call in mock_ref.call_args_list)
        )

    def test_past_empty_download_falls_back_to_reference(self):
        dates, today = self._dates()
        past = dates[0]
        fallback = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=[],
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=fallback,
        ) as mock_ref:
            result = fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(result[past], fallback)
        self.assertTrue(
            any(call.args[0] == past for call in mock_ref.call_args_list)
        )

    def test_today_uses_reference_rates_not_download(self):
        dates, today = self._dates()
        reference = [RateRecord(day252=1, day360=1, rate="14,65")]
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_reference_rates",
            return_value=reference,
        ), mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_download",
            return_value=reference,
        ) as mock_dl:
            result = fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(result[today], reference)
        self.assertFalse(
            any(call.args[0] == today for call in mock_dl.call_args_list)
        )

    def test_unavailable_date_is_isolated(self):
        dates, today = self._dates()
        unavailable = dates[0]
        records = [RateRecord(day252=1, day360=1, rate="14,65")]

        def fake_fetch(date_str, **kwargs):
            if date_str == unavailable:
                raise CommunicationError("empty")
            return records, "GetList"

        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_for_date",
            side_effect=fake_fetch,
        ):
            result = fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(result[unavailable], [])
        self.assertEqual(result[dates[1]], records)
        self.assertEqual(len(result), 5)

    def test_all_unavailable_dates_return_empty_lists(self):
        dates, today = self._dates()
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_for_date",
            side_effect=CommunicationError("empty"),
        ):
            result = fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(set(result), set(dates))
        self.assertTrue(all(records == [] for records in result.values()))

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
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_for_date",
            return_value=([], "GetList"),
        ):
            fetch_historical_rates(today, sleep=lambda _: None)
        self.assertEqual(pool.kwargs["max_workers"], 5)

    def test_progress_callback_values(self):
        dates, today = self._dates()
        progress = []
        with mock.patch(
            "b3_selic_pre.infrastructure.b3_client.fetch_rates_for_date",
            return_value=([], "GetList"),
        ):
            fetch_historical_rates(
                today,
                progress_callback=lambda d, t: progress.append((d, t)),
                sleep=lambda _: None,
            )
        self.assertEqual(progress[-1], (5, 5))


if __name__ == "__main__":
    unittest.main()
