"""Testes headless dos adapters de abertura de links e diretórios."""

from unittest import mock

from b3_selic_pre.infrastructure import links
from b3_selic_pre.infrastructure.links import open_directory, open_url


class TestOpenUrl:
    def test_returns_true_when_browser_opens(self):
        with mock.patch.object(links.webbrowser, "open", return_value=True) as opener:
            assert open_url("https://example.com") is True
        opener.assert_called_once_with("https://example.com")

    def test_returns_false_when_browser_does_not_open(self):
        with mock.patch.object(links.webbrowser, "open", return_value=False):
            assert open_url("https://example.com") is False

    def test_returns_false_when_browser_raises(self):
        with mock.patch.object(
            links.webbrowser, "open", side_effect=OSError("no browser")
        ):
            assert open_url("https://example.com") is False


class TestOpenDirectory:
    def test_linux_uses_xdg_open(self):
        completed = mock.Mock(returncode=0)
        with mock.patch.object(links.os.path, "isdir", return_value=True), mock.patch.object(
            links.platform, "system", return_value="Linux"
        ), mock.patch.object(
            links.subprocess, "run", return_value=completed
        ) as runner:
            assert open_directory("/tmp/logs") is True
        runner.assert_called_once_with(["xdg-open", "/tmp/logs"], check=False)

    def test_macos_uses_open_command(self):
        completed = mock.Mock(returncode=0)
        with mock.patch.object(links.os.path, "isdir", return_value=True), mock.patch.object(
            links.platform, "system", return_value="Darwin"
        ), mock.patch.object(
            links.subprocess, "run", return_value=completed
        ) as runner:
            assert open_directory("/tmp/logs") is True
        runner.assert_called_once_with(["open", "/tmp/logs"], check=False)

    def test_windows_uses_startfile(self):
        with mock.patch.object(links.os.path, "isdir", return_value=True), mock.patch.object(
            links.platform, "system", return_value="Windows"
        ), mock.patch.object(
            links.os, "startfile", create=True
        ) as starter:
            assert open_directory("C:\\logs") is True
        starter.assert_called_once_with("C:\\logs")

    def test_missing_directory_is_not_opened(self):
        with mock.patch.object(links.os.path, "isdir", return_value=False), mock.patch.object(
            links.subprocess, "run"
        ) as runner, mock.patch.object(
            links.platform, "system"
        ) as system:
            assert open_directory("/tmp/missing") is False
        runner.assert_not_called()
        system.assert_not_called()

    def test_non_zero_return_code_reports_failure(self):
        completed = mock.Mock(returncode=1)
        with mock.patch.object(links.os.path, "isdir", return_value=True), mock.patch.object(
            links.platform, "system", return_value="Linux"
        ), mock.patch.object(links.subprocess, "run", return_value=completed):
            assert open_directory("/tmp/logs") is False

    def test_startfile_failure_reports_failure(self):
        with mock.patch.object(links.os.path, "isdir", return_value=True), mock.patch.object(
            links.platform, "system", return_value="Windows"
        ), mock.patch.object(
            links.os, "startfile", create=True, side_effect=OSError("no handler")
        ):
            assert open_directory("C:\\logs") is False

    def test_command_failure_reports_failure(self):
        with mock.patch.object(links.os.path, "isdir", return_value=True), mock.patch.object(
            links.platform, "system", return_value="Linux"
        ), mock.patch.object(
            links.subprocess, "run", side_effect=OSError("xdg-open missing")
        ):
            assert open_directory("/tmp/logs") is False
