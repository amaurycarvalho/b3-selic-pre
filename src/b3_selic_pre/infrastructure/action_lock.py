"""Cross-process action lock used by data update and MCP preparation."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from types import TracebackType

from b3_selic_pre.infrastructure.xdg import cache_base

DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_POLL_SECONDS = 0.1


class ActionLockTimeout(TimeoutError):
    """Raised when the action lock could not be acquired in time."""


def default_lock_path() -> Path:
    """Return the default lock path under the application cache directory."""
    return cache_base() / "b3-selic-pre" / "action.lock"


class ActionLock:
    """Exclusive lock backed by a file descriptor.

    On POSIX the implementation uses ``fcntl.flock``. On Windows it uses
    ``msvcrt.locking``. The lock is released by the context manager.
    """

    def __init__(
        self: ActionLock,
        path: str | Path | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        poll: float = DEFAULT_POLL_SECONDS,
        on_wait: Callable[[], None] | None = None,
    ) -> None:
        """Crie um lock de ação para o caminho e timeout informados."""
        self.path = Path(path) if path else default_lock_path()
        self.timeout = timeout
        self.poll = poll
        self.on_wait = on_wait
        self._handle = None

    def __enter__(self: ActionLock) -> ActionLock:  # noqa: PYI034
        """Adquira o lock e devolva o context manager."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+b")
        self._acquire()
        return self

    def __exit__(
        self: ActionLock,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Libere o lock ao sair do context manager."""
        self._release()

    def _acquire(self: ActionLock) -> None:
        deadline = time.monotonic() + self.timeout
        waited = False
        while True:
            try:
                self._try_lock()
                return
            except OSError as exc:
                if time.monotonic() >= deadline:
                    self._release()
                    raise ActionLockTimeout(
                        f"Não foi possível obter o lock de ação em {self.path} "
                        f"após {self.timeout:.0f}s."
                    ) from exc
                if not waited and self.on_wait is not None:
                    self.on_wait()
                    waited = True
                time.sleep(self.poll)

    def _try_lock(self: ActionLock) -> None:
        if os.name == "nt":
            import msvcrt

            self._handle.seek(0)
            if self._handle.read(1) == b"":
                self._handle.write(b"0")
                self._handle.flush()
            self._handle.seek(0)
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            return
        import fcntl

        fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _release(self: ActionLock) -> None:
        handle = self._handle
        if handle is None:
            return
        self._handle = None
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            handle.close()


def action_lock(
    path: str | Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    poll: float = DEFAULT_POLL_SECONDS,
    on_wait: Callable[[], None] | None = None,
) -> ActionLock:
    """Return an :class:`ActionLock` context manager."""
    return ActionLock(path=path, timeout=timeout, poll=poll, on_wait=on_wait)
