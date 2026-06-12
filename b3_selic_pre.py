import argparse
import base64
import csv
from dataclasses import dataclass
from datetime import date, datetime
import io
import json
import threading
import urllib.request


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
    writer.writerow(["DU252", "DC360", "TAXA"])
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


class SelicPreApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.records = []

        root.title("B3 SELIC Pré")
        root.geometry("640x420")

        self.date_var = tk.StringVar(value=default_reference_date())
        self.status_var = tk.StringVar(value="Informe uma data e clique em Buscar.")

        top_frame = ttk.Frame(root, padding=12)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Data (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.date_entry = ttk.Entry(top_frame, textvariable=self.date_var, width=14)
        self.date_entry.pack(side=tk.LEFT, padx=(6, 10))
        self.date_entry.bind("<Return>", lambda _event: self.fetch_rates())

        self.fetch_button = ttk.Button(top_frame, text="Buscar", command=self.fetch_rates)
        self.fetch_button.pack(side=tk.LEFT)

        table_frame = ttk.Frame(root, padding=(12, 0, 12, 8))
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("day252", "day360", "rate")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12,
        )
        self.table.heading("day252", text="Dias Úteis (252)")
        self.table.heading("day360", text="Dias Corridos (365)")
        self.table.heading("rate", text="Taxa")
        self.table.column("day252", width=120, anchor=tk.E)
        self.table.column("day360", width=120, anchor=tk.E)
        self.table.column("rate", width=180, anchor=tk.E)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.table.yview,
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_frame = ttk.Frame(root, padding=12)
        bottom_frame.pack(fill=tk.X)

        self.copy_button = ttk.Button(
            bottom_frame,
            text="Copiar tabela",
            command=self.copy_records,
        )
        self.copy_button.pack(side=tk.LEFT)

        self.export_button = ttk.Button(
            bottom_frame,
            text="Exportar CSV",
            command=self.export_records,
        )
        self.export_button.pack(side=tk.LEFT, padx=(8, 0))

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

    def clear_table(self):
        for row_id in self.table.get_children():
            self.table.delete(row_id)

    def render_records(self, records):
        self.clear_table()
        self.records = list(records)
        for record in self.records:
            self.table.insert(
                "",
                self.tk.END,
                values=(record.day252, record.day360, record.rate),
            )

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
        self.render_records(records)
        if records:
            self.set_status(f"{len(records)} registro(s) carregado(s).")
        else:
            self.set_status("Nenhum registro encontrado para a data informada.")

    def handle_fetch_error(self, exc):
        self.set_loading(False)
        self.clear_table()
        self.records = []
        self.set_status(f"Erro ao buscar dados: {exc}")

    def ensure_records(self):
        if not self.records:
            self.set_status("Não há dados para exportar ou copiar.")
            return False
        return True

    def copy_records(self):
        if not self.ensure_records():
            return

        text = format_records_csv(self.records)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Tabela copiada para a área de transferência.")

    def export_records(self):
        if not self.ensure_records():
            return

        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Exportar CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not filename:
            return

        with open(filename, "w", encoding="utf-8", newline="") as file:
            file.write(format_records_csv(self.records))
        self.set_status(f"CSV exportado: {filename}")


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
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.gui:
        launch_gui()
        return

    records = fetch_reference_rates(args.date)
    output = format_cli_rows(records)
    if output:
        print(output)


if __name__ == "__main__":
    main()
