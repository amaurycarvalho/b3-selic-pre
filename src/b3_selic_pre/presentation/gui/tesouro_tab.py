"""Aba Tesouro Direto com sub-abas analíticas lazy."""

from __future__ import annotations

from typing import Any

from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.tesouro_sub_tab import TesouroSubTab
from b3_selic_pre.presentation.settings import Settings
from b3_selic_pre.presentation.tabs import LazyTabRegistry, TabSpec
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_VISAO_GERAL,
    SUB_TABS,
)

Widget = Any


class TesouroDiretoTab:
    """Controller da aba Tesouro Direto e do sub-notebook lazy."""

    def __init__(
        self: TesouroDiretoTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        settings: Settings,
        icons: dict[str, Any],
    ) -> None:
        """Create the sub-notebook and register its three lazy sub-tabs."""
        import tkinter as tk
        from tkinter import ttk

        self.frame = parent
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.deps = dependencies
        self.settings = settings
        self.icons = icons
        self._ready = False
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.registry = LazyTabRegistry()
        self._frames: dict[str, Widget] = {}
        for kind, label in SUB_TABS:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=label)
            self._frames[kind] = frame
            self.registry.register(self._spec(kind, label, frame))
        self.notebook.select(self._frames[KIND_VISAO_GERAL])
        self.notebook.bind("<<NotebookTabChanged>>", self._on_changed)

    def _spec(
        self: TesouroDiretoTab, kind: str, label: str, frame: Widget
    ) -> TabSpec:
        return TabSpec(
            kind,
            label,
            lambda: TesouroSubTab(
                frame,
                kind,
                root=self.root,
                dependencies=self.deps,
                icons=self.icons,
            ),
        )

    def on_show(self: TesouroDiretoTab) -> None:
        """Build the visible sub-tab the first time the tab is shown."""
        self._ready = True
        self._ensure_visible()

    def active_sub_id(self: TesouroDiretoTab) -> str | None:
        """Return the visible sub-tab identifier."""
        try:
            selected = self.notebook.select()
        except self.tk.TclError:
            return None
        for kind, frame in self._frames.items():
            if str(frame) == selected:
                return kind
        return None

    def _on_changed(self: TesouroDiretoTab, event: object = None) -> None:
        if not self._ready:
            return
        self._ensure_visible()

    def _ensure_visible(self: TesouroDiretoTab) -> None:
        kind = self.active_sub_id()
        if kind is None:
            return
        controller = self.registry.mark_visible(kind)
        controller.on_show()

    def close(self: TesouroDiretoTab) -> None:
        """Close built sub-tabs so pending callbacks are ignored."""
        for kind in self.registry.built_ids():
            built = self.registry.ensure_built(kind)
            built.close()
