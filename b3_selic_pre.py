import argparse
import base64
import csv
from dataclasses import dataclass
from datetime import date, datetime
import io
import json
import os
import threading
import urllib.request


__version__ = "0.2.1"

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

        icon_path = os.path.join(_SCRIPT_DIR, "b3_selic_pre.png")
        if os.path.exists(icon_path):
            img = tk.PhotoImage(file=icon_path)
            self.icon_img = img
            root.iconphoto(True, img)

        self.date_var = tk.StringVar(value=default_reference_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")
        self.consolidate_var = tk.BooleanVar(value=False)

        top_frame = ttk.Frame(root, padding=12)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Data (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.date_entry = ttk.Entry(top_frame, textvariable=self.date_var, width=14)
        self.date_entry.pack(side=tk.LEFT, padx=(6, 10))
        self.date_entry.bind("<Return>", lambda _event: self.fetch_rates())

        self.fetch_button = ttk.Button(top_frame, text="Buscar", command=self.fetch_rates)
        self.fetch_button.pack(side=tk.LEFT)

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

        self.consolidate_cb = ttk.Checkbutton(
            bottom_frame,
            text="Consolidar por ano",
            variable=self.consolidate_var,
            command=self.toggle_view,
        )
        self.consolidate_cb.pack(side=tk.LEFT, padx=(16, 0))

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

    def _update_button_states(self):
        state = self.tk.NORMAL if self.records else self.tk.DISABLED
        self.data_button.configure(state=state)
        self.copy_button.configure(state=state)
        self.export_button.configure(state=state)

    def _redraw_chart(self):
        render_chart(self.figure, self.records, self.consolidate_var.get())
        self.canvas.draw_idle()

    def toggle_view(self):
        if not self.records:
            return
        self._redraw_chart()

    def fetch_rates(self):
        try:
            reference_date = validate_reference_date(self.date_var.get().strip())
        except ValueError as exc:
            self.set_status(str(exc))
            return

        self.set_loading(True)
        self.set_status("Buscando taxas na B3...")

        def worker():
            try:
                records = fetch_reference_rates(reference_date)
            except Exception as exc:
                self.root.after(0, lambda error=exc: self.handle_fetch_error(error))
                return
            self.root.after(0, lambda: self.handle_fetch_success(records))

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
        import subprocess
        import platform
        import tempfile
        import os
        import threading

        from PIL import Image

        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", dpi=150)

        system = platform.system()
        png_data = buf.getvalue()

        def worker():
            success = False

            if system == "Linux":
                try:
                    proc = subprocess.Popen(
                        ["xclip", "-selection", "clipboard",
                         "-t", "image/png"],
                        stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                    )
                    proc.communicate(png_data)
                    if proc.returncode == 0:
                        success = True
                except FileNotFoundError:
                    pass

            elif system == "Darwin":
                tmp = None
                try:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(png_data)
                        tmp = f.name
                    script = (
                        f'set the clipboard to '
                        f'(read (POSIX file "{tmp}") as PNG picture)'
                    )
                    subprocess.run(
                        ["osascript", "-e", script],
                        check=True, capture_output=True,
                    )
                    success = True
                except Exception:
                    pass
                finally:
                    if tmp:
                        try:
                            os.unlink(tmp)
                        except Exception:
                            pass

            elif system == "Windows":
                import ctypes
                img = Image.open(io.BytesIO(png_data))
                with io.BytesIO() as bmp_buf:
                    img.convert("RGB").save(bmp_buf, format="BMP")
                    data = bmp_buf.getvalue()[14:]
                GMEM_MOVEABLE = 0x0002
                CF_DIB = 8
                h = ctypes.windll.kernel32.GlobalAlloc(
                    GMEM_MOVEABLE, len(data)
                )
                if h:
                    p = ctypes.windll.kernel32.GlobalLock(h)
                    ctypes.memmove(p, data, len(data))
                    ctypes.windll.kernel32.GlobalUnlock(h)
                    if ctypes.windll.user32.OpenClipboard(None):
                        ctypes.windll.user32.EmptyClipboard()
                        ctypes.windll.user32.SetClipboardData(CF_DIB, h)
                        ctypes.windll.user32.CloseClipboard()
                        success = True
                    else:
                        ctypes.windll.kernel32.GlobalFree(h)

            def update_status():
                if success:
                    self.set_status("Gráfico copiado para a área de transferência.")
                else:
                    self.set_status("Use Exportar PNG para salvar o gráfico.")

            self.root.after(0, update_status)

        threading.Thread(target=worker, daemon=True).start()

    def copy_data(self):
        if not self._has_data():
            return

        if self.consolidate_var.get():
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
        "--version",
        action="version",
        version=f"b3-selic-pre {__version__}",
        help="Exibe a versão do programa e sai.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
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
