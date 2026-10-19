import unittest
from pathlib import Path
from unittest import mock

from b3_selic_pre.infrastructure.disk_cache import _xdg_cache_dir
from b3_selic_pre.infrastructure.xdg import cache_base


class CacheBaseTest(unittest.TestCase):
    def test_linux_default(self):
        with mock.patch("platform.system", return_value="Linux"), mock.patch(
            "os.environ", {}
        ), mock.patch("pathlib.Path.home", return_value=Path("/home/user")):
            self.assertEqual(cache_base(), Path("/home/user/.cache"))

    def test_linux_with_xdg_cache_home(self):
        with mock.patch("platform.system", return_value="Linux"), mock.patch(
            "os.environ", {"XDG_CACHE_HOME": "/custom/cache"}
        ), mock.patch("pathlib.Path.home", return_value=Path("/home/user")):
            self.assertEqual(cache_base(), Path("/custom/cache"))

    def test_windows_default(self):
        with mock.patch("platform.system", return_value="Windows"), mock.patch(
            "os.environ", {}
        ), mock.patch(
            "pathlib.Path.home", return_value=Path("C:\\Users\\User")
        ):
            self.assertEqual(
                cache_base(),
                Path("C:\\Users\\User") / "AppData" / "Local",
            )

    def test_windows_with_localappdata(self):
        with mock.patch("platform.system", return_value="Windows"), mock.patch(
            "os.environ", {"LOCALAPPDATA": "C:\\Custom\\AppData"}
        ), mock.patch(
            "pathlib.Path.home", return_value=Path("C:\\Users\\User")
        ):
            self.assertEqual(cache_base(), Path("C:\\Custom\\AppData"))

    def test_darwin_default(self):
        with mock.patch("platform.system", return_value="Darwin"), mock.patch(
            "pathlib.Path.home", return_value=Path("/Users/user")
        ):
            self.assertEqual(
                cache_base(), Path("/Users/user") / "Library" / "Caches"
            )

    def test_unknown_system_default(self):
        with mock.patch("platform.system", return_value="FreeBSD"), mock.patch(
            "pathlib.Path.home", return_value=Path("/home/user")
        ):
            self.assertEqual(cache_base(), Path("/home/user/.cache"))


class DiskCachePathTest(unittest.TestCase):
    def test_rates_directory_uses_cache_base(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.disk_cache.cache_base",
            return_value=Path("/cache"),
        ):
            self.assertEqual(
                _xdg_cache_dir(), Path("/cache") / "b3-selic-pre" / "rates"
            )


if __name__ == "__main__":
    unittest.main()
