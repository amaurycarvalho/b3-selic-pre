"""Classe principal da aplicação Tkinter de taxas SELIC Pré."""

# semgrep note: importlib suportado, pois a applicação dá suporte apenas a python 3.7+
from __future__ import annotations

import os
import sys
from importlib import resources  # nosemgrep
from typing import Any

from tkcalendar import DateEntry

from b3_selic_pre import __version__
from b3_selic_pre.application.use_cases import default_reference_date
from b3_selic_pre.infrastructure.cached_client import CachedB3Client
from b3_selic_pre.infrastructure.desktop import _icon_source, shortcut_exists
from b3_selic_pre.presentation.charts import render_chart
from b3_selic_pre.presentation.gui.actions import ActionsMixin
from b3_selic_pre.presentation.gui.chart import ChartMixin
from b3_selic_pre.presentation.gui.fetch import FetchMixin
from b3_selic_pre.presentation.gui.sidebar import SidebarMixin
from b3_selic_pre.presentation.gui.status import StatusMixin
from b3_selic_pre.presentation.gui.window import WindowMixin
from b3_selic_pre.presentation.settings import Settings

Widget = Any
TkModule = Any


class SelicPreApp(
    WindowMixin, StatusMixin, ActionsMixin, ChartMixin, SidebarMixin, FetchMixin
):
    """Aplicação Tkinter de consulta às taxas referenciais SELIC."""

    def __init__(self: SelicPreApp, root: Widget) -> None:
        """Constrói a interface gráfica completa com gráficos e barra de status."""
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.records = []
        self._load_icons(root, tk)
        self._setup_state(tk)
        self._apply_saved_settings(root, tk)
        root.bind("<Configure>", self._on_window_configure, add="+")
        self._build_top_bar(root, tk, ttk)
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X)
        self._build_view_options(root, tk, ttk)
        self._build_chart_area(root, tk, ttk)
        self._build_toolbar(root, tk, ttk)
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(4, 0))
        self._build_statusbar(root, tk, ttk)
        self._lockable_widgets = [
            self.date_entry, self.today_button,
            self.fetch_button,
            self.data_button, self.copy_toolbar_btn,
            self.view_raw_rb, self.view_consolidated_rb,
            self.evolution_cb, self.cb_3d, self.sidebar_cb,
        ]
        self._setup_tooltips()
        self._setup_shortcuts()
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

    def _load_icons(self: SelicPreApp, root: Widget, tk: TkModule) -> None:
        """Define o título da janela e carrega os ícones usados pela interface."""
        root.title(f"Taxas Referenciais SELIC (B3) v{__version__}")
        icon_path = _icon_source()
        if os.path.exists(icon_path):
            img = tk.PhotoImage(file=icon_path, master=root)
            self.icon_img = img
            root.iconphoto(True, img)
        self.icons = {}
        for name in ['document-open-recent', 'view-refresh', 'edit-copy', 'content-loading']:
            if getattr(sys, 'frozen', False):
                path = os.path.join(sys._MEIPASS, f'{name}.png')
            else:
                path = str(resources.files('b3_selic_pre') / 'icons' / f'{name}.png')
            if os.path.exists(path):
                self.icons[name] = tk.PhotoImage(file=path, master=root)

    def _setup_state(self: SelicPreApp, tk: TkModule) -> None:
        """Inicializa as variáveis Tk e o estado inicial da aplicação."""
        self.date_var = tk.StringVar(value=default_reference_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")
        self.view_var = tk.StringVar(value="raw")
        self.evolution_var = tk.BooleanVar(value=False)
        self.var_3d = tk.BooleanVar(value=False)
        self.historical_data = None
        self._data_source = ""
        self.sidebar_var = tk.BooleanVar(value=False)
        self.settings = Settings()
        self._client = CachedB3Client()
        self._configure_after_id = None

    def _apply_saved_settings(self: SelicPreApp, root: Widget, tk: TkModule) -> None:
        """Aplica geometria e preferências salvas na janela e nas variáveis."""
        saved_geo = self.settings.get("window_geometry")
        saved_max = self.settings.get("window_maximized", False)
        if saved_geo:
            root.geometry(saved_geo)
            if saved_max:
                root.after(10, lambda: root.state("zoomed"))
        else:
            root.geometry("1100x660")
            root.after(10, self._center_window)
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

    def _build_top_bar(self: SelicPreApp, root: Widget, tk: TkModule, ttk: TkModule) -> None:
        """Constrói a barra superior com o seletor de data e os botões."""
        top_frame = ttk.Frame(root, padding=12)
        top_frame.pack(fill=tk.X)
        ttk.Label(top_frame, text="Data de referência:").pack(side=tk.LEFT)
        self.date_entry = DateEntry(
            top_frame, textvariable=self.date_var, width=14,
            date_pattern='yyyy-mm-dd', background='white',
        )
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
        self.data_button.pack(side=tk.LEFT)
        self.shortcut_button = None
        if not shortcut_exists():
            self.shortcut_button = ttk.Button(
                top_frame, text="Criar Atalho Desktop",
                command=self._create_shortcut,
            )
            self.shortcut_button.pack(side=tk.RIGHT)

    def _build_view_options(self: SelicPreApp, root: Widget, tk: TkModule, ttk: TkModule) -> None:
        """Constrói as opções de visualização da curva e o rótulo de estatísticas."""
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

    def _build_chart_area(self: SelicPreApp, root: Widget, tk: TkModule, ttk: TkModule) -> None:
        """Constrói a área central com o gráfico principal e o painel lateral."""
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

    def _build_toolbar(self: SelicPreApp, root: Widget, tk: TkModule, ttk: TkModule) -> None:
        """Constrói a barra de ferramentas do gráfico com o botão de copiar."""
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

    def _build_statusbar(self: SelicPreApp, root: Widget, tk: TkModule, ttk: TkModule) -> None:
        """Constrói a barra de status com o rótulo de mensagens e as barras de progresso."""
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


def launch_gui() -> None:
    """Inicia a janela principal da aplicação."""
    import tkinter as tk
    root = tk.Tk()
    app = SelicPreApp(root)

    def on_closing() -> None:
        app._save_window_state()
        root.quit()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
