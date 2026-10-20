"""Dependências injetáveis da interface gráfica."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from b3_selic_pre.presentation.settings import Settings


def _default_shortcut_exists() -> bool:
    return True


def _noop() -> None:
    return None


def _no_icon() -> str:
    return ""


def _no_open_url(url: str) -> bool:
    return False


def _no_open_directory(path: str) -> bool:
    return False


def _no_log_directory() -> str:
    return ""


def _no_latest_version() -> str | None:
    return None


@dataclass
class GuiDependencies:
    """Adapters e serviços usados pela interface gráfica."""

    client: Any = None
    shortcut_exists: Callable[[], bool] = _default_shortcut_exists
    create_shortcut: Callable[[], None] = _noop
    icon_source: Callable[[], str] = _no_icon
    settings: Settings | None = None
    open_url: Callable[[str], bool] = _no_open_url
    open_directory: Callable[[str], bool] = _no_open_directory
    log_directory: Callable[[], str] = _no_log_directory
    latest_version: Callable[[], str | None] = _no_latest_version
