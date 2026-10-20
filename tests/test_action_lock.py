import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

from b3_selic_pre.infrastructure.action_lock import (
    ActionLock,
    ActionLockTimeout,
    action_lock,
)


def test_acquire_and_release():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "action.lock"
        with ActionLock(path=path, timeout=1):
            assert path.exists()
        with ActionLock(path=path, timeout=1):
            pass


def test_on_wait_is_called_when_lock_is_held():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "action.lock"
        waited = []
        real_try_lock = ActionLock._try_lock
        state = {"first": True}

        def fake_try_lock(self):
            if state["first"]:
                state["first"] = False
                raise OSError("busy")
            return real_try_lock(self)

        with mock.patch.object(ActionLock, "_try_lock", fake_try_lock):
            with ActionLock(
                path=path,
                timeout=1,
                poll=0.01,
                on_wait=lambda: waited.append(True),
            ):
                pass
        assert waited == [True]


def test_timeout_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "action.lock"
        with mock.patch.object(
            ActionLock, "_try_lock", side_effect=OSError("busy")
        ), mock.patch(
            "b3_selic_pre.infrastructure.action_lock.time.monotonic",
            side_effect=[0.0, 0.0, 10.0],
        ), mock.patch(
            "b3_selic_pre.infrastructure.action_lock.time.sleep"
        ):
            with pytest.raises(ActionLockTimeout):
                with ActionLock(path=path, timeout=0.5):
                    pass


def test_action_lock_helper():
    with tempfile.TemporaryDirectory() as tmp:
        lock = action_lock(path=Path(tmp) / "action.lock", timeout=1)
        assert isinstance(lock, ActionLock)
        with lock:
            pass


def test_lock_file_is_created_under_missing_parent():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nested" / "action.lock"
        with ActionLock(path=path, timeout=1):
            pass
        assert path.exists()
        time.sleep(0)
