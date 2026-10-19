"""Resolução de diretórios base compatíveis com XDG e com cada plataforma."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def cache_base() -> Path:
    """Return the platform cache directory, following XDG conventions."""
    system = platform.system()
    if system == "Linux":
        return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    if system == "Darwin":
        return Path.home() / "Library" / "Caches"
    return Path.home() / ".cache"
