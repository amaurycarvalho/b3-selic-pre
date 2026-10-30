"""Construção dos controles, painéis e statusbar de uma sub-aba."""

from __future__ import annotations

import threading
from typing import Any

from b3_selic_pre.presentation.gui.tesouro_chart_panel import ChartPanel
from b3_selic_pre.presentation.gui.tesouro_orientation import build_orientation
from b3_selic_pre.presentation.gui.tooltip import Tooltip

Widget = Any

_STATUS_COLORS = {
    "info": "",
    "success": "green",
    "warning": "orange",
    "error": "red",
}


class SubTabUI:
    """Métodos de layout usados por ``TesouroSubTab``."""

    def build_controls(self: SubTabUI) -> None:
        """Build the window selector, refresh button and cache checkbox."""
        tk, ttk = self.tk, self.ttk  # type: ignore[attr-defined]
        frame = ttk.Frame(self.frame, padding=(8, 6))  # type: ignore[attr-defined]
        frame.pack(fill=tk.X)
        ttk.Label(frame, text="Janela:").pack(side=tk.LEFT)
        self.window_var = tk.StringVar(  # type: ignore[attr-defined]
            value=self.controller.window  # type: ignore[attr-defined]
        )
        self.window_combo = ttk.Combobox(  # type: ignore[attr-defined]
            frame,
            textvariable=self.window_var,  # type: ignore[attr-defined]
            values=(
                self.controller.view_model().window_options  # type: ignore[attr-defined]
            ),
            state="readonly",
            width=8,
        )
        self.window_combo.pack(side=tk.LEFT, padx=(4, 12))  # type: ignore[attr-defined]
        self.window_combo.bind(  # type: ignore[attr-defined]
            "<<ComboboxSelected>>", self._on_window_change  # type: ignore[attr-defined]
        )
        self._refresh_image = (  # type: ignore[attr-defined]
            self.icons.get('view-refresh')  # type: ignore[attr-defined]
        )
        self.refresh_button = ttk.Button(  # type: ignore[attr-defined]
            frame,
            image=(
                self._refresh_image  # type: ignore[attr-defined]
                if self._refresh_image is not None  # type: ignore[attr-defined]
                else ""
            ),
            text=(
                ""
                if self._refresh_image is not None  # type: ignore[attr-defined]
                else "Atualizar"
            ),
            command=lambda: self._start_refresh(False),  # type: ignore[attr-defined]
        )
        self.refresh_button.pack(side=tk.LEFT)  # type: ignore[attr-defined]
        self.ignore_cache_var = tk.BooleanVar(  # type: ignore[attr-defined]
            value=False
        )
        self.ignore_cache_cb = ttk.Checkbutton(  # type: ignore[attr-defined]
            frame,
            text="Ignorar cache",
            variable=self.ignore_cache_var,  # type: ignore[attr-defined]
        )
        self.ignore_cache_cb.pack(side=tk.LEFT, padx=(8, 0))  # type: ignore[attr-defined]
        self.detail_var = tk.StringVar(value="")  # type: ignore[attr-defined]
        self.detail_label = ttk.Label(  # type: ignore[attr-defined]
            frame,
            textvariable=self.detail_var,  # type: ignore[attr-defined]
            anchor=tk.W,
        )
        self.detail_label.pack(  # type: ignore[attr-defined]
            side=tk.LEFT, padx=(12, 0), fill=tk.X, expand=True
        )
        Tooltip(
            self.window_combo,  # type: ignore[attr-defined]
            "Janela de análise ancorada na maior data disponível",
        )
        Tooltip(
            self.refresh_button,  # type: ignore[attr-defined]
            "Atualiza os dados desta sub-aba",
        )
        Tooltip(
            self.ignore_cache_cb,  # type: ignore[attr-defined]
            "Força uma verificação condicional; 304 reutiliza o cache",
        )

    def build_body(self: SubTabUI) -> None:
        """Build the separator, split pane, charts and orientation text."""
        tk, ttk = self.tk, self.ttk  # type: ignore[attr-defined]
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).pack(  # type: ignore[attr-defined]
            fill=tk.X, pady=(4, 0)
        )
        self.paned = ttk.PanedWindow(  # type: ignore[attr-defined]
            self.frame, orient=tk.HORIZONTAL  # type: ignore[attr-defined]
        )
        self.paned.pack(  # type: ignore[attr-defined]
            fill=tk.BOTH, expand=True, padx=8, pady=6
        )
        charts = ttk.Frame(self.paned)  # type: ignore[attr-defined]
        self.paned.add(charts, weight=3)  # type: ignore[attr-defined]
        self.current_panel = ChartPanel(  # type: ignore[attr-defined]
            charts,
            icons=self.icons,  # type: ignore[attr-defined]
            on_status=self.apply_status,
        )
        self.current_panel.frame.pack(  # type: ignore[attr-defined]
            side=tk.TOP, fill=tk.BOTH, expand=True
        )
        self.evolution_panel = ChartPanel(  # type: ignore[attr-defined]
            charts,
            icons=self.icons,  # type: ignore[attr-defined]
            on_status=self.apply_status,
        )
        self.evolution_panel.frame.pack(  # type: ignore[attr-defined]
            side=tk.TOP, fill=tk.BOTH, expand=True
        )
        orientation = build_orientation(
            self.paned, self.kind, tk, ttk  # type: ignore[attr-defined]
        )
        self.paned.add(orientation, weight=1)  # type: ignore[attr-defined]

    def build_statusbar(self: SubTabUI) -> None:
        """Build the separator, statusbar and indeterminate progress bar."""
        tk, ttk = self.tk, self.ttk  # type: ignore[attr-defined]
        statusbar = ttk.Frame(  # type: ignore[attr-defined]
            self.frame, padding=(8, 2, 8, 4)  # type: ignore[attr-defined]
        )
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).pack(  # type: ignore[attr-defined]
            side=tk.BOTTOM, fill=tk.X
        )
        row = ttk.Frame(statusbar)
        row.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="")  # type: ignore[attr-defined]
        self.status_label = ttk.Label(  # type: ignore[attr-defined]
            row,
            textvariable=self.status_var,  # type: ignore[attr-defined]
            anchor=tk.W,
        )
        self.status_label.pack(  # type: ignore[attr-defined]
            side=tk.LEFT, fill=tk.X, expand=True
        )
        self.progress = ttk.Progressbar(  # type: ignore[attr-defined]
            row, mode="indeterminate", length=140
        )

    def update_loading_state(self: SubTabUI, loading: bool) -> None:
        """Enable/disable controls and move the progress bar in the statusbar."""
        tk = self.tk  # type: ignore[attr-defined]
        state = tk.DISABLED if loading else tk.NORMAL
        self.refresh_button.configure(state=state)  # type: ignore[attr-defined]
        self.ignore_cache_cb.configure(state=state)  # type: ignore[attr-defined]
        self.window_combo.configure(  # type: ignore[attr-defined]
            state="disabled" if loading else "readonly"
        )
        if self._refresh_image is not None:  # type: ignore[attr-defined]
            image_name = 'content-loading' if loading else 'view-refresh'
            image = self.icons.get(image_name)  # type: ignore[attr-defined]
            if image is not None:
                self.refresh_button.configure(image=image)  # type: ignore[attr-defined]
        if loading:
            self.progress.pack(  # type: ignore[attr-defined]
                side=tk.RIGHT, padx=(8, 0)
            )
            self.progress.start()  # type: ignore[attr-defined]
        elif self.progress.winfo_manager():  # type: ignore[attr-defined]
            self.progress.stop()  # type: ignore[attr-defined]
            self.progress.pack_forget()  # type: ignore[attr-defined]

    def _start_load(
        self: SubTabUI, *, cache_only: bool = False, force: bool = False
    ) -> None:
        """Start a load in the worker thread and show its initial status."""
        if self._loading or self._closed:  # type: ignore[attr-defined]
            return
        self._loading = True  # type: ignore[attr-defined]
        self.controller.begin_load(  # type: ignore[attr-defined]
            cache_only=cache_only
        )
        self.update_loading_state(True)
        view_model = self.controller.view_model()  # type: ignore[attr-defined]
        self.apply_status(view_model.status_text, view_model.status_kind)
        threading.Thread(
            target=self._load_worker,  # type: ignore[attr-defined]
            args=(cache_only, force),
            daemon=True,
        ).start()

    def _on_stage(self: SubTabUI, stage: str) -> None:
        """Marshal a worker stage callback to the UI thread."""
        if self._closed:  # type: ignore[attr-defined]
            return
        try:
            self.root.after(  # type: ignore[attr-defined]
                0, self._apply_stage, stage
            )
        except Exception:
            return

    def _apply_stage(self: SubTabUI, stage: str) -> None:
        """Apply the current load stage and refresh the statusbar."""
        if self._closed or not self._root_alive():  # type: ignore[attr-defined]
            return
        if not self.controller.loading:  # type: ignore[attr-defined]
            return
        self.controller.loading_stage = stage  # type: ignore[attr-defined]
        view_model = self.controller.view_model()  # type: ignore[attr-defined]
        self.apply_status(view_model.status_text, view_model.status_kind)

    def apply_status(self: SubTabUI, message: str, kind: str) -> None:
        """Write a message and its severity color to the statusbar."""
        self.status_var.set(message)  # type: ignore[attr-defined]
        self.status_label.configure(  # type: ignore[attr-defined]
            foreground=_STATUS_COLORS.get(kind, "")
        )
