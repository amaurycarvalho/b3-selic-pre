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


@dataclass
class GuiDependencies:
    """Adapters e serviços usados pela interface gráfica."""

    client: Any = None
    shortcut_exists: Callable[[], bool] = _default_shortcut_exists
    create_shortcut: Callable[[], None] = _noop
    icon_source: Callable[[], str] = _no_icon
    settings: Settings | None = None
