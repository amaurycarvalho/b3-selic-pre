import json
import platform
import unittest
from pathlib import Path
from unittest import mock

from b3_selic_pre.presentation.settings import Settings, _xdg_path


class XdgPathTest(unittest.TestCase):
    def test_linux_default(self):
        with mock.patch("platform.system", return_value="Linux"), mock.patch(
            "os.environ", {}
        ), mock.patch("pathlib.Path.home", return_value=Path("/home/user")):
            self.assertEqual(
                _xdg_path(), Path("/home/user/.config/b3-selic-pre/settings.json")
            )

    def test_linux_with_xdg_config_home(self):
        with mock.patch("platform.system", return_value="Linux"), mock.patch(
            "os.environ", {"XDG_CONFIG_HOME": "/custom/config"}
        ), mock.patch("pathlib.Path.home", return_value=Path("/home/user")):
            self.assertEqual(
                _xdg_path(), Path("/custom/config/b3-selic-pre/settings.json")
            )

    def test_windows_default(self):
        with mock.patch("platform.system", return_value="Windows"), mock.patch(
            "os.environ", {}
        ), mock.patch("pathlib.Path.home", return_value=Path("C:\\Users\\User")):
            self.assertEqual(
                _xdg_path(),
                Path("C:\\Users\\User") / "AppData" / "Roaming" / "b3-selic-pre" / "settings.json",
            )

    def test_windows_with_appdata(self):
        with mock.patch("platform.system", return_value="Windows"), mock.patch(
            "os.environ", {"APPDATA": "C:\\Custom\\AppData"}
        ), mock.patch("pathlib.Path.home", return_value=Path("C:\\Users\\User")):
            self.assertEqual(
                _xdg_path(), Path("C:\\Custom\\AppData") / "b3-selic-pre" / "settings.json"
            )

    def test_darwin_default(self):
        with mock.patch("platform.system", return_value="Darwin"), mock.patch(
            "pathlib.Path.home", return_value=Path("/Users/user")
        ):
            self.assertEqual(
                _xdg_path(),
                Path("/Users/user") / "Library" / "Application Support" / "b3-selic-pre" / "settings.json",
            )

    def test_unknown_system_default(self):
        with mock.patch("platform.system", return_value="FreeBSD"), mock.patch(
            "pathlib.Path.home", return_value=Path("/home/user")
        ):
            self.assertEqual(
                _xdg_path(), Path("/home/user/.config/b3-selic-pre/settings.json")
            )


class SettingsLoadTest(unittest.TestCase):
    def test_load_reads_existing_file(self):
        data = {"view_mode": "detailed"}
        with mock.patch("pathlib.Path.exists", return_value=True), mock.patch(
            "pathlib.Path.read_text", return_value=json.dumps(data)
        ):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertEqual(settings.get("view_mode"), "detailed")

    def test_load_ignores_non_dict(self):
        with mock.patch("pathlib.Path.exists", return_value=True), mock.patch(
            "pathlib.Path.read_text", return_value="[1, 2, 3]"
        ):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertEqual(settings.get("view_mode"), "raw")

    def test_load_missing_file_uses_first_run_defaults(self):
        with mock.patch("pathlib.Path.exists", return_value=False):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertTrue(settings.is_first_run)
        self.assertEqual(settings.get("view_mode"), "consolidated")
        self.assertTrue(settings.get("evolution"))
        self.assertTrue(settings.get("sidebar"))
        self.assertFalse(settings.get("show_3d"))

    def test_missing_file_does_not_write_settings(self):
        with mock.patch("pathlib.Path.exists", return_value=False), mock.patch(
            "pathlib.Path.write_text"
        ) as mock_write:
            Settings(path=Path("/tmp/settings.json"))
        mock_write.assert_not_called()

    def test_load_corrupt_file_keeps_compatibility_defaults(self):
        with mock.patch("pathlib.Path.exists", return_value=True), mock.patch(
            "pathlib.Path.read_text", return_value="{invalid json"
        ):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertFalse(settings.is_first_run)
        self.assertEqual(settings.get("view_mode"), "raw")
        self.assertFalse(settings.get("evolution"))
        self.assertFalse(settings.get("sidebar"))

    def test_existing_file_missing_keys_uses_compatibility_defaults(self):
        with mock.patch("pathlib.Path.exists", return_value=True), mock.patch(
            "pathlib.Path.read_text",
            return_value=json.dumps({"last_date": "2026-06-10"}),
        ):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertFalse(settings.is_first_run)
        self.assertEqual(settings["last_date"], "2026-06-10")
        self.assertEqual(settings.get("view_mode"), "raw")
        self.assertFalse(settings.get("evolution"))
        self.assertFalse(settings.get("sidebar"))

    def test_existing_preferences_prevail_over_first_run_defaults(self):
        data = {
            "view_mode": "detailed",
            "evolution": False,
            "sidebar": False,
            "show_3d": True,
        }
        with mock.patch("pathlib.Path.exists", return_value=True), mock.patch(
            "pathlib.Path.read_text", return_value=json.dumps(data)
        ):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertFalse(settings.is_first_run)
        self.assertEqual(settings["view_mode"], "detailed")
        self.assertFalse(settings["evolution"])
        self.assertFalse(settings["sidebar"])
        self.assertTrue(settings["show_3d"])


class SettingsAccessTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__settings_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.settings = Settings(path=self.tmpdir / "settings.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_existing_key(self):
        self.assertEqual(self.settings.get("view_mode"), "consolidated")

    def test_get_missing_key_returns_default(self):
        self.assertEqual(self.settings.get("nao_existe", "padrao"), "padrao")

    def test_get_missing_key_returns_none(self):
        self.assertIsNone(self.settings.get("nao_existe"))

    def test_getitem_existing_key(self):
        self.assertEqual(self.settings["view_mode"], "consolidated")

    def test_getitem_missing_key_raises(self):
        with self.assertRaises(KeyError):
            _ = self.settings["nao_existe"]

    def test_setitem_persists(self):
        with mock.patch("pathlib.Path.write_text") as mock_write, mock.patch(
            "pathlib.Path.mkdir"
        ):
            self.settings["view_mode"] = "detailed"
        self.assertEqual(self.settings["view_mode"], "detailed")
        mock_write.assert_called_once()

    def test_first_set_persists_first_run_defaults(self):
        with mock.patch("pathlib.Path.write_text") as mock_write, mock.patch(
            "pathlib.Path.mkdir"
        ):
            self.settings["last_date"] = "2026-10-20"
        payload = json.loads(mock_write.call_args.args[0])
        self.assertEqual(payload["last_date"], "2026-10-20")
        self.assertEqual(payload["view_mode"], "consolidated")
        self.assertTrue(payload["evolution"])
        self.assertTrue(payload["sidebar"])
        self.assertFalse(payload["show_3d"])


class LogRetentionDaysTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__log_retention_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.settings = Settings(path=self.tmpdir / "settings.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_missing_key_uses_default(self):
        del self.settings._data["log_retention_days"]
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_valid_integer_is_used(self):
        self.settings._data["log_retention_days"] = 3
        self.assertEqual(self.settings.log_retention_days(), 3)

    def test_string_falls_back_to_default(self):
        self.settings._data["log_retention_days"] = "7"
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_float_falls_back_to_default(self):
        self.settings._data["log_retention_days"] = 7.0
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_boolean_falls_back_to_default(self):
        self.settings._data["log_retention_days"] = True
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_none_falls_back_to_default(self):
        self.settings._data["log_retention_days"] = None
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_zero_falls_back_to_default(self):
        self.settings._data["log_retention_days"] = 0
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_negative_falls_back_to_default(self):
        self.settings._data["log_retention_days"] = -1
        self.assertEqual(self.settings.log_retention_days(), 7)

    def test_large_integer_is_used(self):
        large = 10**100
        self.settings._data["log_retention_days"] = large
        self.assertEqual(self.settings.log_retention_days(), large)


if __name__ == "__main__":
    unittest.main()


class SettingsDataReferenciaTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__settings_referencia_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.path = self.tmpdir / "settings.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_is_empty(self):
        settings = Settings(path=self.path)
        self.assertEqual(settings.get("data_referencia"), "")

    def test_persists_data_referencia_atomically(self):
        settings = Settings(path=self.path)
        settings["data_referencia"] = "2026-06-17"
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["data_referencia"], "2026-06-17")
        self.assertEqual(list(self.tmpdir.glob("*.tmp")), [])

    def test_missing_key_does_not_break_loading(self):
        self.path.write_text(
            json.dumps({"last_date": "2026-06-10"}), encoding="utf-8"
        )
        settings = Settings(path=self.path)
        self.assertEqual(settings.get("data_referencia"), "")
