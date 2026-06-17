import os
import tempfile
import unittest
from unittest import mock

from b3_selic_pre import (
    RateRecord,
    SelicPreApp,
    consolidate_by_year,
    format_cli_rows,
    format_yearly_rows,
)


class SelicPreAppTest(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from tkinter import TclError

        try:
            self.root = tk.Tk()
        except TclError as exc:
            self.skipTest(f"tkinter display unavailable: {exc}")
        self.root.withdraw()
        self.app = SelicPreApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_invalid_date_shows_validation_without_fetching(self):
        self.app.date_var.set("10/06/2026")

        with mock.patch("b3_selic_pre.fetch_reference_rates") as fetch:
            self.app.fetch_rates()

        fetch.assert_not_called()
        self.assertIn("YYYY-MM-DD", self.app.status_var.get())

    def test_success_and_empty_and_error_flows(self):
        records = [RateRecord(day252=1, day360=2, rate="14.65")]

        self.app.handle_fetch_success(records)
        self.assertIn("1 registro", self.app.status_var.get())
        self.assertIsNotNone(self.app.figure)
        self.assertEqual(len(self.app.records), 1)

        self.app.handle_fetch_success([])
        self.assertIn("Nenhum registro", self.app.status_var.get())
        self.assertEqual(len(self.app.records), 0)

        self.app.handle_fetch_error(RuntimeError("falha simulada"))
        self.assertIn("falha simulada", self.app.status_var.get())
        self.assertEqual(len(self.app.records), 0)

    def test_consolidate_checkbox_exists_and_defaults_to_off(self):
        self.assertIsNotNone(self.app.consolidate_cb)
        self.assertFalse(self.app.consolidate_var.get())

    def test_toggle_checkbox_updates_chart(self):
        records = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
        ]
        self.app.handle_fetch_success(records)

        ax = self.app.figure.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].get_color(), "green")

        self.app.consolidate_var.set(True)
        self.app.toggle_view()

        lines = ax.get_lines()
        self.assertEqual(len(lines), 2)
        colors = [line.get_color() for line in lines]
        self.assertIn("blue", colors)
        self.assertIn("red", colors)

    def test_fetch_respects_consolidate_toggle(self):
        records = [RateRecord(day252=1, day360=30, rate="14.65")]
        self.app.handle_fetch_success(records)

        self.app.consolidate_var.set(True)
        records2 = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
        ]
        self.app.handle_fetch_success(records2)

        ax = self.app.figure.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 2)

    def test_export_png(self):
        records = [RateRecord(day252=1, day360=2, rate="14.65")]
        self.app.handle_fetch_success(records)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as file:
            export_path = file.name
        try:
            with mock.patch(
                "tkinter.filedialog.asksaveasfilename",
                return_value=export_path,
            ):
                self.app.export_chart()

            self.assertTrue(os.path.getsize(export_path) > 0)
        finally:
            os.unlink(export_path)

    def test_buttons_disabled_without_data(self):
        self.assertEqual(
            str(self.app.copy_button.cget("state")),
            "disabled",
        )
        self.assertEqual(
            str(self.app.export_button.cget("state")),
            "disabled",
        )

    def test_buttons_enabled_after_data_loaded(self):
        records = [RateRecord(day252=1, day360=2, rate="14.65")]
        self.app.handle_fetch_success(records)

        self.assertEqual(
            str(self.app.copy_button.cget("state")),
            "normal",
        )
        self.assertEqual(
            str(self.app.export_button.cget("state")),
            "normal",
        )

    def test_buttons_disabled_after_error_clears_data(self):
        self.app.handle_fetch_success([RateRecord(day252=1, day360=2, rate="14.65")])
        self.app.handle_fetch_error(RuntimeError("falha simulada"))

        self.assertEqual(
            str(self.app.copy_button.cget("state")),
            "disabled",
        )

    def test_data_button_exists_and_disabled_without_data(self):
        self.assertIsNotNone(self.app.data_button)
        self.assertEqual(
            str(self.app.data_button.cget("state")),
            "disabled",
        )

    def test_data_button_enabled_after_data_loaded(self):
        records = [RateRecord(day252=1, day360=2, rate="14.65")]
        self.app.handle_fetch_success(records)

        self.assertEqual(
            str(self.app.data_button.cget("state")),
            "normal",
        )

    def test_data_button_disabled_after_error_clears_data(self):
        self.app.handle_fetch_success([RateRecord(day252=1, day360=2, rate="14.65")])
        self.app.handle_fetch_error(RuntimeError("falha simulada"))

        self.assertEqual(
            str(self.app.data_button.cget("state")),
            "disabled",
        )

    def test_copy_data_raw_mode(self):
        records = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=2, day360=60, rate="14.50"),
        ]
        self.app.handle_fetch_success(records)
        self.app.consolidate_var.set(False)

        expected = format_cli_rows(records)

        with mock.patch.object(self.app.root, "clipboard_clear") as mock_clear:
            with mock.patch.object(self.app.root, "clipboard_append") as mock_append:
                self.app.copy_data()

        mock_clear.assert_called_once()
        mock_append.assert_called_once_with(expected)
        self.assertIn("Dados copiados", self.app.status_var.get())

    def test_copy_data_consolidated_mode(self):
        records = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
            RateRecord(day252=366, day360=425, rate="14.80"),
        ]
        self.app.handle_fetch_success(records)
        self.app.consolidate_var.set(True)

        expected = format_yearly_rows(consolidate_by_year(records))

        with mock.patch.object(self.app.root, "clipboard_clear") as mock_clear:
            with mock.patch.object(self.app.root, "clipboard_append") as mock_append:
                self.app.copy_data()

        mock_clear.assert_called_once()
        mock_append.assert_called_once_with(expected)
        self.assertIn("Dados copiados", self.app.status_var.get())

    def test_copy_data_noop_when_no_data(self):
        with mock.patch.object(self.app.root, "clipboard_clear") as mock_clear:
            with mock.patch.object(self.app.root, "clipboard_append") as mock_append:
                self.app.copy_data()

        mock_clear.assert_not_called()
        mock_append.assert_not_called()


if __name__ == "__main__":
    unittest.main()
