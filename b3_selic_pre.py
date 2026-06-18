import argparse
import base64
import csv
from dataclasses import dataclass
from datetime import date, datetime
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import concurrent.futures
import urllib.request


__version__ = "0.4.0"

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

B3_BASE_URL = "https://sistemaswebb3-derivativos.b3.com.br/"
DEFAULT_LANGUAGE = "pt-br"
DEFAULT_RATE_ID = "SLP"
DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 100


@dataclass(frozen=True)
class RateRecord:
    day252: int
    day360: int
    rate: str


def default_reference_date():
    return date.today().isoformat()


def validate_reference_date(reference_date):
    try:
        parsed = datetime.strptime(reference_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Use uma data no formato YYYY-MM-DD.") from exc
    return parsed.isoformat()


def build_payload(
    reference_date,
    language=DEFAULT_LANGUAGE,
    rate_id=DEFAULT_RATE_ID,
    page_number=DEFAULT_PAGE_NUMBER,
    page_size=DEFAULT_PAGE_SIZE,
):
    return {
        "language": language,
        "id": rate_id,
        "pageNumber": page_number,
        "pageSize": page_size,
        "date": validate_reference_date(reference_date),
    }


def encode_payload(payload):
    return base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8")


def build_url(payload):
    return f"{B3_BASE_URL}referenceRatesProxy/Search/GetList/{encode_payload(payload)}"


def normalize_records(data):
    results = data.get("results")
    if results is None:
        raise ValueError("Resposta da B3 não contém o campo 'results'.")
    if not isinstance(results, list):
        raise ValueError("Campo 'results' da B3 não é uma lista.")

    records = []
    for item in results:
        try:
            records.append(
                RateRecord(
                    day252=int(item["day252"]),
                    day360=int(item["day360"]),
                    rate=str(item["rate"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Registro de taxa da B3 tem formato inesperado.") from exc
    return records


def fetch_reference_rates_page(
    reference_date,
    page_number=DEFAULT_PAGE_NUMBER,
    page_size=DEFAULT_PAGE_SIZE,
    opener=urllib.request.urlopen,
    timeout=30,
):
    payload = build_payload(
        reference_date,
        page_number=page_number,
        page_size=page_size,
    )
    url = build_url(payload)
    with opener(url, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return normalize_records(data)


def fetch_reference_rates(
    reference_date,
    opener=urllib.request.urlopen,
    timeout=30,
    page_size=DEFAULT_PAGE_SIZE,
    max_pages=DEFAULT_MAX_PAGES,
):
    if page_size <= 0:
        raise ValueError("Tamanho da página deve ser maior que zero.")
    if max_pages <= 0:
        raise ValueError("Quantidade máxima de páginas deve ser maior que zero.")

    records = []
    for page_number in range(DEFAULT_PAGE_NUMBER, max_pages + 1):
        page_records = fetch_reference_rates_page(
            reference_date,
            page_number=page_number,
            page_size=page_size,
            opener=opener,
            timeout=timeout,
        )
        records.extend(page_records)
        if len(page_records) < page_size:
            return records

    raise ValueError("Paginação da B3 excedeu o limite máximo de páginas.")


def format_cli_rows(records):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["DU252", "DC365", "TAXA"])
    for record in records:
        writer.writerow([record.day252, record.day360, record.rate])
    return output.getvalue()


def format_records_csv(records):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["day252", "day360", "rate"])
    for record in records:
        writer.writerow([record.day252, record.day360, record.rate])
    return output.getvalue()


def consolidate_by_year(records):
    groups = {}
    for r in records:
        year = r.day360 // 365
        rate = float(r.rate.replace(",", "."))
        if year in groups:
            g = groups[year]
            if rate < g["min_rate"]:
                g["min_rate"] = rate
            if rate > g["max_rate"]:
                g["max_rate"] = rate
        else:
            groups[year] = {"year": year, "min_rate": rate, "max_rate": rate}
    return [groups[y] for y in sorted(groups)]


def average_rate_by_year(records):
    consolidated = consolidate_by_year(records)
    return {g["year"]: (g["min_rate"] + g["max_rate"]) / 2 for g in consolidated}


def _days_ago(base_date, days):
    from datetime import timedelta
    d = datetime.strptime(base_date, "%Y-%m-%d").date()
    return (d - timedelta(days=days)).isoformat()


EVOLUTION_DAYS = [28, 21, 14, 7, 0]


def fetch_rates_download(date_str):
    payload = {"language": "pt-br", "date": date_str, "id": "SLP"}
    compact = json.dumps(payload, separators=(",", ":"))
    encoded = base64.b64encode(compact.encode("utf-8")).decode("utf-8")
    url = f"{B3_BASE_URL}referenceRatesProxy/Search/GetDownloadFile/{encoded}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read()
    b64_text = raw.decode("latin-1").strip()
    if not b64_text:
        return []
    decoded = base64.b64decode(b64_text)
    text = decoded.decode("latin-1")
    lines = text.strip().split("\n")
    records = []
    for line in lines[1:]:
        parts = line.split(";")
        if len(parts) >= 4:
            records.append(RateRecord(
                day252=int(parts[1]),
                day360=int(parts[2]),
                rate=parts[3],
            ))
    return records


def fetch_historical_rates(base_date, progress_callback=None):
    today = date.today().isoformat()
    dates = [_days_ago(base_date, d) for d in EVOLUTION_DAYS]

    def fetch_one(date_str):
        if date_str == today:
            records = fetch_reference_rates(date_str, page_size=100)
        else:
            records = fetch_rates_download(date_str)
            if not records:
                records = fetch_reference_rates(date_str, page_size=100)
        return date_str, records

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_one, d): d for d in dates}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            date_str, records = future.result()
            results[date_str] = records
            if progress_callback:
                progress_callback(i + 1, len(dates))
    return results


def _brl(value):
    return f"{value:.2f}".replace(".", ",")


def format_yearly_rows(consolidated):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["ANO", "MENOR_TAXA", "MAIOR_TAXA"])
    for row in consolidated:
        writer.writerow([
            row["year"],
            _brl(row["min_rate"]),
            _brl(row["max_rate"]),
        ])
    return output.getvalue()


def render_chart(fig, records, consolidated=False):
    ax = fig.gca()
    ax.clear()

    if not records:
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_xlabel("DC365")
        ax.set_ylabel("TAXA")
        fig.tight_layout()
        return

    if consolidated:
        grouped = consolidate_by_year(records)
        years = [g["year"] for g in grouped]
        min_rates = [g["min_rate"] for g in grouped]
        max_rates = [g["max_rate"] for g in grouped]
        ax.plot(years, min_rates, color="blue", marker="o",
                linestyle="-", linewidth=1.5, label="Menor taxa")
        ax.plot(years, max_rates, color="red", marker="o",
                linestyle="-", linewidth=1.5, label="Maior taxa")
        ax.set_xlabel("Ano")
        ax.set_xlim(0, 20)
        ax.set_xticks(range(0, 21))
        ax.legend()
    else:
        days = [r.day252 for r in records]
        rates = [float(r.rate.replace(",", ".")) for r in records]
        ax.plot(days, rates, color="green", marker=".",
                linestyle="-", linewidth=1.5)
        ax.set_xlabel("DU252")
        ax.set_xlim(0, 756)
        ax.set_xticks(range(1, 757, 20))

    ax.set_ylabel("TAXA (%)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()


QUIVER_YEARS = [0, 1, 2, 3, 5, 10, 15, 20]


def render_curve_evolution(fig, date_rates):
    import numpy as np
    import matplotlib.pyplot as plt

    ax = fig.gca()
    ax.clear()

    if not date_rates:
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_xlabel("Ano")
        ax.set_ylabel("TAXA")
        fig.tight_layout()
        return

    dates_sorted = sorted(date_rates.keys())
    n = len(dates_sorted)
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, n))
    alphas = np.linspace(0.3, 1.0, n)
    linewidths = np.linspace(0.8, 2.5, n)

    all_rates = []
    for i, date_str in enumerate(dates_sorted):
        rates = average_rate_by_year(date_rates[date_str])
        years = sorted(rates.keys())
        vals = [rates[y] for y in years]
        all_rates.append((years, vals))
        ax.plot(years, vals, color=colors[i], alpha=alphas[i],
                linewidth=linewidths[i], label=date_str)

    for j, year in enumerate(QUIVER_YEARS):
        rates_seq = []
        for date_str in dates_sorted:
            rates = average_rate_by_year(date_rates[date_str])
            rates_seq.append(rates.get(year))
        rates_seq = [r for r in rates_seq if r is not None]
        if len(rates_seq) < 2:
            continue
        X = [year + t * 0.06 for t in range(len(rates_seq) - 1)]
        Y = rates_seq[:-1]
        U = [0.06] * (len(rates_seq) - 1)
        V = [rates_seq[t + 1] - rates_seq[t] for t in range(len(rates_seq) - 1)]
        ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=1,
                  color=plt.cm.Blues(np.linspace(0.3, 0.9, len(rates_seq) - 1)),
                  width=0.004, zorder=5)

    ax.set_xlabel("Ano")
    ax.set_xlim(0, 20)
    ax.set_xticks(range(0, 21))
    ax.set_ylabel("TAXA (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()


def format_evolution_csv(date_rates):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["DATA", "ANO", "TAXA_MEDIA"])
    for date_str in sorted(date_rates.keys()):
        rates = average_rate_by_year(date_rates[date_str])
        for year in sorted(rates):
            writer.writerow([date_str, year, f"{rates[year]:.2f}"])
    return output.getvalue()


def _detect_desktop_dir():
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if path:
                return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    user_dirs = os.path.expanduser("~/.config/user-dirs.dirs")
    if os.path.isfile(user_dirs):
        for line in open(user_dirs):
            if line.startswith("XDG_DESKTOP_DIR="):
                raw = line.split("=", 1)[1].strip().strip('"')
                path = os.path.expandvars(raw)
                if path:
                    return path

    return os.path.expanduser("~/Desktop")


def _resolve_executable():
    if getattr(sys, "frozen", False):
        return sys.executable
    script = os.path.abspath(sys.argv[0])
    return f"{sys.executable} {script}"


def _icon_source():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "b3_selic_pre.png")
    return os.path.join(_SCRIPT_DIR, "icons", "b3_selic_pre.png")


SHORTCUT_CHECK_PATH = os.path.expanduser(
    "~/.local/share/applications/b3-selic-pre.desktop"
)


def shortcut_exists():
    return os.path.isfile(SHORTCUT_CHECK_PATH)


def create_shortcut():
    exec_line = _resolve_executable() + " --gui"
    icon_src = _icon_source()
    desktop_dir = _detect_desktop_dir()

    icons_dst = os.path.expanduser("~/.local/share/icons")
    os.makedirs(icons_dst, exist_ok=True)
    if os.path.isfile(icon_src):
        shutil.copy2(icon_src, os.path.join(icons_dst, "b3-selic-pre.png"))

    icon_path = os.path.join(icons_dst, "b3-selic-pre.png")

    content = (
        "[Desktop Entry]\n"
        f"Name=Taxas Referenciais SELIC (B3)\n"
        "Comment=Consulta taxas referenciais SELIC Pré na B3\n"
        f"Exec={exec_line}\n"
        f"Icon={icon_path}\n"
        "Terminal=false\n"
        "Type=Application\n"
        "Categories=Finance;Office;\n"
        "StartupNotify=true\n"
    )

    dests = [
        os.path.join(desktop_dir, "b3-selic-pre.desktop"),
        os.path.expanduser("~/.local/share/applications/b3-selic-pre.desktop"),
    ]
    for path in dests:
        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        os.chmod(path, 0o755)


class DatePicker:
    def __init__(self, parent, date_var):
        import tkinter as tk
        from tkinter import ttk
        from datetime import timedelta
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
        root.geometry("800x560")

        icon_path = os.path.join(_SCRIPT_DIR, "icons/b3_selic_pre.png")
        if os.path.exists(icon_path):
            img = tk.PhotoImage(file=icon_path)
            self.icon_img = img
            root.iconphoto(True, img)

        self.date_var = tk.StringVar(value=default_reference_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")
        self.view_var = tk.StringVar(value="raw")
        self.historical_data = None

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

        chart_frame = ttk.Frame(root, padding=(12, 0, 12, 8))
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.figure.add_subplot(111)
        self.ax = self.figure.gca()
        render_chart(self.figure, [])
        self.ax.set_title("B3 SELIC Pré", fontsize=14)

        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
        self.toolbar.update()

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
        self.view_evolution_rb = ttk.Radiobutton(
            bottom_frame, text="Evolução da curva", variable=self.view_var,
            value="evolution", command=self.toggle_view,
        )
        self.view_evolution_rb.pack(side=tk.LEFT, padx=(4, 0))

        ttk.Label(bottom_frame, textvariable=self.status_var).pack(
            side=tk.LEFT,
            padx=(16, 0),
            fill=tk.X,
            expand=True,
        )

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
        view = self.view_var.get()
        if view == "evolution":
            if self.historical_data:
                render_curve_evolution(self.figure, self.historical_data)
                self.figure.gca().set_title(
                    "B3 SELIC Pré — Evolução da Curva", fontsize=14, y=0.92)
            else:
                render_chart(self.figure, [])
                self.figure.gca().set_title(
                    "B3 SELIC Pré", fontsize=14, y=0.92)
        elif view == "consolidated":
            render_chart(self.figure, self.records, consolidated=True)
            self.figure.gca().set_title(
                "B3 SELIC Pré — Consolidado", fontsize=14, y=0.92)
        else:
            render_chart(self.figure, self.records, consolidated=False)
            self.figure.gca().set_title(
                "B3 SELIC Pré", fontsize=14, y=0.92)
        self.canvas.draw_idle()

    def toggle_view(self):
        view = self.view_var.get()
        if view == "evolution":
            today = date.today().isoformat()
            if self.date_var.get().strip() != today:
                self.date_var.set(today)
            if not self.historical_data:
                if self.records:
                    self.set_status("Clique em Buscar para carregar dados históricos.")
                else:
                    self.set_status("Informe uma data e clique em Buscar para ver a evolução da curva.")
        self._redraw_chart()

    def fetch_rates(self):
        try:
            reference_date = validate_reference_date(self.date_var.get().strip())
        except ValueError as exc:
            self.set_status(str(exc))
            return

        if self.view_var.get() == "evolution":
            today = date.today().isoformat()
            if reference_date != today:
                self.date_var.set(today)
                reference_date = today
            self._fetch_historical_rates(reference_date)
            return

        parsed = datetime.strptime(reference_date, "%Y-%m-%d").date()
        cutoff = date.today() - __import__("datetime").timedelta(days=30)
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
        if not self.records:
            return False
        return True

    def copy_chart(self):
        if not self._has_data():
            return

        import io
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

        if self.view_var.get() == "evolution" and self.historical_data:
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
    root.mainloop()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Consulta taxas referenciais SELIC Pré na B3."
    )
    parser.add_argument(
        "date",
        nargs="?",
        default=default_reference_date(),
        help="Data de referência no formato YYYY-MM-DD.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abre a interface gráfica desktop.",
    )
    parser.add_argument(
        "--yearly",
        action="store_true",
        help="Exibe taxas consolidadas por ano (ANO, MENOR TAXA, MAIOR TAXA).",
    )
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Cria atalho no desktop e menu de aplicações e sai.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"b3-selic-pre {__version__}",
        help="Exibe a versão do programa e sai.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.create_shortcut:
        create_shortcut()
        print("Atalho criado em ~/Desktop/ e ~/.local/share/applications/")
        return
    if args.gui:
        launch_gui()
        return

    records = fetch_reference_rates(args.date)
    if args.yearly:
        consolidated = consolidate_by_year(records)
        output = format_yearly_rows(consolidated)
    else:
        output = format_cli_rows(records)
    if output:
        print(output)


if __name__ == "__main__":
    main()
