"""Sub-aba analítica do Tesouro Direto com dois gráficos independentes."""

from __future__ import annotations

import logging
from typing import Any

from b3_selic_pre.presentation.busy import BusyIndicator
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.tesouro_sub_tab_ui import SubTabUI
from b3_selic_pre.presentation.logging_utils import log_exception_once
from b3_selic_pre.presentation.tesouro_analise_controller import (
    TesouroAnaliseController,
)
from b3_selic_pre.presentation.tesouro_loaders import (
    cache_available,
    make_loader,
)
from b3_selic_pre.presentation.tesouro_series_loader import series_available

Widget = Any

logger = logging.getLogger(__name__)


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
        self._busy = BusyIndicator(root)
        factory = dependencies.tesouro_provider_factory
        self._client = dependencies.tesouro_client
        self._series_cache = dependencies.tesouro_series_cache
        self._precompute = dependencies.tesouro_precompute
        self._btd_client = dependencies.tesouro_btd
        self.controller = TesouroAnaliseController(
            kind=kind,
            loader=make_loader(
                self._client,
                kind,
                series_cache=self._series_cache,
                precompute=self._precompute,
                btd_client=self._btd_client,
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
        present = cache_available(
            self._client, self.kind, self._btd_client
        ) or series_available(self._series_cache, self.kind)
        self.hide_charts()
        started = False
        if not self._cache_loaded:
            self._cache_loaded = True
            self.controller.note_cache_presence(present)
            started = self._start_load(cache_only=True)
        elif (
            not self.controller.has_data
            and self.controller.note_cache_presence(present)
        ):
            started = self._start_load(cache_only=True)
        if started or self._loading:
            self._draw()
            return
        self._busy.enter()
        try:
            self._draw()
            self.draw_idle()
        finally:
            self.show_charts()
            self._busy.leave()

    def _on_window_change(self: TesouroSubTab, event: object = None) -> None:
        if self._closed:
            return
        try:
            self.controller.set_window(self.window_var.get())
        except ValueError:
            return
        self._busy.enter()
        try:
            self._draw()
        finally:
            self._busy.leave()

    def _start_refresh(self: TesouroSubTab, force: bool) -> None:
        ignore_cache = force or self.ignore_cache_var.get()
        self._start_load(force=ignore_cache)

    def _load_worker(
        self: TesouroSubTab, cache_only: bool, force: bool
    ) -> None:
        data = None
        try:
            data = self.controller.load(
                cache_only=cache_only,
                force=force,
                stage_callback=self._on_stage,
            )
        except Exception as exc:
            log_exception_once(
                logger,
                exc,
                "Falha ao carregar a sub-aba do Tesouro Direto "
                f"({self.kind})",
            )
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
        if self._closed:
            return
        if not self._root_alive():
            self._busy.reset()
            return
        self._loading = False
        self.controller.loading = False
        self.controller.loading_stage = None
        self.update_loading_state(False)
        try:
            self._draw()
            self.draw_idle()
        finally:
            self.show_charts()
            self._busy.leave()

    def _draw(self: TesouroSubTab) -> None:
        if self._closed:
            return
        view_model = self.controller.view_model()
        self.draw_current(view_model)
        self.draw_evolution(view_model)
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

    def _root_alive(self: TesouroSubTab) -> bool:
        try:
            return bool(self.root.winfo_exists())
        except (self.tk.TclError, RuntimeError):
            return False

    def close(self: TesouroSubTab) -> None:
        """Mark the sub-tab closed so late callbacks are ignored."""
        self._closed = True
        self._busy.reset()
