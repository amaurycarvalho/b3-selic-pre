"""Sub-aba Dólar e Ouro e aba Câmbio e Reserva com sub-notebook lazy."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any

from b3_selic_pre.presentation.busy import BUSY_TEXT, BusyIndicator
from b3_selic_pre.presentation.charts_market import render_market
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.market_sub_tab_ui import (
    ASSET_OPTIONS,
    MarketSubTabUI,
)
from b3_selic_pre.presentation.gui.reserves_sub_tab import ReservesSubTab
from b3_selic_pre.presentation.logging_utils import log_exception_once
from b3_selic_pre.presentation.market_chart_data import build_chart_data
from b3_selic_pre.presentation.market_tab import MarketTabController
from b3_selic_pre.presentation.market_view_model import (
    MarketOptions,
    build_view_model,
)
from b3_selic_pre.presentation.tabs import LazyTabRegistry, TabSpec

Widget = Any

logger = logging.getLogger(__name__)

SUB_TABS = (
    ("dolar-ouro", "Dólar e Ouro"),
    ("reservas", "Reservas Internacionais"),
)
DEFAULT_SUB_TAB = "dolar-ouro"
class DolarOuroSubTab(MarketSubTabUI):
    """Sub-aba com controles, status, selo de defasagem e Atualizar próprio."""

    def __init__(
        self: DolarOuroSubTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        icons: dict[str, Any],
    ) -> None:
        """Build the sub-tab widgets and the headless market controller."""
        import tkinter as tk
        from tkinter import ttk

        self.frame = parent
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.icons = icons
        self._closed = False
        self._loading = False
        self._loaded = False
        self._payload: dict[str, Any] | None = None
        self._results: queue.Queue = queue.Queue()
        self._busy = BusyIndicator(root)
        self.options = MarketOptions()
        services = dependencies.market_services
        self.controller = (
            MarketTabController(services) if services is not None else None
        )
        self._build_controls()
        self._build_body()
        self._build_statusbar()

    def on_show(self: DolarOuroSubTab) -> None:
        """Load only the cache on the first display and redraw afterwards."""
        if self._closed:
            return
        self.hide_charts()
        if not self._loaded:
            self._loaded = True
            if self._start_load(cache_only=True):
                return
            self.show_charts()
            return
        if self._loading:
            self._draw()
            return
        self._busy.enter()
        try:
            self._draw()
            self.draw_idle()
        finally:
            self.show_charts()
            self._busy.leave()

    def _on_option_change(self: DolarOuroSubTab, event: object = None) -> None:
        self.options.set_ativo(
            ASSET_OPTIONS.get(self.asset_var.get(), "ambos")
        )
        self.options.base100 = self.base100_var.get()
        self.options.fibonacci = self.fibonacci_var.get()
        self._busy.enter()
        try:
            self._draw()
        finally:
            self._busy.leave()

    def _start_refresh(self: DolarOuroSubTab) -> None:
        self._start_load(cache_only=False)

    def _start_load(self: DolarOuroSubTab, cache_only: bool) -> bool:
        if self._loading or self._closed:
            return False
        if self.controller is None:
            self._apply_status(
                "Serviço de mercado indisponível nesta execução.", "error"
            )
            return False
        self._loading = True
        self.hide_charts()
        self._busy.enter()
        self.update_loading_state(True)
        self._apply_status(
            "Carregando cache..." if cache_only else "Atualizando fontes...",
            "info",
        )
        self.root.after(100, self._poll_result)
        threading.Thread(
            target=self._load_worker, args=(cache_only,), daemon=True
        ).start()
        return True

    def _load_worker(self: DolarOuroSubTab, cache_only: bool) -> None:
        payload: dict[str, Any] | None = None
        error: str | None = None
        try:
            payload = (
                self.controller.load_cache_only()  # type: ignore[union-attr]
                if cache_only
                else self.controller.refresh()  # type: ignore[union-attr]
            )
        except Exception as exc:
            log_exception_once(
                logger,
                exc,
                "Falha ao carregar a sub-aba Dólar e Ouro",
            )
            error = str(exc)
        self._results.put((payload, error))

    def _poll_result(self: DolarOuroSubTab) -> None:
        if self._closed:
            return
        try:
            payload, error = self._results.get_nowait()
        except queue.Empty:
            if self._loading:
                self.root.after(100, self._poll_result)
            return
        self._finish_load(payload, error)

    def _finish_load(
        self: DolarOuroSubTab,
        payload: dict[str, Any] | None,
        error: str | None = None,
    ) -> None:
        if self._closed:
            return
        self._loading = False
        self.update_loading_state(False)
        try:
            if payload is not None:
                self._payload = payload
            self._draw()
            self.draw_idle()
            if error:
                self._apply_status(f"Falha ao atualizar: {error}", "error")
        finally:
            self.show_charts()
            self._busy.leave()

    def _draw(self: DolarOuroSubTab) -> None:
        if self._closed or self._payload is None:
            return
        errors = tuple(self._payload.get("erros_fontes", []))
        view = build_view_model(self._payload, self.options, errors)
        self._apply_status(view.status_text, view.status_kind)
        self.stale_var.set(view.stale_badge or "")
        chart = build_chart_data(self._payload, self.options)
        self.panel.draw(render_market, chart)

    def close(self: DolarOuroSubTab) -> None:
        """Mark the sub-tab closed so late callbacks are ignored."""
        self._closed = True
        self._busy.reset()


class CambioOuroTab:
    """Aba Câmbio e Reserva com sub-notebook lazy."""

    def __init__(
        self: CambioOuroTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        icons: dict[str, Any],
    ) -> None:
        """Create the sub-notebook and register the lazy sub-tabs."""
        import tkinter as tk
        from tkinter import ttk

        self.frame = parent
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.deps = dependencies
        self.icons = icons
        self._ready = False
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.registry = LazyTabRegistry()
        self._frames: dict[str, Widget] = {}
        self._warnings: dict[str, Widget] = {}
        for sub_id, label in SUB_TABS:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=label)
            self._frames[sub_id] = frame
            self._warnings[sub_id] = ttk.Label(
                frame, text=BUSY_TEXT, anchor=tk.CENTER
            )
            self.registry.register(
                TabSpec(
                    sub_id,
                    label,
                    lambda sub_id=sub_id, frame=frame, label=label: self._build(
                        sub_id, frame, label
                    ),
                )
            )
        self.notebook.select(self._frames[DEFAULT_SUB_TAB])
        self.notebook.bind("<<NotebookTabChanged>>", self._on_changed)

    def _build(
        self: CambioOuroTab, sub_id: str, frame: Widget, label: str
    ) -> object:
        _ = label
        warning = self._warnings.pop(sub_id, None)
        if warning is not None:
            warning.place(relx=0.5, rely=0.5, anchor=self.tk.CENTER)
            warning.lift()
            frame.update_idletasks()
        try:
            if sub_id == "reservas":
                return ReservesSubTab(
                    frame,
                    root=self.root,
                    dependencies=self.deps,
                    icons=self.icons,
                )
            return DolarOuroSubTab(
                frame,
                root=self.root,
                dependencies=self.deps,
                icons=self.icons,
            )
        finally:
            if warning is not None:
                warning.place_forget()
                warning.destroy()

    def on_show(self: CambioOuroTab) -> None:
        """Build the visible sub-tab the first time the tab is shown."""
        self._ready = True
        self._ensure_visible()

    def active_sub_id(self: CambioOuroTab) -> str | None:
        """Return the visible sub-tab identifier."""
        try:
            selected = self.notebook.select()
        except self.tk.TclError:
            return None
        for sub_id, frame in self._frames.items():
            if str(frame) == selected:
                return sub_id
        return None

    def _on_changed(self: CambioOuroTab, event: object = None) -> None:
        if not self._ready:
            return
        self._ensure_visible()

    def _ensure_visible(self: CambioOuroTab) -> None:
        sub_id = self.active_sub_id()
        if sub_id is None:
            return
        controller = self.registry.mark_visible(sub_id)
        on_show = getattr(controller, "on_show", None)
        if callable(on_show):
            on_show()

    def close(self: CambioOuroTab) -> None:
        """Close built sub-tabs so pending callbacks are ignored."""
        for sub_id in self.registry.built_ids():
            controller = self.registry.ensure_built(sub_id)
            close = getattr(controller, "close", None)
            if callable(close):
                close()
