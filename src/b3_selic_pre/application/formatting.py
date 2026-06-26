import csv
import io

from b3_selic_pre.domain.models import RateRecord


def _brl(value):
    return f"{value:.2f}".replace(".", ",")


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


def format_evolution_csv(date_rates):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["DATA", "ANO", "TAXA_MEDIA"])
    for date_str in sorted(date_rates.keys()):
        from b3_selic_pre.application.use_cases import average_rate_by_year
        rates = average_rate_by_year(date_rates[date_str])
        for year in sorted(rates):
            writer.writerow([date_str, year, f"{rates[year]:.2f}"])
    return output.getvalue()
