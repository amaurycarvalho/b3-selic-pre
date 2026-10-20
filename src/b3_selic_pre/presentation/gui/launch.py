"""Composition root da interface gráfica desktop."""

from __future__ import annotations

import logging

from b3_selic_pre import __version__
from b3_selic_pre.infrastructure.cached_client import CachedB3Client
from b3_selic_pre.infrastructure.desktop import (
    _icon_source,
    create_shortcut,
    shortcut_exists,
)
from b3_selic_pre.infrastructure.links import open_directory, open_url
from b3_selic_pre.infrastructure.logging_setup import configure_logging, log_dir
from b3_selic_pre.infrastructure.release_check import fetch_latest_version
from b3_selic_pre.presentation.gui.app import SelicPreApp
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.logging_utils import (
    install_exception_hooks,
    install_tk_exception_hook,
)
from b3_selic_pre.presentation.settings import Settings


def launch_gui() -> None:
    """Inicia a janela principal montando os adapters de infraestrutura."""
    import tkinter as tk

    settings = Settings()
    active_log = configure_logging(
        retention_days=settings.log_retention_days()
    )
    logger = logging.getLogger(__name__)
    install_exception_hooks(logger)
    if active_log is not None:
        logger.info(
            "Iniciando b3-selic-pre %s (GUI); log em %s",
            __version__,
            active_log,
        )
    else:
        logger.info("Iniciando b3-selic-pre %s (GUI)", __version__)
    root = tk.Tk()
    install_tk_exception_hook(root, logger)
    dependencies = GuiDependencies(
        client=CachedB3Client(),
        shortcut_exists=shortcut_exists,
        create_shortcut=create_shortcut,
        icon_source=_icon_source,
        settings=settings,
        open_url=open_url,
        open_directory=open_directory,
        log_directory=lambda: str(log_dir()),
        latest_version=fetch_latest_version,
    )
    app = SelicPreApp(root, dependencies)

    def on_closing() -> None:
        app._save_window_state()
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
