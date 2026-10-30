from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import (
    PeriodoInvalidoError,
    TesouroDataError,
    agregar_por_titulo,
    build_agregados_payload,
    build_vendas_payload,
    filtrar_por_periodo,
    filtrar_por_titulo,
    format_agregados_csv,
    format_vendas_csv,
    ordenar_vendas,
    parse_vendas,
    resolver_periodo,
    validar_periodo,
)
from b3_selic_pre.domain.models import VendaTesouroDireto

HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;"
    "PU;Quantidade;Valor"
)


def _csv(*rows: str) -> bytes:
    return ("\n".join((HEADER, *rows)) + "\n").encode("utf-8")


def _sales():
    return parse_vendas(
        _csv(
            "Tesouro Selic 2029;02/01/2029;01/10/2026;15.000,00;2,00;30.000,00",
            "Tesouro IPCA+ 2035;15/05/2035;02/10/2026;3.000,00;1,00;3.000,00",
            "Tesouro Selic 2029;02/01/2029;01/10/2026;14.000,00;3,00;42.000,00",
        )
    )


class TestModel:
    def test_model_is_immutable(self):
        sale = VendaTesouroDireto(
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-10-01",
            Decimal("15000"),
            Decimal("2"),
            Decimal("30000"),
        )
        with pytest.raises(AttributeError):
            sale.pu = Decimal("1")


class TestParsing:
    def test_parses_dates_decimals_and_preserves_duplicates(self):
        sales = _sales()

        assert len(sales) == 3
        assert sales[0].vencimento == "2029-01-02"
        assert sales[0].data_liquidacao == "2026-10-01"
        assert sales[0].pu == Decimal("15000.00")
        assert sales[0].quantidade == Decimal("2.00")
        assert sales[0].valor == Decimal("30000.00")

    def test_accepts_latin1_and_accented_header(self):
        text = (
            "Tipo Título;Vencimento do Título;Data de Liquidação da Venda;"
            "PU;Quantidade;Valor\n"
            "Tesouro Ação;02/01/2029;01/10/2026;10,00;1,00;10,00\n"
        )
        sales = parse_vendas(text.encode("latin-1"))

        assert sales[0].tipo_titulo == "Tesouro Ação"

    def test_missing_required_column(self):
        data = (
            "Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;"
            "PU;Quantidade\n"
            "Tesouro Selic;02/01/2029;01/10/2026;10,00;1,00\n"
        ).encode()
        with pytest.raises(TesouroDataError, match="Valor"):
            parse_vendas(data)

    def test_invalid_date_reports_line_and_column(self):
        with pytest.raises(TesouroDataError, match="Linha 2.*data inválida"):
            parse_vendas(
                _csv(
                    "Tesouro Selic;31/02/2029;01/10/2026;10,00;1,00;10,00"
                )
            )

    def test_invalid_decimal_reports_line_and_column(self):
        with pytest.raises(TesouroDataError, match="Linha 2.*PU"):
            parse_vendas(
                _csv("Tesouro Selic;02/01/2029;01/10/2026;abc;1,00;10,00")
            )

    def test_empty_csv_is_rejected(self):
        with pytest.raises(TesouroDataError):
            parse_vendas(b"")

    def test_header_only_is_rejected(self):
        with pytest.raises(TesouroDataError, match="sem registros"):
            parse_vendas(HEADER.encode())

    def test_unknown_column_is_ignored(self):
        data = (
            HEADER
            + ";Extra\n"
            + "Tesouro Selic;02/01/2029;01/10/2026;10,00;1,00;10,00;x\n"
        ).encode()
        assert len(parse_vendas(data)) == 1


class TestFiltersAggregationSorting:
    def test_filter_by_title_is_partial_and_accent_insensitive(self):
        sales = _sales()
        assert len(filtrar_por_titulo(sales, "ipca")) == 1
        assert len(filtrar_por_titulo(sales, "SELIC")) == 2
        assert len(filtrar_por_titulo(sales, None)) == 3

    def test_filter_by_period_is_inclusive(self):
        sales = _sales()
        result = filtrar_por_periodo(sales, "2026-10-02", "2026-10-02")
        assert len(result) == 1
        assert result[0].tipo_titulo == "Tesouro IPCA+ 2035"

    def test_aggregate_uses_weighted_pu(self):
        aggregated = agregar_por_titulo(_sales())
        selic = next(item for item in aggregated if "Selic" in item.tipo_titulo)

        assert selic.quantidade == Decimal("5.00")
        assert selic.valor == Decimal("72000.00")
        assert selic.pu_medio == Decimal("14400.00")

    def test_sorting_is_deterministic(self):
        ordered = ordenar_vendas(_sales())

        assert ordered[0].data_liquidacao == "2026-10-02"
        assert [item.pu for item in ordered[1:]] == [
            Decimal("14000.00"),
            Decimal("15000.00"),
        ]

    def test_default_and_partial_periods(self):
        sales = _sales()
        assert resolver_periodo(sales, None, None) == (
            "2026-09-02",
            "2026-10-02",
        )
        assert resolver_periodo(sales, None, "2026-10-02") == (
            "2026-09-02",
            "2026-10-02",
        )
        assert resolver_periodo(sales, "2026-10-01", None) == (
            "2026-10-01",
            "2026-10-02",
        )

    @pytest.mark.parametrize("inicio,fim", [("2026-1-01", None), (None, "x")])
    def test_invalid_period_date(self, inicio, fim):
        with pytest.raises(PeriodoInvalidoError):
            validar_periodo(inicio, fim)

    def test_inverted_period(self):
        with pytest.raises(PeriodoInvalidoError):
            validar_periodo("2026-10-02", "2026-10-01")


class TestFormatting:
    def test_sales_csv_format(self):
        content = format_vendas_csv(_sales())
        lines = content.splitlines()

        assert lines[0] == (
            "TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR"
        )
        assert "15000.000000;2.00;30000.00" in lines[1]

    def test_empty_sales_csv_has_header(self):
        assert format_vendas_csv([]).splitlines() == [
            "TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR"
        ]

    def test_aggregate_csv_format(self):
        content = format_agregados_csv(agregar_por_titulo(_sales()))

        assert content.splitlines()[0] == (
            "TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO"
        )

    def test_json_payloads(self):
        metadata = {
            "resource_id": "r1",
            "checked_at": "2026-10-20T00:00:00+00:00",
            "last_modified": "2026-10-16T10:29:05",
            "last_data_date": "2026-10-02",
        }
        sales = _sales()
        sales_payload = build_vendas_payload(
            sales, metadata, {"inicio": "2026-10-01", "fim": "2026-10-02"}
        )
        aggregate_payload = build_agregados_payload(
            agregar_por_titulo(sales),
            metadata,
            {"inicio": "2026-10-01", "fim": "2026-10-02"},
            len(sales),
        )

        assert sales_payload["registros"][0]["pu"] == "15000.000000"
        assert sales_payload["data_maxima_liquidacao"] == "2026-10-02"
        assert "registros" not in aggregate_payload
        assert aggregate_payload["total_agregados"] == 2
        assert aggregate_payload["total_registros"] == 3
