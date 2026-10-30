"""Sub-aba analítica do Tesouro Direto com dois gráficos independentes."""

from __future__ import annotations

import threading
from typing import Any

from b3_selic_pre.presentation.charts_tesouro import (
    render_current_comparison,
    render_current_share,
    render_evolution,
    render_gap,
)
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.tesouro_sub_tab_ui import SubTabUI
from b3_selic_pre.presentation.tesouro_analise_controller import (
    TesouroAnaliseController,
)
from b3_selic_pre.presentation.tesouro_analise_view_model import (
    TesouroAnaliseViewModel,
)
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_VISAO_GERAL,
    SUB_TABS,
    ComparisonChart,
    GapChart,
)
from b3_selic_pre.presentation.tesouro_loaders import (
    cache_available,
    make_loader,
)
from b3_selic_pre.presentation.tesouro_series_loader import series_available

Widget = Any


class TesouroSubTab(SubTabUI):
    """Sub-aba com dois gráficos, seletor de janela e atualização própria."""

    def __init__(
        self: TesouroSubTab,
        parent: Widget,
        kind: str,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        icons: dict[str, Any],
    ) -> None:
        """Build the sub-tab widgets and its headless controller."""
        import tkinter as tk
        from tkinter import ttk

        self.frame = parent
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.icons = icons
        self.kind = kind
        self._closed = False
        self._loading = False
        self._cache_loaded = False
        factory = dependencies.tesouro_provider_factory
        self._client = dependencies.tesouro_client
        self._series_cache = dependencies.tesouro_series_cache
        self._precompute = dependencies.tesouro_precompute
        self.controller = TesouroAnaliseController(
            kind=kind,
            loader=make_loader(
                self._client,
                kind,
                series_cache=self._series_cache,
                precompute=self._precompute,
            ),
            **({"provider_factory": factory} if factory is not None else {}),
        )
        self.build_controls()
        self.build_statusbar()
        self.build_body()

    def on_show(self: TesouroSubTab) -> None:
        """Load cache once, off the UI thread, when the sub-tab is visible."""
        if self._closed:
            return
        if not self._cache_loaded:
            self._cache_loaded = True
            self.controller.cache_available = cache_available(
                self._client, self.kind
            ) or series_available(self._series_cache, self.kind)
            self._start_load(cache_only=True)
            self._draw()
            return
        self._draw()

    def _on_window_change(self: TesouroSubTab, event: object = None) -> None:
        if self._closed:
            return
        try:
            self.controller.set_window(self.window_var.get())
        except ValueError:
            return
        self._draw()

    def _start_refresh(self: TesouroSubTab, force: bool) -> None:
        ignore_cache = force or self.ignore_cache_var.get()
        self._start_load(force=ignore_cache)

    def _start_load(
        self: TesouroSubTab,
        *,
        cache_only: bool = False,
        force: bool = False,
    ) -> None:
        if self._loading or self._closed:
            return
        self._loading = True
        self.controller.loading = True
        self.update_loading_state(True)
        view_model = self.controller.view_model()
        self.apply_status(view_model.status_text, view_model.status_kind)
        threading.Thread(
            target=self._load_worker,
            args=(cache_only, force),
            daemon=True,
        ).start()

    def _load_worker(
        self: TesouroSubTab, cache_only: bool, force: bool
    ) -> None:
        data = None
        try:
            data = self.controller.load(
                cache_only=cache_only, force=force
            )
        except Exception:
            pass
        try:
            self.root.after(0, self._finish_load)
        except Exception:
            return
        if (
            not cache_only
            and data is not None
            and self._precompute is not None
        ):
            try:
                self._precompute(self.kind, data)
            except Exception:
                return

    def _finish_load(self: TesouroSubTab) -> None:
        if self._closed or not self._root_alive():
            return
        self._loading = False
        self.controller.loading = False
        self.update_loading_state(False)
        self._draw()

    def _draw(self: TesouroSubTab) -> None:
        if self._closed:
            return
        view_model = self.controller.view_model()
        self._draw_current(view_model)
        self._draw_evolution(view_model)
        self.apply_status(view_model.status_text, view_model.status_kind)
        self.detail_var.set(view_model.fluxo_liquido or "")
        self.window_var.set(view_model.window)
        self.refresh_button.configure(
            state=(
                self.tk.DISABLED
                if not view_model.can_refresh
                else self.tk.NORMAL
            )
        )

    def _draw_current(
        self: TesouroSubTab, view_model: TesouroAnaliseViewModel
    ) -> None:
        current = view_model.current_chart()
        if current is None:
            _draw_empty(
                self.current_panel.figure,
                f"{self._title()}",
                view_model.placeholder_message or view_model.empty_message,
            )
            self.current_panel.canvas.draw_idle()
        elif isinstance(current, ComparisonChart):
            self.current_panel.draw(render_current_comparison, current)
        else:
            self.current_panel.draw(render_current_share, current)

    def _draw_evolution(
        self: TesouroSubTab, view_model: TesouroAnaliseViewModel
    ) -> None:
        evolution = view_model.evolution_chart()
        if evolution is None:
            _draw_empty(
                self.evolution_panel.figure,
                f"{self._title()} — evolução",
                view_model.placeholder_message or view_model.empty_message,
                ylabel="p.p." if self.kind == KIND_VISAO_GERAL else "%",
            )
            self.evolution_panel.canvas.draw_idle()
        elif isinstance(evolution, GapChart):
            self.evolution_panel.draw(render_gap, evolution)
        else:
            self.evolution_panel.draw(render_evolution, evolution)

    def _title(self: TesouroSubTab) -> str:
        for kind, label in SUB_TABS:
            if kind == self.kind:
                return label
        return self.kind

    def _root_alive(self: TesouroSubTab) -> bool:
        try:
            return bool(self.root.winfo_exists())
        except (self.tk.TclError, RuntimeError):
            return False

    def close(self: TesouroSubTab) -> None:
        """Mark the sub-tab closed so late callbacks are ignored."""
        self._closed = True


def _draw_empty(
    figure: Widget, title: str, message: str, ylabel: str = "%"
) -> None:
    figure.clf()
    ax = figure.add_subplot(111)
    ax.text(
        0.5, 0.5, message, ha="center", va="center",
        transform=ax.transAxes, fontsize=12, color="gray",
    )
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 100)
