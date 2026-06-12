import base64
import json
import unittest

from b3_selic_pre import (
    RateRecord,
    build_payload,
    build_url,
    encode_payload,
    fetch_reference_rates,
    format_cli_rows,
    format_records_csv,
    normalize_records,
    validate_reference_date,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        return False

    def read(self):
        return json.dumps(self.data).encode("utf-8")


class B3SelicPreTest(unittest.TestCase):
    def test_build_payload_uses_b3_defaults_and_date(self):
        self.assertEqual(
            build_payload("2026-06-10"),
            {
                "language": "pt-br",
                "id": "SLP",
                "pageNumber": 1,
                "pageSize": 20,
                "date": "2026-06-10",
            },
        )

    def test_encode_payload_matches_compact_base64_json(self):
        payload = build_payload("2026-06-10")
        encoded = encode_payload(payload)
        decoded = json.loads(base64.b64decode(encoded).decode("utf-8"))

        self.assertEqual(decoded, payload)

    def test_build_url_contains_encoded_payload(self):
        payload = build_payload("2026-06-10")

        self.assertTrue(
            build_url(payload).startswith(
                "https://sistemaswebb3-derivativos.b3.com.br/"
                "referenceRatesProxy/Search/GetList/"
            )
        )
        self.assertTrue(build_url(payload).endswith(encode_payload(payload)))

    def test_validate_reference_date_accepts_iso_date(self):
        self.assertEqual(validate_reference_date("2026-06-10"), "2026-06-10")

    def test_validate_reference_date_rejects_invalid_format(self):
        with self.assertRaises(ValueError):
            validate_reference_date("10/06/2026")

    def test_validate_reference_date_rejects_invalid_calendar_date(self):
        with self.assertRaises(ValueError):
            validate_reference_date("2026-02-30")

    def test_normalize_records_returns_stable_fields(self):
        records = normalize_records(
            {
                "results": [
                    {
                        "day252": "1",
                        "day360": "2",
                        "rate": 14.65,
                        "ignored": "value",
                    }
                ]
            }
        )

        self.assertEqual(records, [RateRecord(day252=1, day360=2, rate="14.65")])

    def test_normalize_records_rejects_missing_results(self):
        with self.assertRaises(ValueError):
            normalize_records({})

    def test_fetch_reference_rates_collects_all_pages(self):
        requests = []
        pages = {
            1: [
                {"day252": "1", "day360": "2", "rate": "14.65"},
                {"day252": "21", "day360": "30", "rate": "14.70"},
            ],
            2: [
                {"day252": "42", "day360": "60", "rate": "14.75"},
            ],
        }

        def opener(url, timeout):
            encoded_payload = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded_payload).decode("utf-8"))
            requests.append(payload)
            return FakeResponse({"results": pages[payload["pageNumber"]]})

        records = fetch_reference_rates(
            "2026-06-10",
            opener=opener,
            page_size=2,
        )

        self.assertEqual(
            records,
            [
                RateRecord(day252=1, day360=2, rate="14.65"),
                RateRecord(day252=21, day360=30, rate="14.70"),
                RateRecord(day252=42, day360=60, rate="14.75"),
            ],
        )
        self.assertEqual([request["pageNumber"] for request in requests], [1, 2])
        self.assertEqual([request["pageSize"] for request in requests], [2, 2])

    def test_format_cli_rows_outputs_csv_with_header(self):
        text = format_cli_rows([RateRecord(day252=1, day360=2, rate="14.65")])

        self.assertEqual(text, "DU252,DC360,TAXA\n1,2,14.65\n")

    def test_format_records_csv_includes_headers_and_rows(self):
        text = format_records_csv(
            [
                RateRecord(day252=1, day360=2, rate="14.65"),
                RateRecord(day252=21, day360=30, rate="14.70"),
            ]
        )

        self.assertEqual(
            text,
            "day252,day360,rate\n"
            "1,2,14.65\n"
            "21,30,14.70\n",
        )


if __name__ == "__main__":
    unittest.main()
