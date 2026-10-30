"""Aba SELIC Pré, com a tela atual preservada dentro de um frame."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkcalendar import DateEntry

from b3_selic_pre.presentation.charts import render_chart
from b3_selic_pre.presentation.gui.about import AboutMixin
from b3_selic_pre.presentation.gui.actions import ActionsMixin
from b3_selic_pre.presentation.gui.chart import ChartMixin
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.fetch import FetchMixin
from b3_selic_pre.presentation.gui.sidebar import SidebarMixin
from b3_selic_pre.presentation.gui.status import StatusMixin
from b3_selic_pre.presentation.gui.window import WindowMixin
from b3_selic_pre.presentation.settings import Settings

Widget = Any
TkModule = Any


class SelicPreTab(
    WindowMixin, StatusMixin, ActionsMixin, AboutMixin, ChartMixin,
    SidebarMixin, FetchMixin,
):
    """Conteúdo atual da aplicação, parented no frame da aba SELIC Pré."""

    def __init__(
        self: SelicPreTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        settings: Settings,
        icons: dict[str, Any],
        is_active: Callable[[], bool],
    ) -> None:
        """Build the SELIC Pré widgets into ``parent``."""
        import tkinter as tk
        from tkinter import ttk

        self.container = parent
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.deps = dependencies
        self.settings = settings
        self.icons = icons
        self._is_active = is_active
        self.records = []
        self._startup_finished = False
        self._setup_state(tk)
        self._apply_saved_settings()
        self._build_top_bar(parent, tk, ttk)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self._build_view_options(parent, tk, ttk)
        self._build_chart_area(parent, tk, ttk)
        self._build_toolbar(parent, tk, ttk)
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(
            fill=tk.X, pady=(4, 0)
        )
        self._build_statusbar(parent, tk, ttk)
        self._lockable_widgets = [
            self.date_entry, self.today_button,
            self.fetch_button,
            self.data_button, self.copy_toolbar_btn,
            self.view_raw_rb, self.view_consolidated_rb,
            self.evolution_cb, self.cb_3d, self.sidebar_cb,
        ]
        self._statusbar_default_fg = self.statusbar_label.cget("foreground")
        self._msg_colors = {
            "info": self._statusbar_default_fg,
            "success": "green",
            "warning": "orange",
            "error": "red",
        }
        self._msg_icons = {
            "info": "⏳",
            "success": "✓",
            "warning": "⚠",
            "error": "✖",
        }
        self._update_button_states()

    def is_active(self: SelicPreTab) -> bool:
        """Return whether this tab is the visible top-level tab."""
        return self._is_active()

    def finish_startup(self: SelicPreTab) -> None:
        """Remove the startup lock and enable shortcuts and tooltips."""
        if getattr(self, "_startup_finished", False):
            return
        self._startup_finished = True
        self._set_ui_locked(False)
        self._update_button_states()
        self._setup_shortcuts()
        self._setup_tooltips()

    def _disable_startup_controls(self: SelicPreTab) -> None:
        """Disable lockable widgets while the startup shield is visible."""
        for widget in self._lockable_widgets:
            try:
                widget.configure(state=self.tk.DISABLED)
            except self.tk.TclError:
                pass

    def _setup_state(self: SelicPreTab, tk: TkModule) -> None:
        """Initialize Tk variables and the initial application state."""
        self.date_var = tk.StringVar(value=self.deps.initial_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")
        self.view_var = tk.StringVar(value="raw")
        self.evolution_var = tk.BooleanVar(value=False)
        self.var_3d = tk.BooleanVar(value=False)
        self.historical_data = None
        self._data_source = ""
        self.sidebar_var = tk.BooleanVar(value=False)
        self._client = self.deps.client
        self._configure_after_id = None

    def _apply_saved_settings(self: SelicPreTab) -> None:
        """Apply saved view preferences to the Tk variables."""
        saved_date = self.settings.get("last_date")
        if saved_date:
            self.date_var.set(saved_date)
        self.view_var.set(self.settings.get("view_mode", "raw"))
        self.evolution_var.set(self.settings.get("evolution", False))
        self.var_3d.set(self.settings.get("show_3d", False))
        self.sidebar_var.set(self.settings.get("sidebar", False))
        self.var_3d.trace_add(
            "write", lambda *_: self.settings.set("show_3d", self.var_3d.get())
        )
        if self.sidebar_var.get():
            self.root.after(10, self._toggle_sidebar)

    def _build_top_bar(
        self: SelicPreTab, root: Widget, tk: TkModule, ttk: TkModule
    ) -> None:
        """Build the top bar with the date selector and buttons."""
        top_frame = ttk.Frame(root, padding=12)
        top_frame.pack(fill=tk.X)
        ttk.Label(top_frame, text="Data de referência:").pack(side=tk.LEFT)
        self.date_entry = self._create_date_entry(top_frame, tk, ttk)
        self.date_entry.pack(side=tk.LEFT, padx=(6, 10))
        self.date_entry.bind("<Return>", lambda _event: self.fetch_rates())
        icon_btn_style = ttk.Style()
        icon_btn_style.configure("Icon.TButton", padding=0)
        self.today_button = ttk.Button(
            top_frame, image=self.icons['document-open-recent'],
            command=self._go_today, style="Icon.TButton",
        )
        self.today_button.pack(side=tk.LEFT, padx=(0, 4))
        self.fetch_button = ttk.Button(
            top_frame, image=self.icons['view-refresh'],
            command=self.fetch_rates, style="Icon.TButton",
        )
        self.fetch_button.pack(side=tk.LEFT, padx=(0, 4))
        self.data_button = ttk.Button(
            top_frame, image=self.icons['edit-copy'],
            command=self.copy_data, style="Icon.TButton",
        )
        self.data_button.pack(side=tk.LEFT, padx=(12, 0))
        self.about_button = ttk.Button(
            top_frame, image=self.icons['help-about'],
            command=self._open_about, style="Icon.TButton",
        )
        self.about_button.pack(side=tk.LEFT, padx=(16, 0))
        self.shortcut_button = None
        if not self.deps.shortcut_exists():
            self.shortcut_button = ttk.Button(
                top_frame, text="Criar Atalho Desktop",
                command=self._create_shortcut,
            )
            self.shortcut_button.pack(side=tk.RIGHT)

    def _create_date_entry(
        self: SelicPreTab, parent: Widget, tk: TkModule, ttk: TkModule
    ) -> Widget:
        """Create the date selector; hooks allow tests to inject a lighter one."""
        return DateEntry(
            parent, textvariable=self.date_var, width=14,
            date_pattern='yyyy-mm-dd', background='white',
        )

    def _build_view_options(
        self: SelicPreTab, root: Widget, tk: TkModule, ttk: TkModule
    ) -> None:
        """Build the curve view options and the statistics label."""
        middle_frame = ttk.Frame(root, padding=(12, 4))
        middle_frame.pack(fill=tk.X)
        left_group = ttk.Frame(middle_frame)
        left_group.pack(side=tk.LEFT)
        self.view_raw_rb = ttk.Radiobutton(
            left_group, text="Curva curta", variable=self.view_var,
            value="raw", command=self.toggle_view,
        )
        self.view_raw_rb.pack(side=tk.LEFT, padx=(0, 4))
        self.view_consolidated_rb = ttk.Radiobutton(
            left_group, text="Curva longa", variable=self.view_var,
            value="consolidated", command=self.toggle_view,
        )
        self.view_consolidated_rb.pack(side=tk.LEFT, padx=(4, 0))
        self.evolution_cb = ttk.Checkbutton(
            left_group, text="Evolução da curva",
            variable=self.evolution_var, command=self.toggle_evolution,
        )
        self.evolution_cb.pack(side=tk.LEFT, padx=(8, 0))
        self.cb_3d = ttk.Checkbutton(
            left_group, text="3D",
            variable=self.var_3d, command=self._redraw_chart,
        )
        self.cb_3d.pack(side=tk.LEFT, padx=(4, 0))
        self.cb_3d.configure(state=tk.DISABLED)
        self.sidebar_cb = ttk.Checkbutton(
            left_group, text="Análise",
            variable=self.sidebar_var, command=self._toggle_sidebar,
        )
        self.sidebar_cb.pack(side=tk.LEFT, padx=(4, 0))
        self.stats_label = ttk.Label(
            middle_frame, text="", anchor=tk.E, padding=(16, 0, 0, 0)
        )
        self.stats_label.pack(side=tk.RIGHT, fill=tk.X)

    def _build_chart_area(
        self: SelicPreTab, root: Widget, tk: TkModule, ttk: TkModule
    ) -> None:
        """Build the central chart area and the analysis sidebar."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 0))
        chart_frame = ttk.Frame(self.pane)
        self.pane.add(chart_frame, weight=1)
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.figure.add_subplot(111)
        render_chart(self.figure, [])
        self.ax = self.figure.gca()
        self.ax.set_title("Curva Curta (SELIC Pré)", fontsize=14)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.sidebar_frame = ttk.Frame(self.pane, width=280)
        self._build_sidebar(self.sidebar_frame)

    def _build_toolbar(
        self: SelicPreTab, root: Widget, tk: TkModule, ttk: TkModule
    ) -> None:
        """Build the chart toolbar with the copy-image button."""
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

        toolbar_frame = ttk.Frame(root)
        toolbar_frame.pack(fill=tk.X, padx=12)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.copy_toolbar_btn = tk.Button(
            self.toolbar, image=self.icons['edit-copy'],
            command=self.copy_chart, bd=0, relief=tk.FLAT,
        )
        self.copy_toolbar_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.toolbar.update()

    def _build_statusbar(
        self: SelicPreTab, root: Widget, tk: TkModule, ttk: TkModule
    ) -> None:
        """Build the status bar with message and progress bars."""
        self.statusbar_frame = ttk.Frame(root, padding=(12, 2, 12, 4))
        self.statusbar_frame.pack(fill=tk.X)
        self.statusbar_label = ttk.Label(
            self.statusbar_frame, textvariable=self.status_var
        )
        self.statusbar_label.pack(fill=tk.X, expand=True)
        self._indeterminate_bar = ttk.Progressbar(
            self.statusbar_frame, mode="indeterminate"
        )
        self._determinate_bar = ttk.Progressbar(
            self.statusbar_frame, mode="determinate"
        )
