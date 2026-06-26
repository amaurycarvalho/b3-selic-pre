import argparse
from datetime import date, datetime

from b3_selic_pre import __version__
from b3_selic_pre.application.use_cases import (
    consolidate_by_year,
    default_reference_date,
)
from b3_selic_pre.application.formatting import format_cli_rows, format_yearly_rows
from b3_selic_pre.infrastructure.b3_client import fetch_reference_rates
from b3_selic_pre.infrastructure.desktop import create_shortcut
from b3_selic_pre.presentation.gui import launch_gui


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
