import json
import os
import platform
from pathlib import Path


DEFAULT_SETTINGS = {
    "last_date": "",
    "view_mode": "raw",
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


def _xdg_path():
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
    def __init__(self, path=None):
        self.path = path or _xdg_path()
        self._data = dict(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                raw = self.path.read_text(encoding="utf-8")
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    self._data.update(loaded)
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self._save()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self.set(key, value)
