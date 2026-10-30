"""Sub-aba Reservas Internacionais com carregamento lazy e Atualizar próprio."""

from __future__ import annotations

import queue
import threading
from typing import Any

from b3_selic_pre.presentation.charts_reserves import render_reserves
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.market_chart_panel import MarketChartPanel
from b3_selic_pre.presentation.gui.market_sub_tab_ui import STATUS_COLORS
from b3_selic_pre.presentation.gui.reserves_orientation import (
    build_reserves_orientation,
)
from b3_selic_pre.presentation.gui.tooltip import Tooltip
from b3_selic_pre.presentation.reserves_chart_data import build_chart_data
from b3_selic_pre.presentation.reserves_tab import ReservesTabController
from b3_selic_pre.presentation.reserves_view_model import (
    ReservesOptions,
    build_view_model,
)

Widget = Any
JANELA_OPTIONS = {"12 meses": "12m", "3 anos": "3a"}


class ReservesSubTab:
    """Sub-aba com janela, status, selo de regime e Atualizar próprio."""

    def __init__(
        self: ReservesSubTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        icons: dict[str, Any],
    ) -> None:
        """Build the sub-tab widgets and the headless reserves controller."""
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
        self.options = ReservesOptions()
        services = dependencies.reserves_services
        self.controller = (
            ReservesTabController(services) if services is not None else None
        )
        self._build_controls()
        self._build_body()
        self._build_statusbar()

    def _build_controls(self: ReservesSubTab) -> None:
        tk, ttk = self.tk, self.ttk
        frame = ttk.Frame(self.frame, padding=(8, 6))
        frame.pack(fill=tk.X)
        ttk.Label(frame, text="Janela:").pack(side=tk.LEFT)
        self.window_var = tk.StringVar(value="12 meses")
        self.window_combo = ttk.Combobox(
            frame,
            textvariable=self.window_var,
            values=tuple(JANELA_OPTIONS),
            state="readonly",
            width=10,
        )
        self.window_combo.pack(side=tk.LEFT, padx=(4, 8))
        self.window_combo.bind("<<ComboboxSelected>>", self._on_option_change)
        self._refresh_image = self.icons.get("view-refresh")
        self.refresh_button = ttk.Button(
            frame,
            image=self._refresh_image if self._refresh_image else "",
            text="" if self._refresh_image else "Atualizar",
            command=self._start_refresh,
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 12))
        self.stale_var = tk.StringVar(value="")
        self.stale_label = ttk.Label(
            frame, textvariable=self.stale_var, foreground="orange"
        )
        self.stale_label.pack(side=tk.LEFT, padx=(0, 12))
        self.regime_var = tk.StringVar(value="")
        self.regime_label = ttk.Label(
            frame, textvariable=self.regime_var, foreground="#1f4e79"
        )
        self.regime_label.pack(side=tk.LEFT)
        Tooltip(
            self.window_combo,
            "Seleciona a janela de 12 meses ou 3 anos",
        )
        Tooltip(
            self.refresh_button,
            "Atualiza a série de reservas internacionais do BCB",
        )

    def _build_body(self: ReservesSubTab) -> None:
        tk, ttk = self.tk, self.ttk
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self.paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        charts = ttk.Frame(self.paned)
        self.paned.add(charts, weight=4)
        self.panel = MarketChartPanel(
            charts, icons=self.icons, on_status=self._apply_status
        )
        self.panel.frame.pack(fill=tk.BOTH, expand=True)
        orientation = build_reserves_orientation(self.paned, tk, ttk)
        self.paned.add(orientation, weight=1)

    def _build_statusbar(self: ReservesSubTab) -> None:
        tk, ttk = self.tk, self.ttk
        statusbar = ttk.Frame(self.frame, padding=(8, 2, 8, 4))
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).pack(
            side=tk.BOTTOM, fill=tk.X
        )
        row = ttk.Frame(statusbar)
        row.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(
            row, textvariable=self.status_var, anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress = ttk.Progressbar(
            row, mode="indeterminate", length=140
        )

    def on_show(self: ReservesSubTab) -> None:
        """Load only the cache on first display and redraw afterwards."""
        if self._closed:
            return
        if not self._loaded:
            self._loaded = True
            self._start_load(cache_only=True)
            return
        self._draw()

    def _on_option_change(self: ReservesSubTab, event: object = None) -> None:
        self.options.set_janela(
            JANELA_OPTIONS.get(self.window_var.get(), "12m")
        )
        self._draw()

    def _start_refresh(self: ReservesSubTab) -> None:
        self._start_load(cache_only=False)

    def _start_load(self: ReservesSubTab, cache_only: bool) -> None:
        if self._loading or self._closed:
            return
        if self.controller is None:
            self._apply_status(
                "Serviço de reservas indisponível nesta execução.", "error"
            )
            return
        self._loading = True
        self.update_loading_state(True)
        self._apply_status(
            "Carregando cache..." if cache_only else "Atualizando reservas...",
            "info",
        )
        self.root.after(100, self._poll_result)
        threading.Thread(
            target=self._load_worker, args=(cache_only,), daemon=True
        ).start()

    def _load_worker(self: ReservesSubTab, cache_only: bool) -> None:
        payload: dict[str, Any] | None = None
        error: str | None = None
        try:
            payload = (
                self.controller.load_cache_only()  # type: ignore[union-attr]
                if cache_only
                else self.controller.refresh()  # type: ignore[union-attr]
            )
        except Exception as exc:
            error = str(exc)
        self._results.put((payload, error))

    def _poll_result(self: ReservesSubTab) -> None:
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
        self: ReservesSubTab,
        payload: dict[str, Any] | None,
        error: str | None = None,
    ) -> None:
        if self._closed:
            return
        self._loading = False
        self.update_loading_state(False)
        if payload is not None:
            self._payload = payload
        self._draw()
        if error:
            self._apply_status(f"Falha ao atualizar: {error}", "error")

    def _draw(self: ReservesSubTab) -> None:
        if self._closed or self._payload is None:
            return
        errors = tuple(self._payload.get("erros_fontes", []))
        calendar = (
            getattr(self.controller.services, "calendar", None)
            if self.controller is not None
            else None
        )
        view = build_view_model(
            self._payload, self.options, errors, calendar=calendar
        )
        self._apply_status(view.status_text, view.status_kind)
        self.stale_var.set(view.stale_badge or "")
        self.regime_var.set(view.regime_badge or "")
        chart = build_chart_data(
            self._payload, self.options, calendar=calendar
        )
        self.panel.draw(render_reserves, chart)

    def update_loading_state(self: ReservesSubTab, loading: bool) -> None:
        """Enable/disable controls and animate the statusbar progress."""
        state = self.tk.DISABLED if loading else self.tk.NORMAL
        self.refresh_button.configure(state=state)
        self.window_combo.configure(
            state="disabled" if loading else "readonly"
        )
        image_name = "content-loading" if loading else "view-refresh"
        image = self.icons.get(image_name)
        if image is not None:
            self.refresh_button.configure(image=image, text="")
        if loading:
            self.progress.pack(side=self.tk.RIGHT, padx=(8, 0))
            self.progress.start()
        elif self.progress.winfo_manager():
            self.progress.stop()
            self.progress.pack_forget()

    def _apply_status(
        self: ReservesSubTab, message: str, kind: str
    ) -> None:
        self.status_var.set(message)
        self.status_label.configure(
            foreground=STATUS_COLORS.get(kind, "")
        )

    def close(self: ReservesSubTab) -> None:
        """Mark the sub-tab closed so late callbacks are ignored."""
        self._closed = True


__all__ = ["JANELA_OPTIONS", "ReservesSubTab"]
