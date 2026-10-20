import argparse
import io
from contextlib import redirect_stderr
from unittest import mock

from b3_selic_pre.presentation.mcp import command


class _Settings:
    def __init__(self, events):
        self.events = events
        self.values = {}

    def __setitem__(self, key, value):
        self.events.append("set")
        self.values[key] = value

    def get(self, key, default=None):
        return self.values.get(key, default)


class _Lock:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        self.events.append("enter")
        return self

    def __exit__(self, *args):
        self.events.append("exit")


class _Server:
    def __init__(self, events):
        self.events = events

    def run(self):
        self.events.append("run")
        return 0


def _args(**kwargs):
    values = {"data": None, "atualizar": False}
    values.update(kwargs)
    return argparse.Namespace(**values)


def _run(args, events, load_update, server=None):
    settings = _Settings(events)
    server = server or _Server(events)
    with mock.patch.object(command, "load_update", load_update), mock.patch.object(
        command, "McpServer", return_value=server
    ):
        code = command.run_mcp_command(
            args,
            settings,
            cache=object(),
            client_factory=object,
            lock_factory=lambda: _Lock(events),
            settings_factory=lambda: settings,
        )
    return code, settings


def test_without_preparation_starts_server_without_lock():
    events = []
    code, _ = _run(_args(), events, mock.Mock())
    assert code == 0
    assert events == ["run"]


def test_data_prepares_under_lock_and_persists_reference():
    events = []
    load = mock.Mock(return_value=([object()], {}))

    with mock.patch.object(
        command, "resolve_data", return_value="2026-06-17"
    ) as resolve:
        code, settings = _run(_args(data="2026-06-17"), events, load)

    assert code == 0
    resolve.assert_called_once_with("2026-06-17")
    assert events == ["enter", "set", "exit", "run"]
    assert settings.values["data_referencia"] == "2026-06-17"


def test_both_flags_do_one_update_with_data():
    events = []
    load = mock.Mock(return_value=([object()], {}))

    with mock.patch.object(
        command, "resolve_data", return_value="2026-06-17"
    ) as resolve:
        code, _ = _run(
            _args(atualizar=True, data="2026-06-17"), events, load
        )

    assert code == 0
    resolve.assert_called_once_with("2026-06-17")
    load.assert_called_once()


def test_preparation_failure_does_not_start_server():
    events = []
    load = mock.Mock(side_effect=RuntimeError("offline"))
    stderr = io.StringIO()

    with mock.patch.object(
        command, "resolve_data", return_value="2026-06-17"
    ), redirect_stderr(stderr):
        code, _ = _run(_args(data="2026-06-17"), events, load)

    assert code == 1
    assert "run" not in events
    assert "Falha na preparação" in stderr.getvalue()


def test_empty_records_does_not_start_server_or_persist():
    events = []
    load = mock.Mock(return_value=([], {}))
    stderr = io.StringIO()

    with mock.patch.object(
        command, "resolve_data", return_value="2026-06-17"
    ), redirect_stderr(stderr):
        code, settings = _run(_args(data="2026-06-17"), events, load)

    assert code == 1
    assert "run" not in events
    assert "data_referencia" not in settings.values
    assert "Nenhum registro encontrado" in stderr.getvalue()


def test_invalid_date_returns_two_without_server():
    events = []
    with mock.patch.object(
        command, "resolve_data", side_effect=ValueError("bad date")
    ), redirect_stderr(io.StringIO()):
        code, _ = _run(_args(data="bad"), events, mock.Mock())

    assert code == 2
    assert events == []


def test_progress_and_source_go_to_stderr():
    events = []
    stderr = io.StringIO()

    def load(client, data, **kwargs):
        kwargs["source_callback"]("Cache")
        kwargs["progress_callback"](1, 5)
        return [object()], {}

    with mock.patch.object(
        command, "resolve_data", return_value="2026-06-17"
    ), redirect_stderr(stderr):
        code, _ = _run(_args(data="2026-06-17"), events, load)

    assert code == 0
    assert "Fonte: Cache" in stderr.getvalue()
    assert "1/5 datas" in stderr.getvalue()
    assert "run" in events
