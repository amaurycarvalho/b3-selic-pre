import tempfile
import unittest
from pathlib import Path

import pytest

from b3_selic_pre.presentation.gui import GuiDependencies, SelicPreApp
from b3_selic_pre.presentation.settings import Settings

INITIAL_STATUS = "Informe uma data e clique em Buscar."


def _make_dependencies(shortcut_exists: bool = False) -> GuiDependencies:
    return GuiDependencies(
        client=object(),
        shortcut_exists=lambda: shortcut_exists,
        create_shortcut=lambda: None,
        icon_source=lambda: "",
        settings=Settings(path=Path(tempfile.mktemp(suffix=".json"))),
    )


class _FastSelicPreApp(SelicPreApp):
    """App que usa um Entry simples no lugar de tkcalendar.DateEntry."""

    def _create_date_entry(self, parent, tk, ttk):
        return ttk.Entry(parent, textvariable=self.date_var, width=14)


@pytest.mark.slow
@pytest.mark.ui
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
        cls.app = _FastSelicPreApp(cls.root, _make_dependencies())

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.app.records = []
        self.app.historical_data = None
        self.app.view_var.set("raw")
        self.app.evolution_var.set(False)
        self.app.var_3d.set(False)
        self.app.sidebar_var.set(False)
        self.app.status_var.set(INITIAL_STATUS)
        self.app._update_button_states()

    def test_radio_buttons_exist_and_raw_is_default(self):
        self.assertIsNotNone(self.app.view_raw_rb)
        self.assertIsNotNone(self.app.view_consolidated_rb)
        self.assertIsNotNone(self.app.evolution_cb)
        self.assertIsNotNone(self.app.cb_3d)
        self.assertEqual(self.app.view_var.get(), "raw")
        self.assertEqual(self.app.evolution_var.get(), False)
        self.assertEqual(self.app.var_3d.get(), False)

    def test_export_png_replaced_by_toolbar(self):
        self.assertFalse(hasattr(self.app, 'export_button'))
        self.assertFalse(hasattr(self.app, 'export_chart'))

    def test_data_button_exists_and_disabled_without_data(self):
        self.assertIsNotNone(self.app.data_button)
        self.assertEqual(
            str(self.app.data_button.cget("state")),
            "disabled",
        )


@pytest.mark.slow
@pytest.mark.ui
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
        cls.app_no = _FastSelicPreApp(
            cls.root_no, _make_dependencies(shortcut_exists=False)
        )
        cls.app_yes = _FastSelicPreApp(
            cls.root_yes, _make_dependencies(shortcut_exists=True)
        )

    @classmethod
    def tearDownClass(cls):
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


if __name__ == "__main__":
    unittest.main()
