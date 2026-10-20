"""Abertura de URLs e diretórios nos aplicativos padrão do sistema."""

from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
from pathlib import Path


def open_url(url: str) -> bool:
    """Open a URL in the default browser and report whether it was opened."""
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False


def open_directory(path: str | Path) -> bool:
    """Open an existing directory in the platform file manager."""
    target = str(path)
    if not os.path.isdir(target):
        return False
    try:
        if platform.system() == "Windows":
            os.startfile(target)  # type: ignore[attr-defined]
            return True
        command = (
            ["open", target]
            if platform.system() == "Darwin"
            else ["xdg-open", target]
        )
        result = subprocess.run(command, check=False)
        return result.returncode == 0
    except (OSError, AttributeError):
        return False
