"""Widgets e estados visuais da sub-aba Dólar e Ouro."""

from __future__ import annotations

from typing import Any

from b3_selic_pre.presentation.busy import BUSY_TEXT
from b3_selic_pre.presentation.gui.market_chart_panel import MarketChartPanel
from b3_selic_pre.presentation.gui.market_orientation import (
    build_market_orientation,
)
from b3_selic_pre.presentation.gui.tooltip import Tooltip

Widget = Any

STATUS_COLORS = {
    "info": "",
    "success": "green",
    "warning": "orange",
    "error": "red",
}
ASSET_OPTIONS = {"Ambos": "ambos", "Dólar": "usd", "Ouro": "ouro"}


class MarketSubTabUI:
    """Layout, tooltips, statusbar e estado de carregamento da sub-aba."""

    def _build_controls(self: MarketSubTabUI) -> None:
        tk, ttk = self.tk, self.ttk
        frame = ttk.Frame(self.frame, padding=(8, 6))
        frame.pack(fill=tk.X)
        ttk.Label(frame, text="Ativo:").pack(side=tk.LEFT)
        self.asset_var = tk.StringVar(value="Ambos")
        self.asset_combo = ttk.Combobox(
            frame, textvariable=self.asset_var,
            values=tuple(ASSET_OPTIONS), state="readonly", width=8,
        )
        self.asset_combo.pack(side=tk.LEFT, padx=(4, 4))
        self.asset_combo.bind("<<ComboboxSelected>>", self._on_option_change)
        self._refresh_image = self.icons.get("view-refresh")
        self.refresh_button = ttk.Button(
            frame,
            image=self._refresh_image if self._refresh_image else "",
            text="" if self._refresh_image else "Atualizar",
            command=self._start_refresh,
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 12))
        self.base100_var = tk.BooleanVar(value=False)
        self.base100_cb = ttk.Checkbutton(
            frame, text="Base 100", variable=self.base100_var,
            command=self._on_option_change,
        )
        self.base100_cb.pack(side=tk.LEFT)
        self.fibonacci_var = tk.BooleanVar(value=False)
        self.fibonacci_cb = ttk.Checkbutton(
            frame, text="Fibonacci", variable=self.fibonacci_var,
            command=self._on_option_change,
        )
        self.fibonacci_cb.pack(side=tk.LEFT, padx=(8, 0))
        self.stale_var = tk.StringVar(value="")
        self.stale_label = ttk.Label(
            frame, textvariable=self.stale_var, foreground="orange"
        )
        self.stale_label.pack(side=tk.LEFT, padx=(12, 0))
        Tooltip(
            self.asset_combo,
            "Filtra a exibição entre dólar, ouro ou ambos",
        )
        Tooltip(
            self.refresh_button,
            "Atualiza as fontes de dólar e ouro desta sub-aba",
        )
        Tooltip(
            self.base100_cb,
            "Reindexa as séries para 100 na data inicial da janela",
        )
        Tooltip(
            self.fibonacci_cb,
            "Desenha níveis de retração sobre o range de 12 meses",
        )

    def _build_body(self: MarketSubTabUI) -> None:
        tk, ttk = self.tk, self.ttk
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self.paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        charts = ttk.Frame(self.paned)
        self.paned.add(charts, weight=3)
        self.loading_label = ttk.Label(
            charts,
            text=BUSY_TEXT,
            anchor=tk.CENTER,
            font=("TkDefaultFont", 12),
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.panel = MarketChartPanel(
            charts, icons=self.icons, on_status=self._apply_status
        )
        self.panel.frame.pack(fill=tk.BOTH, expand=True)
        self.loading_label.lower()
        orientation = build_market_orientation(self.paned, tk, ttk)
        self.paned.add(orientation, weight=1)

    def hide_charts(self: MarketSubTabUI) -> None:
        """Hide the chart panel so the fixed processing text is visible."""
        self.panel.frame.pack_forget()  # type: ignore[attr-defined]
        self.loading_label.lower()  # type: ignore[attr-defined]

    def show_charts(self: MarketSubTabUI) -> None:
        """Show the chart panel again, leaving the text behind it."""
        if not self.panel.frame.winfo_manager():  # type: ignore[attr-defined]
            self.panel.frame.pack(fill=self.tk.BOTH, expand=True)  # type: ignore[attr-defined]
        self.loading_label.lower()  # type: ignore[attr-defined]

    def draw_idle(self: MarketSubTabUI) -> None:
        """Schedule an additional repaint after the panel returns."""
        self.panel.canvas.draw_idle()  # type: ignore[attr-defined]

    def _build_statusbar(self: MarketSubTabUI) -> None:
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
            row, textvariable=self.status_var, anchor=tk.W, width=1
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress = ttk.Progressbar(
            row, mode="indeterminate", length=140
        )
        self.progress_host = ttk.Frame(
            row,
            width=140,
            height=max(20, self.progress.winfo_reqheight()),
        )
        self.progress_host.pack(side=tk.RIGHT, padx=(8, 0))
        self.progress_host.pack_propagate(False)

    def update_loading_state(self: MarketSubTabUI, loading: bool) -> None:
        """Enable/disable controls and animate the statusbar progress."""
        state = self.tk.DISABLED if loading else self.tk.NORMAL
        self.refresh_button.configure(state=state)
        self.asset_combo.configure(
            state="disabled" if loading else "readonly"
        )
        self.base100_cb.configure(state=state)
        self.fibonacci_cb.configure(state=state)
        image_name = "content-loading" if loading else "view-refresh"
        image = self.icons.get(image_name)
        if image is not None:
            self.refresh_button.configure(image=image, text="")
        if loading:
            if not self.progress.winfo_manager():
                self.progress.pack(fill=self.tk.BOTH, expand=True)
            self.progress.start()
        elif self.progress.winfo_manager():
            self.progress.stop()
            self.progress.pack_forget()

    def _apply_status(
        self: MarketSubTabUI, message: str, kind: str
    ) -> None:
        self.status_var.set(message)  # type: ignore[attr-defined]
        self.status_label.configure(  # type: ignore[attr-defined]
            foreground=STATUS_COLORS.get(kind, "")
        )
