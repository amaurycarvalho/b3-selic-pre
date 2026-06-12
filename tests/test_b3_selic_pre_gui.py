import os
import tempfile
import unittest
from unittest import mock

from b3_selic_pre import RateRecord, SelicPreApp


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

    def test_success_empty_error_copy_and_export_flows(self):
        records = [RateRecord(day252=1, day360=2, rate="14.65")]

        self.app.handle_fetch_success(records)
        self.assertEqual(len(self.app.table.get_children()), 1)
        self.assertIn("1 registro", self.app.status_var.get())

        self.app.copy_records()
        self.assertEqual(self.root.clipboard_get(), "day252,day360,rate\n1,2,14.65\n")

        with tempfile.NamedTemporaryFile(delete=False) as file:
            export_path = file.name
        try:
            with mock.patch(
                "tkinter.filedialog.asksaveasfilename",
                return_value=export_path,
            ):
                self.app.export_records()

            with open(export_path, encoding="utf-8") as file:
                self.assertEqual(file.read(), "day252,day360,rate\n1,2,14.65\n")
        finally:
            os.unlink(export_path)

        self.app.handle_fetch_success([])
        self.assertEqual(len(self.app.table.get_children()), 0)
        self.assertIn("Nenhum registro", self.app.status_var.get())

        self.app.copy_records()
        self.assertIn("Não há dados", self.app.status_var.get())

        self.app.handle_fetch_error(RuntimeError("falha simulada"))
        self.assertEqual(len(self.app.table.get_children()), 0)
        self.assertIn("falha simulada", self.app.status_var.get())


if __name__ == "__main__":
    unittest.main()
