import tempfile
import unittest
from pathlib import Path
from unittest import mock

from b3_selic_pre.application.formatting import format_cli_rows, format_yearly_rows
from b3_selic_pre.application.use_cases import consolidate_by_year, default_reference_date
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation.gui import SelicPreApp
from b3_selic_pre.presentation.settings import Settings

INITIAL_STATUS = "Informe uma data e clique em Buscar."


def _settings_patch():
    return mock.patch(
        "b3_selic_pre.presentation.gui.app.Settings",
        side_effect=lambda: Settings(path=Path(tempfile.mktemp(suffix=".json"))),
    )


class _FastSelicPreApp(SelicPreApp):
    """App que usa um Entry simples no lugar de tkcalendar.DateEntry."""

    def _create_date_entry(self, parent, tk, ttk):
        return ttk.Entry(parent, textvariable=self.date_var, width=14)


class SelicPreAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tkinter as tk
        from tkinter import TclError
        try:
            cls.root = tk.Tk()
        except TclError as exc:
            raise unittest.SkipTest(f"tkinter display unavailable: {exc}") from exc
        cls.root.withdraw()
        cls._settings_patch = _settings_patch()
        cls._settings_patch.start()
        cls.app = _FastSelicPreApp(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls._settings_patch.stop()
        cls.root.destroy()

    def setUp(self):
        self._reset_app_state()

    def _reset_app_state(self):
        self.app.records = []
        self.app.historical_data = None
        self.app._data_source = ""
        self.app._historical_fetching = False
        self.app._last_reference_date = None
        if getattr(self.app, "_restore_after_id", None):
            self.app.root.after_cancel(self.app._restore_after_id)
            self.app._restore_after_id = None
        if getattr(self.app, "_configure_after_id", None):
            try:
                self.app.root.after_cancel(self.app._configure_after_id)
            except self.app.tk.TclError:
                pass
            self.app._configure_after_id = None
        self.app.view_var.set("raw")
        self.app.evolution_var.set(False)
        self.app.var_3d.set(False)
        self.app.sidebar_var.set(False)
        if str(self.app.sidebar_frame) in self.app.pane.panes():
            self.app.pane.forget(self.app.sidebar_frame)
        self.app.date_var.set(default_reference_date())
        self.app.status_var.set(INITIAL_STATUS)
        self.app.statusbar_label.config(foreground=self.app._statusbar_default_fg)
        self.app._set_ui_locked(False)
        self.app.cb_3d.configure(state=self.app.tk.DISABLED)
        self.app.figure.clear()
        self.app._update_button_states()

    def _make_real_app(self):
        import tkinter as tk
        from tkinter import TclError
        try:
            root = tk.Tk()
        except TclError as exc:
            self.skipTest(f"tkinter display unavailable: {exc}")
        root.withdraw()
        with mock.patch(
            "b3_selic_pre.presentation.gui.app.shortcut_exists",
            return_value=True,
        ):
            app = SelicPreApp(root)
        return root, app

    def test_invalid_date_shows_validation_without_fetching(self):
        root, app = self._make_real_app()
        try:
            app.date_var.set("10/06/2026")
            with mock.patch.object(app._client, "fetch_reference_rates") as fetch:
                app.fetch_rates()
            fetch.assert_not_called()
            self.assertIn("YYYY-MM-DD", app.status_var.get())
        finally:
            root.destroy()

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

    def test_radio_buttons_exist_and_raw_is_default(self):
        self.assertIsNotNone(self.app.view_raw_rb)
        self.assertIsNotNone(self.app.view_consolidated_rb)
        self.assertIsNotNone(self.app.evolution_cb)
        self.assertIsNotNone(self.app.cb_3d)
        self.assertEqual(self.app.view_var.get(), "raw")
        self.assertEqual(self.app.evolution_var.get(), False)
        self.assertEqual(self.app.var_3d.get(), False)

    def test_toggle_to_consolidated_updates_chart(self):
        records = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
        ]
        self.app.handle_fetch_success(records)
        ax = self.app.figure.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].get_color(), "green")
        self.app.view_var.set("consolidated")
        self.app.toggle_view()
        ax = self.app.figure.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 2)
        colors = [line.get_color() for line in lines]
        self.assertIn("blue", colors)
        self.assertIn("red", colors)

    def test_fetch_respects_view_mode(self):
        records = [RateRecord(day252=1, day360=30, rate="14.65")]
        self.app.handle_fetch_success(records)
        self.app.view_var.set("consolidated")
        records2 = [
            RateRecord(day252=1, day360=30, rate="14.65"),
            RateRecord(day252=365, day360=365, rate="14.50"),
        ]
        self.app.handle_fetch_success(records2)
        ax = self.app.figure.gca()
        lines = ax.get_lines()
        self.assertEqual(len(lines), 2)

    def test_export_png_replaced_by_toolbar(self):
        self.assertFalse(hasattr(self.app, 'export_button'))
        self.assertFalse(hasattr(self.app, 'export_chart'))

    def test_buttons_disabled_without_data(self):
        self.assertEqual(
            str(self.app.copy_toolbar_btn.cget("state")),
            "disabled",
        )

    def test_buttons_enabled_after_data_loaded(self):
        records = [RateRecord(day252=1, day360=2, rate="14.65")]
        self.app.handle_fetch_success(records)
        self.assertEqual(
            str(self.app.copy_toolbar_btn.cget("state")),
            "normal",
        )

    def test_buttons_disabled_after_error_clears_data(self):
        self.app.handle_fetch_success([RateRecord(day252=1, day360=2, rate="14.65")])
        self.app.handle_fetch_error(RuntimeError("falha simulada"))
        self.assertEqual(
            str(self.app.copy_toolbar_btn.cget("state")),
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
        self.app.view_var.set("raw")
        expected = format_cli_rows(records)
        with mock.patch.object(self.app.root, "clipboard_clear") as mock_clear, mock.patch.object(self.app.root, "clipboard_append") as mock_append:
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
        self.app.view_var.set("consolidated")
        expected = format_yearly_rows(consolidate_by_year(records))
        with mock.patch.object(self.app.root, "clipboard_clear") as mock_clear, mock.patch.object(self.app.root, "clipboard_append") as mock_append:
            self.app.copy_data()
        mock_clear.assert_called_once()
        mock_append.assert_called_once_with(expected)
        self.assertIn("Dados copiados", self.app.status_var.get())

    def test_copy_data_noop_when_no_data(self):
        with mock.patch.object(self.app.root, "clipboard_clear") as mock_clear, mock.patch.object(self.app.root, "clipboard_append") as mock_append:
            self.app.copy_data()
        mock_clear.assert_not_called()
        mock_append.assert_not_called()

    def test_3d_checkbox_disabled_when_evolution_off(self):
        self.assertEqual(str(self.app.cb_3d.cget("state")), "disabled")

    def test_3d_checkbox_enabled_when_evolution_on_with_data(self):
        records = [RateRecord(day252=1, day360=1, rate="14.0")]
        self.app.historical_data = {"2026-06-17": records}
        self.app.evolution_var.set(True)
        self.app.toggle_evolution()
        self.assertEqual(str(self.app.cb_3d.cget("state")), "normal")

    def test_3d_checkbox_disabled_and_reset_when_evolution_turned_off(self):
        records = [RateRecord(day252=1, day360=1, rate="14.0")]
        self.app.historical_data = {"2026-06-17": records}
        self.app.evolution_var.set(True)
        self.app.toggle_evolution()
        self.app.var_3d.set(True)
        self.app.evolution_var.set(False)
        self.app.toggle_evolution()
        self.assertEqual(str(self.app.cb_3d.cget("state")), "disabled")
        self.assertEqual(self.app.var_3d.get(), False)

    def test_3d_triggers_3d_render_dispatch(self):
        records = [RateRecord(day252=1, day360=1, rate="14.0")]
        self.app.historical_data = {"2026-06-17": records}
        self.app.evolution_var.set(True)
        self.app.toggle_evolution()
        self.app.var_3d.set(True)
        with mock.patch("b3_selic_pre.presentation.gui.chart.render_3d_evolution") as mock_3d:
            self.app._redraw_chart()
        mock_3d.assert_called_once()


class SelicPreAppShortcutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tkinter as tk
        from tkinter import TclError
        try:
            cls.root_no = tk.Tk()
            cls.root_yes = tk.Tk()
        except TclError as exc:
            raise unittest.SkipTest(f"tkinter display unavailable: {exc}") from exc
        cls.root_no.withdraw()
        cls.root_yes.withdraw()
        cls._settings_patch = _settings_patch()
        cls._settings_patch.start()
        with mock.patch(
            "b3_selic_pre.presentation.gui.app.shortcut_exists",
            return_value=False,
        ):
            cls.app_no = _FastSelicPreApp(cls.root_no)
        cls.shortcut_btn_no = cls.app_no.shortcut_button
        with mock.patch(
            "b3_selic_pre.presentation.gui.app.shortcut_exists",
            return_value=True,
        ):
            cls.app_yes = _FastSelicPreApp(cls.root_yes)

    def setUp(self):
        if self.app_no.shortcut_button is None:
            self.shortcut_btn_no.pack(side=self.app_no.tk.RIGHT)
            self.app_no.shortcut_button = self.shortcut_btn_no
        self.app_no.status_var.set(INITIAL_STATUS)

    @classmethod
    def tearDownClass(cls):
        cls._settings_patch.stop()
        cls.root_no.destroy()
        cls.root_yes.destroy()

    def test_shortcut_button_shown_when_no_shortcut(self):
        self.assertIsNotNone(self.app_no.shortcut_button)
        self.assertEqual(
            str(self.app_no.shortcut_button.cget("text")),
            "Criar Atalho Desktop",
        )

    def test_shortcut_button_hidden_when_shortcut_exists(self):
        self.assertIsNone(self.app_yes.shortcut_button)

    def test_shortcut_button_callback_creates_shortcut(self):
        self.assertIsNotNone(self.app_no.shortcut_button)
        with mock.patch("b3_selic_pre.presentation.gui.actions.create_shortcut") as mock_cs:
            self.app_no._create_shortcut()
        mock_cs.assert_called_once()
        self.assertIsNone(self.app_no.shortcut_button)
        self.assertIn("Atalho criado", self.app_no.status_var.get())


if __name__ == "__main__":
    unittest.main()
