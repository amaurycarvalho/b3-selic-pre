import importlib.resources as resources
import os
import shutil
import subprocess
import sys

from b3_selic_pre.domain.constants import SHORTCUT_CHECK_PATH


def _detect_desktop_dir():
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if path:
                return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    user_dirs = os.path.expanduser("~/.config/user-dirs.dirs")
    if os.path.isfile(user_dirs):
        for line in open(user_dirs):
            if line.startswith("XDG_DESKTOP_DIR="):
                raw = line.split("=", 1)[1].strip().strip('"')
                path = os.path.expandvars(raw)
                if path:
                    return path
    return os.path.expanduser("~/Desktop")


def _resolve_executable():
    if getattr(sys, "frozen", False):
        return sys.executable
    script = os.path.abspath(sys.argv[0])
    return f"{sys.executable} {script}"


def _icon_source():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "b3_selic_pre.png")
    return str(resources.files("b3_selic_pre") / "icons" / "b3_selic_pre.png")


def shortcut_exists():
    return os.path.isfile(SHORTCUT_CHECK_PATH)


def create_shortcut():
    exec_line = _resolve_executable() + " --gui"
    icon_src = _icon_source()
    desktop_dir = _detect_desktop_dir()
    icons_dst = os.path.expanduser("~/.local/share/icons")
    os.makedirs(icons_dst, exist_ok=True)
    if os.path.isfile(icon_src):
        shutil.copy2(icon_src, os.path.join(icons_dst, "b3-selic-pre.png"))
    icon_path = os.path.join(icons_dst, "b3-selic-pre.png")
    content = (
        "[Desktop Entry]\n"
        f"Name=Taxas Referenciais SELIC (B3)\n"
        "Comment=Consulta taxas referenciais SELIC Pré na B3\n"
        f"Exec={exec_line}\n"
        f"Icon={icon_path}\n"
        "Terminal=false\n"
        "Type=Application\n"
        "Categories=Finance;Office;\n"
        "StartupNotify=true\n"
    )
    dests = [
        os.path.join(desktop_dir, "b3-selic-pre.desktop"),
        os.path.expanduser("~/.local/share/applications/b3-selic-pre.desktop"),
    ]
    for path in dests:
        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        os.chmod(path, 0o755)
