import io
import os
import threading
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
from b3_selic_pre.application.analyze import analyze


class DatePicker:
    def __init__(self, parent, date_var):
        import tkinter as tk
        from tkinter import ttk
        self.parent = parent
        self.date_var = date_var
        self.tk = tk
        now = date.today()
        self.year = now.year
        self.month = now.month
        self.top = tk.Toplevel(parent)
        self.top.title("Selecionar Data")
        self.top.resizable(False, False)
        self.top.grab_set()
        nav = ttk.Frame(self.top, padding=4)
        nav.pack()
        ttk.Button(nav, text="<", width=3,
                   command=self._prev_month).pack(side=tk.LEFT)
        self.month_label = ttk.Label(nav, text="", width=14, anchor="center")
        self.month_label.pack(side=tk.LEFT, padx=4)
        ttk.Button(nav, text=">", width=3,
                   command=self._next_month).pack(side=tk.LEFT)
        self.year_spin = tk.Spinbox(nav, from_=2020, to=2030, width=5,
                                    command=self._rebuild)
        self.year_spin.pack(side=tk.LEFT, padx=(8, 0))
        self.cal_frame = ttk.Frame(self.top, padding=4)
        self.cal_frame.pack()
        self._rebuild()

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._rebuild()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._rebuild()

    def _rebuild(self):
        from calendar import monthcalendar, month_name
        for w in self.cal_frame.winfo_children():
            w.destroy()
        self.month_label.config(text=f"{month_name[self.month]} {self.year}")
        self.year_spin.delete(0, self.tk.END)
        self.year_spin.insert(0, str(self.year))
        days_header = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for i, d in enumerate(days_header):
            self.tk.Label(self.cal_frame, text=d, font=("", 8, "bold"),
                          width=4, anchor="center").grid(row=0, column=i, padx=1)
        cal = monthcalendar(self.year, self.month)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    self.tk.Label(self.cal_frame, text="", width=4).grid(
                        row=r + 1, column=c, padx=1)
                else:
                    btn = self.tk.Button(
                        self.cal_frame, text=str(day), width=4,
                        command=lambda d=day: self._pick(d),
                    )
                    btn.grid(row=r + 1, column=c, padx=1)

    def _pick(self, day):
        selected = date(self.year, self.month, day).isoformat()
        self.date_var.set(selected)
        self.top.destroy()


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
        root.geometry("1100x560")
        icon_path = _icon_source()
        if os.path.exists(icon_path):
            img = tk.PhotoImage(file=icon_path)
            self.icon_img = img
            root.iconphoto(True, img)
        self.date_var = tk.StringVar(value=default_reference_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")
        self.view_var = tk.StringVar(value="raw")
        self.evolution_var = tk.BooleanVar(value=False)
        self.var_3d = tk.BooleanVar(value=False)
        self.historical_data = None
        self.sidebar_var = tk.BooleanVar(value=False)
        top_frame = ttk.Frame(root, padding=12)
        top_frame.pack(fill=tk.X)
        ttk.Label(top_frame, text="Data (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.date_entry = ttk.Entry(top_frame, textvariable=self.date_var, width=14)
        self.date_entry.pack(side=tk.LEFT, padx=(6, 10))
        self.date_entry.bind("<Return>", lambda _event: self.fetch_rates())
        self.cal_button = ttk.Button(
            top_frame, text="📅", width=3, command=self._open_calendar,
        )
        self.cal_button.pack(side=tk.LEFT, padx=(0, 10))
        self.fetch_button = ttk.Button(top_frame, text="Buscar", command=self.fetch_rates)
        self.fetch_button.pack(side=tk.LEFT)
        self.shortcut_button = None
        if not shortcut_exists():
            self.shortcut_button = ttk.Button(
                top_frame, text="Criar Atalho Desktop",
                command=self._create_shortcut,
            )
            self.shortcut_button.pack(side=tk.RIGHT)
        middle_frame = ttk.Frame(root)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        chart_frame = ttk.Frame(middle_frame)
        chart_frame.grid(row=0, column=0, sticky="nsew")
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.figure.add_subplot(111)
        render_chart(self.figure, [])
        self.ax = self.figure.gca()
        self.ax.set_title("B3 SELIC Pré", fontsize=14)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
        self.toolbar.update()
        self.sidebar_frame = ttk.Frame(middle_frame, width=280)
        self._build_sidebar(self.sidebar_frame)
        bottom_frame = ttk.Frame(root, padding=12)
        bottom_frame.pack(fill=tk.X)
        self.data_button = ttk.Button(
            bottom_frame,
            text="Copiar dados",
            command=self.copy_data,
        )
        self.data_button.pack(side=tk.LEFT)
        self.copy_button = ttk.Button(
            bottom_frame,
            text="Copiar gráfico",
            command=self.copy_chart,
        )
        self.copy_button.pack(side=tk.LEFT, padx=(8, 0))
        self.export_button = ttk.Button(
            bottom_frame,
            text="Exportar PNG",
            command=self.export_chart,
        )
        self.export_button.pack(side=tk.LEFT, padx=(8, 0))
        self._update_button_states()
        self.view_raw_rb = ttk.Radiobutton(
            bottom_frame, text="Detalhado", variable=self.view_var,
            value="raw", command=self.toggle_view,
        )
        self.view_raw_rb.pack(side=tk.LEFT, padx=(16, 0))
        self.view_consolidated_rb = ttk.Radiobutton(
            bottom_frame, text="Consolidado", variable=self.view_var,
            value="consolidated", command=self.toggle_view,
        )
        self.view_consolidated_rb.pack(side=tk.LEFT, padx=(4, 0))
        self.evolution_cb = ttk.Checkbutton(
            bottom_frame, text="Evolução da curva",
            variable=self.evolution_var, command=self.toggle_evolution,
        )
        self.evolution_cb.pack(side=tk.LEFT, padx=(4, 0))
        self.cb_3d = ttk.Checkbutton(
            bottom_frame, text="3D",
            variable=self.var_3d, command=self._redraw_chart,
        )
        self.cb_3d.pack(side=tk.LEFT, padx=(4, 0))
        self.cb_3d.configure(state=tk.DISABLED)
        self.sidebar_cb = ttk.Checkbutton(
            bottom_frame, text="Análise",
            variable=self.sidebar_var, command=self._toggle_sidebar,
        )
        self.sidebar_cb.pack(side=tk.LEFT, padx=(4, 0))
        ttk.Label(bottom_frame, textvariable=self.status_var).pack(
            side=tk.LEFT,
            padx=(16, 0),
            fill=tk.X,
            expand=True,
        )

    def _build_sidebar(self, parent):
        text_frame = self.ttk.Frame(parent)
        text_frame.pack(fill=self.tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.sidebar_text = self.tk.Text(
            text_frame, wrap=self.tk.WORD, state=self.tk.DISABLED,
            width=36, font=("TkDefaultFont", 9),
        )
        scrollbar = self.ttk.Scrollbar(
            text_frame, orient=self.tk.VERTICAL,
            command=self.sidebar_text.yview,
        )
        self.sidebar_text.configure(yscrollcommand=scrollbar.set)
        self.sidebar_text.pack(side=self.tk.LEFT, fill=self.tk.BOTH, expand=True)
        scrollbar.pack(side=self.tk.RIGHT, fill=self.tk.Y)

    def _toggle_sidebar(self):
        if self.sidebar_var.get():
            self.sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
            self._update_analysis()
        else:
            self.sidebar_frame.grid_forget()

    def set_loading(self, is_loading):
        state = self.tk.DISABLED if is_loading else self.tk.NORMAL
        self.fetch_button.configure(state=state)

    def set_status(self, message):
        self.status_var.set(message)

    def _open_calendar(self):
        DatePicker(self.root, self.date_var)

    def _create_shortcut(self):
        create_shortcut()
        if self.shortcut_button:
            self.shortcut_button.pack_forget()
            self.shortcut_button = None
        self.set_status("Atalho criado em ~/Desktop/ e ~/.local/share/applications/.")

    def _update_button_states(self):
        has_single = bool(self.records)
        has_historical = bool(self.historical_data)
        has_any = has_single or has_historical
        state = self.tk.NORMAL if has_any else self.tk.DISABLED
        self.data_button.configure(state=state)
        self.copy_button.configure(state=state)
        self.export_button.configure(state=state)

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
        from b3_selic_pre.application.analyze._report import format_report
        self.sidebar_text.insert(self.tk.END, format_report(report))
        self.sidebar_text.configure(state=self.tk.DISABLED)

    def toggle_view(self):
        self._redraw_chart()

    def toggle_evolution(self):
        if self.evolution_var.get():
            self.cb_3d.configure(state=self.tk.NORMAL)
            if self.historical_data:
                self._redraw_chart()
            else:
                today = date.today().isoformat()
                if self.date_var.get().strip() != today:
                    self.date_var.set(today)
                self._fetch_historical_rates(today)
        else:
            self.var_3d.set(False)
            self.cb_3d.configure(state=self.tk.DISABLED)
            self._redraw_chart()

    def fetch_rates(self):
        try:
            reference_date = validate_reference_date(self.date_var.get().strip())
        except ValueError as exc:
            self.set_status(str(exc))
            return
        parsed = datetime.strptime(reference_date, "%Y-%m-%d").date()
        cutoff = date.today() - timedelta(days=30)
        if parsed < cutoff:
            self.set_status(
                "Data muito antiga. O histórico disponível cobre apenas os "
                "últimos 30 dias. Informe uma data mais recente.")
            return
        self.set_loading(True)
        if reference_date == date.today().isoformat():
            self.set_status("Buscando taxas na B3...")
            source = lambda d: fetch_reference_rates(d, page_size=100)
        else:
            self.set_status("Baixando arquivo de taxas...")
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
        self.set_loading(True)
        self.set_status("Buscando taxas históricas... (0/7 concluídas)")

        def progress(completed, total):
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
        self.set_loading(False)
        self.records = list(records)
        self._redraw_chart()
        self._update_button_states()
        if records:
            self.set_status(f"{len(records)} registro(s) carregado(s).")
        else:
            self.set_status("Nenhum registro encontrado para a data informada.")

    def handle_historical_fetch_success(self, historical):
        self.set_loading(False)
        self.records = list(historical.get(
            sorted(historical.keys())[-1], []
        ))
        self.historical_data = historical
        self._redraw_chart()
        self._update_button_states()
        total = sum(len(v) for v in historical.values())
        dates = len(historical)
        self.set_status(f"Dados históricos carregados: {dates} datas, {total} registros.")

    def handle_fetch_error(self, exc):
        self.set_loading(False)
        self.records = []
        self._redraw_chart()
        self._update_button_states()
        self.set_status(f"Erro ao buscar dados: {exc}")

    def _has_data(self):
        return bool(self.records)

    def copy_chart(self):
        if not self._has_data():
            return
        import pyxclip
        from PIL import Image
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", dpi=150)
        img = Image.open(buf).convert("RGBA")
        try:
            pyxclip.copy((img.width, img.height, img.tobytes()))
            self.set_status("Gráfico copiado para a área de transferência.")
        except pyxclip.ClipboardError:
            self.set_status("Use Exportar PNG para salvar o gráfico.")

    def copy_data(self):
        if not self._has_data():
            return
        if self.evolution_var.get() and self.historical_data:
            csv_text = format_evolution_csv(self.historical_data)
        elif self.view_var.get() == "consolidated":
            consolidated = consolidate_by_year(self.records)
            csv_text = format_yearly_rows(consolidated)
        else:
            csv_text = format_cli_rows(self.records)
        self.root.clipboard_clear()
        self.root.clipboard_append(csv_text)
        self.set_status("Dados copiados para a área de transferência.")

    def export_chart(self):
        if not self._has_data():
            return
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Exportar PNG",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Todos os arquivos", "*.*")],
        )
        if not filename:
            return
        self.figure.savefig(filename, dpi=150)
        self.set_status(f"PNG exportado: {filename}")


def launch_gui():
    import tkinter as tk
    root = tk.Tk()
    SelicPreApp(root)

    def on_closing():
        root.quit()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
