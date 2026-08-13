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

    def test_load_missing_file_keeps_defaults(self):
        with mock.patch("pathlib.Path.exists", return_value=False):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertEqual(settings.get("view_mode"), "raw")

    def test_load_corrupt_file_keeps_defaults(self):
        with mock.patch("pathlib.Path.exists", return_value=True), mock.patch(
            "pathlib.Path.read_text", return_value="{invalid json"
        ):
            settings = Settings(path=Path("/tmp/settings.json"))
        self.assertEqual(settings.get("view_mode"), "raw")


class SettingsAccessTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(__file__).parent / "__settings_test__"
        self.tmpdir.mkdir(exist_ok=True)
        self.settings = Settings(path=self.tmpdir / "settings.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_existing_key(self):
        self.assertEqual(self.settings.get("view_mode"), "raw")

    def test_get_missing_key_returns_default(self):
        self.assertEqual(self.settings.get("nao_existe", "padrao"), "padrao")

    def test_get_missing_key_returns_none(self):
        self.assertIsNone(self.settings.get("nao_existe"))

    def test_getitem_existing_key(self):
        self.assertEqual(self.settings["view_mode"], "raw")

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


if __name__ == "__main__":
    unittest.main()
