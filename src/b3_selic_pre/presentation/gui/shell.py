"""Shell de abas de nível superior da interface gráfica."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from importlib import resources  # nosemgrep
from typing import Any

from b3_selic_pre import __version__
from b3_selic_pre.presentation.gui.about_tab import AboutTab
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.selic_pre_tab import SelicPreTab
from b3_selic_pre.presentation.gui.startup import SETTLE_MS, StartupShield
from b3_selic_pre.presentation.gui.tesouro_tab import TesouroDiretoTab
from b3_selic_pre.presentation.gui.window import WindowMixin
from b3_selic_pre.presentation.settings import Settings
from b3_selic_pre.presentation.tabs import LazyTabRegistry, TabSpec

Widget = Any
TkModule = Any
TabFactory = Callable[[Widget], Any]

SELIC_TAB_ID = "selic-pre"
TESOURO_TAB_ID = "tesouro-direto"
SOBRE_TAB_ID = "sobre"


class AppShell(WindowMixin):
    """Janela principal com notebook, registro de abas e escudo inicial."""

    def __init__(
        self: AppShell,
        root: Widget,
        dependencies: GuiDependencies | None = None,
    ) -> None:
        """Compose the shell and build only the default SELIC Pré tab."""
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.deps = dependencies or GuiDependencies()
        self.settings = self.deps.settings or Settings()
        self._configure_after_id = None
        self._shell_ready = False
        self._startup_finished = False
        self._frames: dict[str, Widget] = {}
        self.selic_pre_tab: SelicPreTab | None = None
        self.tesouro_tab: TesouroDiretoTab | None = None
        self.about_tab: AboutTab | None = None
        self.registry = LazyTabRegistry()
        self._load_window_state(root)
        self._startup_shield = StartupShield(root)
        self._startup_shield.show()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._startup_shield.raise_above_siblings()
        self._register_default_tabs()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._select_default()
        self._startup_shield.raise_above_siblings()
        root.bind("<Configure>", self._on_window_configure, add="+")
        root.after(SETTLE_MS, self._finish_startup)

    def _load_window_state(self: AppShell, root: Widget) -> None:
        """Set title, icons and geometry before creating the notebook."""
        root.title(f"Taxas Referenciais SELIC (B3) v{__version__}")
        icon_path = self.deps.icon_source()
        if os.path.exists(icon_path):
            img = self.tk.PhotoImage(file=icon_path, master=root)
            self.icon_img = img
            root.iconphoto(True, img)
        self.icons = {}
        for name in [
            'document-open-recent', 'view-refresh', 'edit-copy',
            'content-loading', 'help-about',
        ]:
            if getattr(sys, 'frozen', False):
                path = os.path.join(sys._MEIPASS, f'{name}.png')
            else:
                path = str(resources.files('b3_selic_pre') / 'icons' / f'{name}.png')
            if os.path.exists(path):
                self.icons[name] = self.tk.PhotoImage(file=path, master=root)
        saved_geo = self.settings.get("window_geometry")
        saved_max = self.settings.get("window_maximized", False)
        if saved_geo:
            root.geometry(saved_geo)
            if saved_max:
                root.after(10, lambda: root.state("zoomed"))
        else:
            root.geometry("1100x660")
            root.after(10, self._center_window)

    def _register_default_tabs(self: AppShell) -> None:
        """Register SELIC Pré first and Tesouro Direto second."""
        self.register_tab(SELIC_TAB_ID, "SELIC Pré", self._build_selic_pre)
        self.register_tab(
            TESOURO_TAB_ID, "Tesouro Direto", self._build_tesouro
        )
        self.register_tab(SOBRE_TAB_ID, "Sobre", self._build_sobre)

    def register_tab(
        self: AppShell, tab_id: str, label: str, factory: TabFactory
    ) -> Widget:
        """Add a tab frame and register its lazy factory."""
        frame = self.ttk.Frame(self.notebook)
        self.notebook.add(frame, text=label)
        self._frames[tab_id] = frame
        self.registry.register(
            self._tab_spec(tab_id, label, lambda: factory(frame))
        )
        return frame

    def _tab_spec(
        self: AppShell, tab_id: str, label: str, factory: Callable[[], object]
    ) -> TabSpec:
        return TabSpec(tab_id, label, factory)

    def _build_selic_pre(self: AppShell, frame: Widget) -> SelicPreTab:
        tab = SelicPreTab(
            frame,
            root=self.root,
            dependencies=self.deps,
            settings=self.settings,
            icons=self.icons,
            is_active=lambda: self.active_tab_id() == SELIC_TAB_ID,
        )
        tab._disable_startup_controls()
        self.selic_pre_tab = tab
        return tab

    def _build_tesouro(self: AppShell, frame: Widget) -> TesouroDiretoTab:
        tab = TesouroDiretoTab(
            frame,
            root=self.root,
            dependencies=self.deps,
            settings=self.settings,
            icons=self.icons,
        )
        self.tesouro_tab = tab
        return tab

    def _build_sobre(self: AppShell, frame: Widget) -> AboutTab:
        tab = AboutTab(frame, root=self.root, dependencies=self.deps)
        self.about_tab = tab
        return tab

    def _select_default(self: AppShell) -> None:
        frame = self._frames[SELIC_TAB_ID]
        self.notebook.select(frame)
        self.registry.mark_visible(SELIC_TAB_ID)

    def active_tab_id(self: AppShell) -> str | None:
        """Return the identifier of the visible top-level tab."""
        try:
            selected = self.notebook.select()
        except self.tk.TclError:
            return None
        for tab_id, frame in self._frames.items():
            if str(frame) == selected:
                return tab_id
        return None

    def _on_tab_changed(self: AppShell, event: object = None) -> None:
        """Build the visible tab once the shell is ready."""
        if not self._shell_ready:
            return
        tab_id = self.active_tab_id()
        if tab_id is None:
            return
        controller = self.registry.mark_visible(tab_id)
        on_show = getattr(controller, "on_show", None)
        if callable(on_show):
            on_show()

    def _finish_startup(self: AppShell) -> None:
        """Remove the shield and enable tab switching and shortcuts."""
        if self._startup_finished:
            return
        self._startup_finished = True
        shield = self._startup_shield
        self._startup_shield = None
        if not self._root_alive():
            return
        if shield is not None:
            shield.destroy()
        if self.selic_pre_tab is not None:
            self.selic_pre_tab.finish_startup()
        self._shell_ready = True

    def _root_alive(self: AppShell) -> bool:
        """Return whether the root window still exists."""
        try:
            return bool(self.root.winfo_exists())
        except (self.tk.TclError, RuntimeError):
            return False
