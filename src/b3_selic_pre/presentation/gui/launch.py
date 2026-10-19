"""Composition root da interface gráfica desktop."""

from __future__ import annotations

from b3_selic_pre.infrastructure.cached_client import CachedB3Client
from b3_selic_pre.infrastructure.desktop import (
    _icon_source,
    create_shortcut,
    shortcut_exists,
)
from b3_selic_pre.presentation.gui.app import SelicPreApp
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.settings import Settings


def launch_gui() -> None:
    """Inicia a janela principal montando os adapters de infraestrutura."""
    import tkinter as tk

    root = tk.Tk()
    dependencies = GuiDependencies(
        client=CachedB3Client(),
        shortcut_exists=shortcut_exists,
        create_shortcut=create_shortcut,
        icon_source=_icon_source,
        settings=Settings(),
    )
    app = SelicPreApp(root, dependencies)

    def on_closing() -> None:
        app._save_window_state()
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
