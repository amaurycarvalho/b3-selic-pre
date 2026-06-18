import base64
import json
import os
import unittest
from unittest import mock

from b3_selic_pre import (
    RateRecord,
    SHORTCUT_CHECK_PATH,
    _brl,
    _days_ago,
    _detect_desktop_dir,
    _icon_source,
    _resolve_executable,
    average_rate_by_year,
    build_payload,
    build_url,
    consolidate_by_year,
    create_shortcut,
    encode_payload,
    fetch_historical_rates,
    fetch_rates_download,
    fetch_reference_rates,
    format_cli_rows,
    format_evolution_csv,
    format_records_csv,
    format_yearly_rows,
    main,
    normalize_records,
    render_chart,
    render_curve_evolution,
    render_detailed_evolution,
    shortcut_exists,
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

        self.assertEqual(text, "DU252,DC365,TAXA\n1,2,14.65\n")

    def test_consolidate_by_year_groups_by_day360_divided_by_365(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14.65"),
            RateRecord(day252=2, day360=2, rate="14.70"),
            RateRecord(day252=365, day360=365, rate="14.50"),
            RateRecord(day252=366, day360=366, rate="15.10"),
            RateRecord(day252=730, day360=730, rate="15.00"),
            RateRecord(day252=731, day360=731, rate="14.80"),
        ]
        consolidated = consolidate_by_year(records)
        self.assertEqual(
            consolidated,
            [
                {"year": 0, "min_rate": 14.65, "max_rate": 14.70},
                {"year": 1, "min_rate": 14.50, "max_rate": 15.10},
                {"year": 2, "min_rate": 14.80, "max_rate": 15.00},
            ],
        )

    def test_consolidate_by_year_single_record(self):
        records = [RateRecord(day252=1, day360=1, rate="14.65")]
        consolidated = consolidate_by_year(records)
        self.assertEqual(
            consolidated,
            [{"year": 0, "min_rate": 14.65, "max_rate": 14.65}],
        )

    def test_consolidate_by_year_handles_comma_decimal_separator(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14,65"),
            RateRecord(day252=2, day360=2, rate="14,70"),
        ]
        consolidated = consolidate_by_year(records)
        self.assertEqual(
            consolidated,
            [{"year": 0, "min_rate": 14.65, "max_rate": 14.70}],
        )

    def test_consolidate_by_year_empty_list(self):
        self.assertEqual(consolidate_by_year([]), [])

    def test_brl_formats_with_two_decimals_and_comma(self):
        self.assertEqual(_brl(14.5), "14,50")
        self.assertEqual(_brl(14.0), "14,00")
        self.assertEqual(_brl(14.658), "14,66")
        self.assertEqual(_brl(0.0), "0,00")

    def test_format_yearly_rows_outputs_consolidated_csv(self):
        consolidated = [
            {"year": 0, "min_rate": 14.5, "max_rate": 14.7},
            {"year": 1, "min_rate": 14.8, "max_rate": 15.1},
        ]
        text = format_yearly_rows(consolidated)
        self.assertEqual(
            text,
            'ANO,MENOR_TAXA,MAIOR_TAXA\n0,"14,50","14,70"\n1,"14,80","15,10"\n',
        )

    def test_format_yearly_rows_empty(self):
        self.assertEqual(format_yearly_rows([]), "ANO,MENOR_TAXA,MAIOR_TAXA\n")

    def test_main_yearly_flag_uses_consolidated_output(self):
        from b3_selic_pre import main

        records_arg = []

        def fake_fetch(date):
            records_arg.append(date)
            return [
                RateRecord(day252=1, day360=1, rate="14.65"),
                RateRecord(day252=365, day360=365, rate="14.50"),
            ]

        with mock.patch("b3_selic_pre.fetch_reference_rates", fake_fetch), \
             mock.patch("b3_selic_pre.print") as mock_print:
            main(["2026-01-01", "--yearly"])
            self.assertEqual(records_arg, ["2026-01-01"])
            mock_print.assert_called_once_with(
                'ANO,MENOR_TAXA,MAIOR_TAXA\n0,"14,65","14,65"\n1,"14,50","14,50"\n'
            )

    def test_average_rate_by_year_midpoint(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14.65"),
            RateRecord(day252=2, day360=2, rate="14.70"),
            RateRecord(day252=365, day360=365, rate="14.50"),
            RateRecord(day252=366, day360=366, rate="15.10"),
        ]
        avg = average_rate_by_year(records)
        self.assertEqual(avg, {0: 14.675, 1: 14.80})

    def test_average_rate_by_year_empty(self):
        self.assertEqual(average_rate_by_year([]), {})

    def test_average_rate_by_year_single_record(self):
        records = [RateRecord(day252=1, day360=1, rate="14.65")]
        self.assertEqual(average_rate_by_year(records), {0: 14.65})

    def test_days_ago(self):
        self.assertEqual(_days_ago("2026-06-17", 0), "2026-06-17")
        self.assertEqual(_days_ago("2026-06-17", 7), "2026-06-10")
        self.assertEqual(_days_ago("2026-06-17", 28), "2026-05-20")

    def test_fetch_rates_download_parses_csv(self):
        csv_content = (
            "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\n"
            "Selic x pré;1;1;14,40\n"
            "Selic x pré;4;6;14,37\n"
        )
        b64_csv = base64.b64encode(csv_content.encode("latin-1")).decode("latin-1")

        def opener(url, timeout):
            class R:
                def read(self):
                    return b64_csv.encode("latin-1")
                def __enter__(self):
                    return self
                def __exit__(self, *a):
                    return False
            return R()

        with mock.patch("urllib.request.urlopen", opener):
            records = fetch_rates_download("2026-06-09")

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0], RateRecord(day252=1, day360=1, rate="14,40"))
        self.assertEqual(records[1], RateRecord(day252=4, day360=6, rate="14,37"))

    def test_fetch_historical_rates_returns_5_dates_for_today(self):
        today = __import__("datetime").date.today().isoformat()
        csv_content = (
            "Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa\n"
            "Selic x pré;1;1;14,40\n"
        )
        b64_csv = base64.b64encode(csv_content.encode("latin-1")).decode("latin-1")

        class FakeDownloadResponse:
            def __init__(self, body):
                self._body = body
            def read(self):
                return self._body
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        def opener(url, timeout):
            if "GetDownloadFile" in url:
                return FakeDownloadResponse(b64_csv.encode("latin-1"))
            encoded_payload = url.rsplit("/", 1)[-1]
            payload = json.loads(base64.b64decode(encoded_payload).decode("utf-8"))
            if payload.get("pageNumber") == 1:
                return FakeResponse({
                    "results": [
                        {"day252": "1", "day360": "1", "rate": "14.65"},
                        {"day252": "365", "day360": "365", "rate": "14.50"},
                    ]
                })
            return FakeResponse({"results": []})

        with mock.patch("urllib.request.urlopen", opener):
            results = fetch_historical_rates(
                today, progress_callback=lambda c, t: None,
            )

        self.assertEqual(len(results), 5)
        dates = sorted(results.keys())
        self.assertEqual(dates[0], _days_ago(today, 28))
        self.assertEqual(dates[-1], today)

    def test_format_evolution_csv(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
        ]
        date_rates = {"2026-06-17": records, "2026-06-03": records}
        csv_out = format_evolution_csv(date_rates)
        self.assertIn("DATA;ANO;TAXA_MEDIA", csv_out)
        self.assertIn("2026-06-03;0;14.65", csv_out)
        self.assertIn("2026-06-03;1;14.50", csv_out)
        self.assertIn("2026-06-17;0;14.65", csv_out)
        self.assertIn("2026-06-17;1;14.50", csv_out)

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


class ChartRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import matplotlib
        matplotlib.use("Agg")

    def setUp(self):
        from matplotlib.figure import Figure
        self.fig = Figure()
        self.fig.add_subplot(111)

    def test_render_chart_empty_shows_message(self):
        render_chart(self.fig, [])
        ax = self.fig.gca()
        texts = [t.get_text() for t in ax.texts]
        self.assertIn("Sem dados", texts)

    def test_render_chart_raw_green_line(self):
        records = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=2, day360=60, rate="14.70"),
        ]
        render_chart(self.fig, records, consolidated=False)
        ax = self.fig.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].get_color(), "green")

    def test_render_chart_consolidated_blue_red_lines(self):
        records = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
        ]
        render_chart(self.fig, records, consolidated=True)
        ax = self.fig.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 2)
        colors = [line.get_color() for line in lines]
        self.assertIn("blue", colors)
        self.assertIn("red", colors)

    def test_render_chart_raw_xaxis_22_day_minor_ticks(self):
        records = [RateRecord(day252=i, day360=i, rate="15.0") for i in range(1, 61)]
        render_chart(self.fig, records, consolidated=False)
        ax = self.fig.gca()
        from matplotlib.ticker import FixedLocator
        loc = ax.xaxis.get_minor_locator()
        self.assertIsInstance(loc, FixedLocator)
        self.assertIn(1, loc.locs)
        self.assertIn(23, loc.locs)
        self.assertIn(45, loc.locs)

    def test_render_chart_raw_has_66du_major_ticks(self):
        records = [RateRecord(day252=i, day360=i, rate="15.0") for i in [1, 60, 120]]
        render_chart(self.fig, records, consolidated=False)
        ax = self.fig.gca()
        ticks = ax.get_xticks()
        self.assertIn(60, ticks)
        self.assertIn(120, ticks)

    def test_render_chart_consolidated_has_3yr_major_ticks(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
            RateRecord(day252=730, day360=730, rate="14.00"),
            RateRecord(day252=1095, day360=1095, rate="13.50"),
            RateRecord(day252=1460, day360=1460, rate="13.00"),
            RateRecord(day252=1825, day360=1825, rate="12.50"),
            RateRecord(day252=2190, day360=2190, rate="12.00"),
        ]
        render_chart(self.fig, records, consolidated=True)
        ax = self.fig.gca()
        ticks = ax.get_xticks()
        self.assertIn(3, ticks)
        self.assertIn(6, ticks)


class CurveEvolutionChartTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import matplotlib
        matplotlib.use("Agg")

    def setUp(self):
        from matplotlib.figure import Figure
        self.fig = Figure()
        self.fig.add_subplot(111)

    def _make_date_rates(self):
        r0 = [RateRecord(day252=1, day360=1, rate="14.0"),
              RateRecord(day252=60, day360=60, rate="14.0"),
              RateRecord(day252=120, day360=120, rate="14.0"),
              RateRecord(day252=365, day360=365, rate="14.5")]
        r1 = [RateRecord(day252=1, day360=1, rate="14.2"),
              RateRecord(day252=60, day360=60, rate="14.2"),
              RateRecord(day252=120, day360=120, rate="14.2"),
              RateRecord(day252=365, day360=365, rate="14.3")]
        return {"2026-06-17": r0, "2026-06-03": r1}

    def test_render_curve_evolution_shows_lines(self):
        date_rates = self._make_date_rates()
        render_curve_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        lines = ax.get_lines()
        self.assertGreaterEqual(len(lines), 2)

    def test_render_curve_evolution_empty_shows_message(self):
        render_curve_evolution(self.fig, {})
        ax = self.fig.gca()
        texts = [t.get_text() for t in ax.texts]
        self.assertIn("Sem dados", texts)

    def test_render_curve_evolution_has_quiver(self):
        date_rates = self._make_date_rates()
        render_curve_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        quivers = [c for c in ax.collections if hasattr(c, 'get_offsets')]
        self.assertGreaterEqual(len(quivers), 1)

    def test_render_curve_evolution_has_legend(self):
        date_rates = self._make_date_rates()
        render_curve_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        self.assertIsNotNone(ax.get_legend())

    def test_render_curve_evolution_xaxis_years(self):
        date_rates = self._make_date_rates()
        render_curve_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        self.assertEqual(ax.get_xlim(), (0, 20))

    def test_render_detailed_evolution_shows_lines(self):
        date_rates = self._make_date_rates()
        render_detailed_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        lines = ax.get_lines()
        self.assertGreaterEqual(len(lines), 2)

    def test_render_detailed_evolution_empty_shows_message(self):
        render_detailed_evolution(self.fig, {})
        ax = self.fig.gca()
        texts = [t.get_text() for t in ax.texts]
        self.assertIn("Sem dados", texts)

    def test_render_detailed_evolution_uses_green_gradient(self):
        date_rates = self._make_date_rates()
        render_detailed_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        lines = ax.get_lines()
        for line in lines:
            r, g, b, _ = line.get_color()
            self.assertGreater(g, r)
            self.assertGreater(g, b)

    def test_render_detailed_evolution_has_legend(self):
        date_rates = self._make_date_rates()
        render_detailed_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        self.assertIsNotNone(ax.get_legend())

    def test_render_detailed_evolution_xaxis_dias_uteis(self):
        date_rates = self._make_date_rates()
        render_detailed_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        self.assertEqual(ax.get_xlabel(), "Dias úteis")
        self.assertAlmostEqual(ax.get_xlim()[0], 0, delta=1)
        self.assertAlmostEqual(ax.get_xlim()[1], 756, delta=1)

    def test_render_curve_evolution_has_3yr_major_ticks(self):
        r0 = [RateRecord(day252=d, day360=d, rate="14.0") for d in [1, 365, 730, 1095, 1460, 1825, 2190]]
        r1 = [RateRecord(day252=d, day360=d, rate="14.5") for d in [1, 365, 730, 1095, 1460, 1825, 2190]]
        date_rates = {"2026-06-17": r0, "2026-06-03": r1}
        render_curve_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        ticks = ax.get_xticks()
        self.assertIn(3, ticks)

    def test_render_detailed_evolution_has_quiver(self):
        r0 = [RateRecord(day252=60, day360=60, rate="14.0"),
              RateRecord(day252=1, day360=1, rate="14.0")]
        r1 = [RateRecord(day252=60, day360=60, rate="14.2"),
              RateRecord(day252=1, day360=1, rate="14.2")]
        date_rates = {"2026-06-17": r0, "2026-06-03": r1}
        render_detailed_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        quivers = [c for c in ax.collections if hasattr(c, 'get_offsets')]
        self.assertGreaterEqual(len(quivers), 1)

    def test_render_detailed_evolution_has_66du_major_ticks(self):
        date_rates = self._make_date_rates()
        render_detailed_evolution(self.fig, date_rates)
        ax = self.fig.gca()
        ticks = ax.get_xticks()
        self.assertIn(60, ticks)
        self.assertIn(120, ticks)


class ShortcutTest(unittest.TestCase):
    def test_detect_desktop_dir_xdg_user_dir(self):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "/home/user/Desktop"
            result = _detect_desktop_dir()
            self.assertEqual(result, "/home/user/Desktop")

    def test_detect_desktop_dir_xdg_fallback_to_user_dirs(self):
        def fake_run(cmd, **kw):
            raise FileNotFoundError()
        with mock.patch("subprocess.run", fake_run), \
             mock.patch("builtins.open", mock.mock_open(
                 read_data='XDG_DESKTOP_DIR="$HOME/Desktop"\n')), \
             mock.patch("os.path.isfile", return_value=True):
            result = _detect_desktop_dir()
            self.assertTrue(result.endswith("/Desktop"))

    def test_detect_desktop_dir_fallback(self):
        def fake_run(cmd, **kw):
            raise FileNotFoundError()
        with mock.patch("subprocess.run", fake_run), \
             mock.patch("os.path.isfile", return_value=False):
            result = _detect_desktop_dir()
            self.assertTrue(result.endswith("/Desktop"))

    def test_resolve_executable_script_mode(self):
        with mock.patch("sys.frozen", False, create=True), \
             mock.patch("sys.argv", ["/app/b3_selic_pre.py"]), \
             mock.patch("sys.executable", "/usr/bin/python3"):
            result = _resolve_executable()
            self.assertEqual(result, "/usr/bin/python3 /app/b3_selic_pre.py")

    def test_resolve_executable_frozen_mode(self):
        with mock.patch("sys.frozen", True, create=True), \
             mock.patch("sys.executable", "/usr/local/bin/b3-selic-pre"):
            result = _resolve_executable()
            self.assertEqual(result, "/usr/local/bin/b3-selic-pre")

    def test_icon_source_script_mode(self):
        with mock.patch("sys.frozen", False, create=True), \
             mock.patch("b3_selic_pre._SCRIPT_DIR", "/app"):
            result = _icon_source()
            self.assertEqual(result, "/app/icons/b3_selic_pre.png")

    def test_icon_source_frozen_mode(self):
        with mock.patch("sys.frozen", True, create=True), \
             mock.patch("sys._MEIPASS", "/bundle", create=True):
            result = _icon_source()
            self.assertEqual(result, "/bundle/b3_selic_pre.png")

    def test_shortcut_exists_returns_true_when_file_exists(self):
        with mock.patch("os.path.isfile", return_value=True):
            self.assertTrue(shortcut_exists())

    def test_shortcut_exists_returns_false_when_file_missing(self):
        with mock.patch("os.path.isfile", return_value=False):
            self.assertFalse(shortcut_exists())

    def test_create_shortcut_writes_desktop_files(self):
        writes = {}

        def fake_makedirs(path, exist_ok=False):
            pass

        def fake_chmod(path, mode):
            pass

        fake_open = mock.mock_open()
        fake_open.return_value.__enter__.return_value.write.side_effect = \
            lambda content: writes.setdefault("content", content)

        def fake_copy2(src, dst):
            writes["icon_copied"] = (src, dst)

        with mock.patch("os.makedirs", fake_makedirs), \
             mock.patch("builtins.open", fake_open), \
             mock.patch("os.chmod", fake_chmod), \
             mock.patch("shutil.copy2", fake_copy2), \
             mock.patch("os.path.isfile", return_value=True), \
             mock.patch("b3_selic_pre._resolve_executable",
                        return_value="/usr/bin/python3 /app/b3_selic_pre.py"), \
             mock.patch("b3_selic_pre._icon_source",
                        return_value="/app/icons/b3_selic_pre.png"), \
             mock.patch("b3_selic_pre._detect_desktop_dir",
                        return_value="/home/user/Desktop"):
            create_shortcut()

        self.assertIn("icon_copied", writes)
        self.assertIn("Name=Taxas Referenciais SELIC (B3)", writes["content"])
        self.assertIn("Categories=Finance;Office;", writes["content"])
        self.assertIn("/usr/bin/python3 /app/b3_selic_pre.py --gui",
                      writes["content"])

    def test_main_create_shortcut_calls_create_shortcut(self):
        with mock.patch("b3_selic_pre.create_shortcut") as mock_cs, \
             mock.patch("b3_selic_pre.print") as mock_print:
            main(["--create-shortcut"])

        mock_cs.assert_called_once()
        mock_print.assert_called_once_with(
            "Atalho criado em ~/Desktop/ e ~/.local/share/applications/"
        )


if __name__ == "__main__":
    unittest.main()
