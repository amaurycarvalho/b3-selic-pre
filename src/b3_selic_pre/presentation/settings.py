"""Persistent application settings backed by a JSON file.

The settings file lives in a platform-appropriate config directory
and is loaded on construction and written back on every mutation.
"""

from __future__ import annotations

import json
import os
import platform
import uuid
from pathlib import Path

DEFAULT_LOG_RETENTION_DAYS = 7

DEFAULT_SETTINGS = {
    "last_date": "",
    "data_referencia": "",
    "view_mode": "raw",
    "log_retention_days": DEFAULT_LOG_RETENTION_DAYS,
    "evolution": False,
    "show_3d": False,
    "sidebar": False,
    "curva_juros": {
        "expected_inflation": 3.0,
        "faixas_nominais": [6.0, 9.0, 11.0, 13.0],
        "faixas_juro_real": [2.0, 4.0, 6.0],
        "stability_window": 4,
        "stability_fallback": "default",
        "default_mean_deviation_bps": 15.0,
        "faixas_estabilidade": [5.0, 10.0, 20.0, 35.0],
    },
    "curva_evolucao": {
        "steepening_fallback": "unavailable",
        "estimated_delta_slope_bps": 15.0,
        "movement_threshold_bps": 5.0,
        "steepening_threshold_bps": 5.0,
        "steepening_small_bps": 10.0,
        "steepening_medium_bps": 20.0,
        "steepening_large_bps": 40.0,
    },
}

FIRST_RUN_DEFAULTS = {
    "view_mode": "consolidated",
    "evolution": True,
    "sidebar": True,
}


def _xdg_path() -> Path:
    app = "b3-selic-pre"
    system = platform.system()
    if system == "Linux":
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    elif system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / app / "settings.json"


class Settings:
    """Loads and persists application settings in a JSON file."""

    def __init__(self: Settings, path: str | None = None) -> None:
        """Initialize settings, optionally pointing to a custom file."""
        self.path = path or _xdg_path()
        self.is_first_run = not self.path.exists()
        self._data = dict(DEFAULT_SETTINGS)
        if self.is_first_run:
            self._data.update(FIRST_RUN_DEFAULTS)
        self._load()

    def _load(self: Settings) -> None:
        try:
            if self.path.exists():
                raw = self.path.read_text(encoding="utf-8")
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    self._data.update(loaded)
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self: Settings) -> None:
        tmp_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_name(
                f".{self.path.name}.{uuid.uuid4().hex}.tmp"
            )
            tmp_path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp_path, self.path)
        except OSError:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def get(self: Settings, key: str, default: object = None) -> object:
        """Return the value for ``key`` or ``default`` if absent."""
        return self._data.get(key, default)

    def log_retention_days(self: Settings) -> int:
        """Return the validated log retention period in days."""
        value = self.get("log_retention_days", DEFAULT_LOG_RETENTION_DAYS)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            return DEFAULT_LOG_RETENTION_DAYS
        return value

    def set(self: Settings, key: str, value: object) -> None:
        """Store ``value`` under ``key`` and persist the settings file."""
        self._data[key] = value
        self._save()

    def __getitem__(self: Settings, key: str) -> object:
        """Return the value for ``key``, raising KeyError if absent."""
        return self._data[key]

    def __setitem__(self: Settings, key: str, value: object) -> None:
        """Store ``value`` under ``key`` via ``set``."""
        self.set(key, value)
