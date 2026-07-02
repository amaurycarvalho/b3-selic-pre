import io
import os
import sys
import threading
import importlib.resources as resources
from datetime import date, datetime, timedelta

from b3_selic_pre import __version__
from b3_selic_pre.application.use_cases import (
    consolidate_by_year,
    default_reference_date,
    validate_reference_date,
)
from b3_selic_pre.application.formatting import (
    format_cli_rows,
    format_evolution_csv,
    format_yearly_rows,
)
from b3_selic_pre.infrastructure.b3_client import (
    fetch_historical_rates,
    fetch_rates_download,
    fetch_reference_rates,
)
from b3_selic_pre.domain.constants import EVOLUTION_DAYS
from b3_selic_pre.infrastructure.desktop import (
    _icon_source,
    create_shortcut,
    shortcut_exists,
)
from b3_selic_pre.presentation.charts import (
    render_3d_evolution,
    render_chart,
    render_curve_evolution,
    render_detailed_evolution,
)
from b3_selic_pre.presentation.settings import Settings
from b3_selic_pre.application.analyze import analyze
from tkcalendar import DateEntry


class Tooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _schedule(self, event=None):
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        import tkinter as tk
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip_window = tk.Toplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip_window, text=self.text,
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("TkDefaultFont", 9), padx=4, pady=2,
        )
        label.pack()

    def _hide(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None


class SelicPreApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg,
            NavigationToolbar2Tk,
        )
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.records = []
        root.title(f"B3 SELIC Pré v{__version__}")
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
        self.date_var = tk.StringVar(value=default_reference_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")
        self.view_var = tk.StringVar(value="raw")
        self.evolution_var = tk.BooleanVar(value=False)
        self.var_3d = tk.BooleanVar(value=False)
        self.historical_data = None
        self._data_source = ""
        self.sidebar_var = tk.BooleanVar(value=False)
        self.settings = Settings()
        self._configure_after_id = None
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
        self.var_3d.trace_add("write", lambda *_: self.settings.set("show_3d", self.var_3d.get()))
        if self.sidebar_var.get():
            self.root.after(10, self._toggle_sidebar)
        root.bind("<Configure>", self._on_window_configure, add="+")
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
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X)
        middle_frame = ttk.Frame(root, padding=(12, 4))
        middle_frame.pack(fill=tk.X)
        left_group = ttk.Frame(middle_frame)
        left_group.pack(side=tk.LEFT)
        self.view_raw_rb = ttk.Radiobutton(
            left_group, text="Detalhado", variable=self.view_var,
            value="raw", command=self.toggle_view,
        )
        self.view_raw_rb.pack(side=tk.LEFT, padx=(0, 4))
        self.view_consolidated_rb = ttk.Radiobutton(
            left_group, text="Consolidado", variable=self.view_var,
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
        self.stats_label = ttk.Label(middle_frame, text="", anchor=tk.E, padding=(16, 0, 0, 0))
        self.stats_label.pack(side=tk.RIGHT, fill=tk.X)
        self.pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 0))
        chart_frame = ttk.Frame(self.pane)
        self.pane.add(chart_frame, weight=1)
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.figure.add_subplot(111)
        render_chart(self.figure, [])
        self.ax = self.figure.gca()
        self.ax.set_title("B3 SELIC Pré", fontsize=14)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.sidebar_frame = ttk.Frame(self.pane, width=280)
        self._build_sidebar(self.sidebar_frame)
        toolbar_frame = ttk.Frame(root)
        toolbar_frame.pack(fill=tk.X, padx=12)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.copy_toolbar_btn = tk.Button(
            self.toolbar, image=self.icons['edit-copy'],
            command=self.copy_chart, bd=0, relief=tk.FLAT,
        )
        self.copy_toolbar_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.toolbar.update()
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(4, 0))
        self.statusbar_frame = ttk.Frame(root, padding=(12, 2, 12, 4))
        self.statusbar_frame.pack(fill=tk.X)
        self.statusbar_label = ttk.Label(self.statusbar_frame, textvariable=self.status_var)
        self.statusbar_label.pack(fill=tk.X, expand=True)
        self._indeterminate_bar = ttk.Progressbar(
            self.statusbar_frame, mode="indeterminate"
        )
        self._determinate_bar = ttk.Progressbar(
            self.statusbar_frame, mode="determinate"
        )
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

    def _build_sidebar(self, parent):
        text_frame = self.ttk.Frame(parent)
        text_frame.pack(fill=self.tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.sidebar_text = self.tk.Text(
            text_frame, wrap=self.tk.WORD, state=self.tk.DISABLED,
            width=36, font=("TkDefaultFont", 9),
        )
        self.sidebar_text.tag_configure("header", font=("TkDefaultFont", 9, "bold"))
        self.sidebar_text.tag_configure("conf_high", foreground="green")
        self.sidebar_text.tag_configure("conf_mid", foreground="orange")
        self.sidebar_text.tag_configure("conf_low", foreground="red")
        self.sidebar_text.tag_configure("positive", foreground="green")
        self.sidebar_text.tag_configure("negative", foreground="red")
        scrollbar = self.ttk.Scrollbar(
            text_frame, orient=self.tk.VERTICAL,
            command=self.sidebar_text.yview,
        )
        self.sidebar_text.configure(yscrollcommand=scrollbar.set)
        self.sidebar_text.pack(side=self.tk.LEFT, fill=self.tk.BOTH, expand=True)
        scrollbar.pack(side=self.tk.RIGHT, fill=self.tk.Y)

    def _update_stats(self):
        if not self.records:
            self.stats_label.configure(text="")
            return
        rates = [float(r.rate.replace(",", ".")) for r in self.records]
        date_str = self.date_var.get().strip()
        self.stats_label.configure(
            text=f"Data: {date_str} | Maior: {max(rates):.2f}% | "
                 f"Menor: {min(rates):.2f}%"
        )

    def _toggle_sidebar(self):
        self.settings["sidebar"] = self.sidebar_var.get()
        if self.sidebar_var.get():
            self.pane.add(self.sidebar_frame, weight=0)
            self._update_analysis()
        else:
            self.pane.forget(self.sidebar_frame)

    def _set_ui_locked(self, locked, determinate=False):
        state = self.tk.DISABLED if locked else self.tk.NORMAL
        for w in self._lockable_widgets:
            try:
                w.configure(state=state)
            except self.tk.TclError:
                pass
        self.root.config(cursor="watch" if locked else "")
        if locked:
            self._indeterminate_bar.stop()
            self._indeterminate_bar.pack_forget()
            self._determinate_bar.pack_forget()
            if determinate:
                self._determinate_bar["value"] = 0
                self._determinate_bar.pack(side=self.tk.LEFT, padx=(0, 8))
            else:
                self._indeterminate_bar.pack(side=self.tk.LEFT, padx=(0, 8))
                self._indeterminate_bar.start()
            self.fetch_button.configure(image=self.icons['content-loading'])
            self.set_status("Buscando taxas…", msg_type="info")
        else:
            self._indeterminate_bar.stop()
            self._indeterminate_bar.pack_forget()
            self._determinate_bar.pack_forget()
            self.fetch_button.configure(image=self.icons['view-refresh'])

    def set_status(self, message, msg_type="info"):
        if hasattr(self, "_restore_after_id") and self._restore_after_id:
            self.root.after_cancel(self._restore_after_id)
            self._restore_after_id = None
        icon = self._msg_icons.get(msg_type, "")
        self.status_var.set(f"{icon} {message}" if icon else message)
        color = self._msg_colors.get(msg_type, self._statusbar_default_fg)
        self.statusbar_label.config(foreground=color)

    def _on_fetch_progress(self, current_page, total_pages):
        if total_pages is not None and current_page <= total_pages:
            self._indeterminate_bar.stop()
            self._indeterminate_bar.pack_forget()
            self._determinate_bar["maximum"] = total_pages
            self._determinate_bar["value"] = current_page
            self._determinate_bar.pack(side=self.tk.LEFT, padx=(0, 8))
            self.set_status(
                f"Buscando taxas… ({current_page}/{total_pages} páginas)",
                msg_type="info",
            )

    def _center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.update_idletasks()
        self.settings.set("window_geometry", self.root.geometry())

    def _on_window_configure(self, event):
        if event.widget != self.root:
            return
        if self._configure_after_id:
            self.root.after_cancel(self._configure_after_id)
        self._configure_after_id = self.root.after(500, self._save_window_state)

    def _save_window_state(self):
        self._configure_after_id = None
        state = self.root.state()
        is_maximized = state == "zoomed"
        if not is_maximized:
            self.settings.set("window_geometry", self.root.geometry())
        self.settings.set("window_maximized", is_maximized)

    def _nearest_business_day(self, date_str):
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
        while parsed.weekday() >= 5:
            parsed -= timedelta(days=1)
        return parsed.isoformat()

    def _setup_shortcuts(self):
        self.root.bind("<Control-d>", lambda e: self.copy_data())
        self.root.bind("<Control-Shift-C>", lambda e: self.copy_chart())
        self.root.bind("<F5>", lambda e: self.fetch_rates())
        self.root.bind("<Control-e>", lambda e: self.evolution_cb.invoke())
        self.root.bind("<Control-l>", lambda e: self.sidebar_cb.invoke())

    def _setup_tooltips(self):
        tooltips = {
            self.date_entry: "Digite a data no formato AAAA-MM-DD",
            self.today_button: "Define a data atual e busca automaticamente",
            self.fetch_button: "Busca as taxas para a data informada",
            self.data_button: "Copia os dados para a área de transferência",
            self.copy_toolbar_btn: "Copia o gráfico como imagem",
            self.view_raw_rb: "Exibe todos os vencimentos disponíveis",
            self.view_consolidated_rb: "Agrupa os vencimentos por ano",
            self.evolution_cb: "Carrega automaticamente os últimos 7 pregões",
            self.cb_3d: "Exibe a evolução temporal em três dimensões",
            self.sidebar_cb: "Exibe painel com análise da curva",
        }
        for widget, text in tooltips.items():
            Tooltip(widget, text)

    def _go_today(self):
        self.date_var.set(date.today().isoformat())
        self.fetch_rates()

    def _create_shortcut(self):
        create_shortcut()
        if self.shortcut_button:
            self.shortcut_button.pack_forget()
            self.shortcut_button = None
        self.set_status("Atalho criado em ~/Desktop/ e ~/.local/share/applications/.", msg_type="success")

    def _update_button_states(self):
        has_single = bool(self.records)
        has_historical = bool(self.historical_data)
        has_any = has_single or has_historical
        copy_state = self.tk.NORMAL if has_any else self.tk.DISABLED
        self.data_button.configure(state=copy_state)
        self.copy_toolbar_btn.configure(state=copy_state)
        consolidated_state = self.tk.NORMAL if has_single else self.tk.DISABLED
        self.view_consolidated_rb.configure(state=consolidated_state)
        self.view_raw_rb.configure(state=consolidated_state)
        self.evolution_cb.configure(state=consolidated_state)
        analysis_state = self.tk.NORMAL if has_single else self.tk.DISABLED
        self.sidebar_cb.configure(state=analysis_state)

    def _redraw_chart(self):
        show_evolution = self.evolution_var.get()
        show_3d = self.var_3d.get()
        view = self.view_var.get()
        if show_evolution and self.historical_data:
            if show_3d:
                c = view == "consolidated"
                render_3d_evolution(self.figure, self.historical_data, consolidated=c)
                mode = "Consolidada" if c else "Detalhada"
                self.figure.gca().set_title(
                    f"B3 SELIC Pré — Evolução 3D {mode}", fontsize=14, y=1.06,
                    ha="center")
            elif view == "consolidated":
                render_curve_evolution(self.figure, self.historical_data)
                self.figure.gca().set_title(
                    "B3 SELIC Pré — Evolução Consolidada", fontsize=14, y=0.92)
            else:
                render_detailed_evolution(self.figure, self.historical_data)
                self.figure.gca().set_title(
                    "B3 SELIC Pré — Evolução Detalhada", fontsize=14, y=0.92)
        elif view == "consolidated":
            render_chart(self.figure, self.records, consolidated=True)
            self.figure.gca().set_title(
                "B3 SELIC Pré — Consolidado", fontsize=14, y=0.92)
        else:
            render_chart(self.figure, self.records, consolidated=False)
            self.figure.gca().set_title(
                "B3 SELIC Pré", fontsize=14, y=0.92)
        if show_evolution and self.historical_data and show_3d:
            t = self.figure.gca().title
            self.canvas.draw()
            renderer = self.canvas.get_renderer()
            if renderer is not None:
                bbox = t.get_window_extent(renderer=renderer)
                ax_box = self.figure.gca().get_position()
                fig_w, _ = self.figure.get_size_inches()
                w_ax = (bbox.width / self.figure.dpi) / (ax_box.width * fig_w)
                if w_ax > 0:
                    t.set_x(0.5 - 0.7 * w_ax)
        self.canvas.draw_idle()
        self._update_analysis()

    def _update_analysis(self):
        if not self.sidebar_var.get():
            return
        report = analyze(
            records=self.records,
            historical_data=self.historical_data,
            view_mode=self.view_var.get(),
            evolution_active=self.evolution_var.get(),
        )
        self.sidebar_text.configure(state=self.tk.NORMAL)
        self.sidebar_text.delete("1.0", self.tk.END)
        for i, statement in enumerate(report.statements):
            lines = statement.split("\n")
            for j, line in enumerate(lines):
                if not line.strip():
                    continue
                if j == 0:
                    self.sidebar_text.insert(self.tk.END, line + "\n", "header")
                elif line.startswith("▲"):
                    self.sidebar_text.insert(self.tk.END, line + "\n", "positive")
                elif line.startswith("▼"):
                    self.sidebar_text.insert(self.tk.END, line + "\n", "negative")
                else:
                    self.sidebar_text.insert(self.tk.END, line + "\n")
            if i < len(report.statements) - 1:
                self.sidebar_text.insert(self.tk.END, "\n")
        self.sidebar_text.configure(state=self.tk.DISABLED)

    def toggle_view(self):
        self.settings["view_mode"] = self.view_var.get()
        self._redraw_chart()

    def toggle_evolution(self):
        self.settings["evolution"] = self.evolution_var.get()
        if self.evolution_var.get():
            self.cb_3d.configure(state=self.tk.NORMAL)
            if self.historical_data:
                self._redraw_chart()
            else:
                today = self._nearest_business_day(date.today().isoformat())
                if self.date_var.get().strip() != today:
                    self.date_var.set(today)
                self._fetch_historical_rates(today)
        else:
            self.var_3d.set(False)
            self.settings["show_3d"] = False
            self.cb_3d.configure(state=self.tk.DISABLED)
            self._redraw_chart()

    def fetch_rates(self):
        try:
            reference_date = validate_reference_date(self.date_var.get().strip())
        except ValueError as exc:
            self.set_status(str(exc), msg_type="error")
            return
        parsed = datetime.strptime(reference_date, "%Y-%m-%d").date()
        if parsed > date.today():
            self.set_status(
                "Data futura. Informe uma data até hoje.", msg_type="error")
            return
        reference_date = self._nearest_business_day(reference_date)
        self.date_var.set(reference_date)
        cutoff = date.today() - timedelta(days=30)
        if parsed < cutoff:
            self.set_status(
                "Data muito antiga. O histórico disponível cobre apenas os "
                "últimos 30 dias. Informe uma data mais recente.",
                msg_type="warning")
            return
        self._set_ui_locked(True)
        self._last_reference_date = reference_date
        if self.evolution_var.get():
            self.historical_data = None
        if reference_date == date.today().isoformat():
            self._data_source = "API B3"

            def _progress_cb(current, total):
                self.root.after(0, lambda: self._on_fetch_progress(current, total))

            source = lambda d: fetch_reference_rates(
                d, page_size=100, progress_callback=_progress_cb
            )
        else:
            self._data_source = "Arquivo oficial B3"
            source = fetch_rates_download

        def worker():
            try:
                records = source(reference_date)
            except Exception as exc:
                self.root.after(0, lambda error=exc: self.handle_fetch_error(error))
                return
            self.root.after(0, lambda: self.handle_fetch_success(records))
        threading.Thread(target=worker, daemon=True).start()

    def _fetch_historical_rates(self, reference_date):
        if getattr(self, "_historical_fetching", False):
            return
        self._historical_fetching = True
        self._set_ui_locked(True, determinate=True)
        self._determinate_bar["maximum"] = len(EVOLUTION_DAYS)

        def progress(completed, total):
            self.root.after(0, lambda: self._determinate_bar.configure(value=completed))
            self.root.after(0, lambda: self.set_status(
                f"Buscando taxas históricas... ({completed}/{total} concluídas)"
            ))

        def worker():
            try:
                historical = fetch_historical_rates(
                    reference_date, progress_callback=progress
                )
            except Exception as exc:
                self.root.after(0, lambda error=exc: self.handle_fetch_error(error))
                return
            self.root.after(0, lambda: self.handle_historical_fetch_success(historical))
        threading.Thread(target=worker, daemon=True).start()

    def handle_fetch_success(self, records):
        self.records = list(records)
        self._redraw_chart()
        self._update_button_states()
        self.settings["last_date"] = self.date_var.get().strip()
        self._update_stats()
        if self.evolution_var.get() and not self.historical_data and records:
            self._fetch_historical_rates(self._last_reference_date)
            return
        self._set_ui_locked(False)
        now = datetime.now().strftime("%H:%M:%S")
        if records:
            self.set_status(
                f"{len(records)} registro(s) carregado(s)  |  {self._data_source}  |  {now}",
                msg_type="success")
        else:
            self.set_status("Nenhum registro encontrado para a data informada.")

    def handle_historical_fetch_success(self, historical):
        self._historical_fetching = False
        self._set_ui_locked(False)
        self.records = list(historical.get(
            sorted(historical.keys())[-1], []
        ))
        self.historical_data = historical
        self._data_source = "Histórico B3"
        self._redraw_chart()
        self._update_button_states()
        self.settings["last_date"] = self.date_var.get().strip()
        total = sum(len(v) for v in historical.values())
        dates = len(historical)
        now = datetime.now().strftime("%H:%M:%S")
        self.set_status(
            f"Dados históricos carregados: {dates} datas, {total} registros.  |  {self._data_source}  |  {now}",
            msg_type="success")

    def handle_fetch_error(self, exc):
        self._historical_fetching = False
        self._set_ui_locked(False)
        self.records = []
        self._redraw_chart()
        self._update_button_states()
        self.set_status(f"Erro ao buscar dados: {exc}", msg_type="error")

    def _has_data(self):
        return bool(self.records)

    def _schedule_restore(self, prior_text, prior_color):
        def restore():
            self.status_var.set(prior_text)
            self.statusbar_label.config(foreground=prior_color)
            self._restore_after_id = None
        self._restore_after_id = self.root.after(2000, restore)

    def copy_chart(self):
        if not self._has_data():
            return
        prior_text = self.status_var.get()
        prior_color = self.statusbar_label.cget("foreground")
        import pyxclip
        from PIL import Image
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", dpi=150)
        img = Image.open(buf).convert("RGBA")
        try:
            pyxclip.copy((img.width, img.height, img.tobytes()))
            self.set_status("Gráfico copiado para a área de transferência.", msg_type="success")
            self._schedule_restore(prior_text, prior_color)
        except pyxclip.ClipboardError:
            self.set_status("Use o botão Salvar do toolbar para salvar o gráfico.", msg_type="warning")

    def copy_data(self):
        if not self._has_data():
            return
        prior_text = self.status_var.get()
        prior_color = self.statusbar_label.cget("foreground")
        if self.evolution_var.get() and self.historical_data:
            csv_text = format_evolution_csv(self.historical_data)
        elif self.view_var.get() == "consolidated":
            consolidated = consolidate_by_year(self.records)
            csv_text = format_yearly_rows(consolidated)
        else:
            csv_text = format_cli_rows(self.records)
        self.root.clipboard_clear()
        self.root.clipboard_append(csv_text)
        self.set_status("Dados copiados para a área de transferência.", msg_type="success")
        self._schedule_restore(prior_text, prior_color)


def launch_gui():
    import tkinter as tk
    root = tk.Tk()
    app = SelicPreApp(root)

    def on_closing():
        app._save_window_state()
        root.quit()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
