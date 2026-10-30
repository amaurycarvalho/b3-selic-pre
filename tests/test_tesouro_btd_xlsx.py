from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.domain.models import EstoqueMensalTitulo
from b3_selic_pre.infrastructure.tesouro_btd_xlsx import parse_btd_xlsx
from tests.btd_fixtures import (
    stock_rows,
    xlsx_bytes,
    xlsx_renamed_sheet,
    xlsx_without_stock_sheet,
    xlsx_without_values,
)


def test_parses_stock_sheet_and_converts_millions_to_reais():
    records = parse_btd_xlsx(xlsx_bytes())

    assert EstoqueMensalTitulo(
        "Tesouro Selic 2029", "2026-09", Decimal("120000000")
    ) in records
    assert EstoqueMensalTitulo(
        "Tesouro IPCA+ 2035", "2026-08", Decimal("50000000")
    ) in records


def test_percentage_section_is_not_read_as_absolute_values():
    records = parse_btd_xlsx(xlsx_bytes())

    assert {record.mes for record in records} == {"2026-08", "2026-09"}
    assert all(record.valor_estoque >= Decimal("1000000") for record in records)


def test_aggregate_total_row_is_not_read_as_a_title():
    records = parse_btd_xlsx(xlsx_bytes())

    assert all(record.tipo_titulo != "Estoque" for record in records)


def test_converts_month_abbreviation_to_iso_month():
    records = parse_btd_xlsx(xlsx_bytes())

    assert "2026-09" in {record.mes for record in records}


def test_sheet_identified_by_first_cell_when_name_differs():
    records = parse_btd_xlsx(xlsx_renamed_sheet())

    assert records


def test_missing_stock_sheet_fails():
    with pytest.raises(TesouroDataError, match="não encontrada"):
        parse_btd_xlsx(xlsx_without_stock_sheet())


def test_sheet_without_values_fails():
    with pytest.raises(TesouroDataError, match="sem registros"):
        parse_btd_xlsx(xlsx_without_values())


def test_invalid_zip_fails():
    with pytest.raises(TesouroDataError, match="XLSX"):
        parse_btd_xlsx(b"not a zip")


def test_unknown_title_is_preserved():
    rows = stock_rows().replace(
        "Tesouro IPCA+ 2035", "Tesouro Futuro 2045"
    )

    records = parse_btd_xlsx(xlsx_bytes(rows))

    assert any(
        record.tipo_titulo == "Tesouro Futuro 2045" for record in records
    )
