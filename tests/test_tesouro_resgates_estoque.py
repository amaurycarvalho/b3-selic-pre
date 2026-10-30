from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import (
    PeriodoInvalidoError,
    TesouroDataError,
    agregar_estoque,
    agregar_resgates,
    build_estoque_agregados_payload,
    build_estoque_payload,
    build_resgates_agregados_payload,
    build_resgates_payload,
    combine_metadata,
    filtrar_estoque_por_periodo,
    filtrar_estoque_por_titulo,
    filtrar_resgates_por_periodo,
    filtrar_resgates_por_tipo,
    filtrar_resgates_por_titulo,
    format_estoque_agregados_csv,
    format_estoque_csv,
    format_resgates_agregados_csv,
    format_resgates_csv,
    meses_presentes,
    ordenar_estoque,
    ordenar_resgates,
    parse_estoque,
    parse_resgates,
    resolver_periodo_estoque,
    resolver_periodo_resgates,
    validar_meses,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
)

RECOMPRA_HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade;Valor"
)
RESGATE_HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor"
)
ESTOQUE_HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;Valor Estoque"
)


def _csv(header: str, *rows: str) -> bytes:
    return ("\n".join((header, *rows)) + "\n").encode("utf-8")


def _recompras():
    return parse_resgates(
        _csv(
            RECOMPRA_HEADER,
            "Tesouro Selic 2029;02/01/2029;01/10/2026;2,00;30.000,00",
            "Tesouro IPCA+ 2035;15/05/2035;02/10/2026;1,00;3.000,00",
            "Tesouro Selic 2029;02/01/2029;01/10/2026;3,00;42.000,00",
        ),
        "recompra",
    )


def _cupons():
    return parse_resgates(
        _csv(
            RESGATE_HEADER,
            "Tesouro IPCA+ 2035;15/05/2035;01/10/2026;3.000,00;1,00;3.000,00",
            "Tesouro IPCA+ 2035;15/05/2035;02/10/2026;2.000,00;2,00;4.000,00",
        ),
        "cupom",
    )


def _estoque():
    return parse_estoque(
        _csv(
            ESTOQUE_HEADER,
            "Tesouro Selic 2029;02/01/2029;09/2026;15.000,00;2,00;30.000,00",
            "Tesouro Selic 2029;02/01/2029;09/2026;14.000,00;3,00;42.000,00",
            "Tesouro Selic 2029;02/01/2029;08/2026;13.000,00;1,00;13.000,00",
        )
    )


class TestModels:
    def test_resgate_is_immutable(self):
        record = ResgateTesouroDireto(
            "recompra",
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-10-01",
            None,
            Decimal("1"),
            Decimal("10"),
        )
        with pytest.raises(AttributeError):
            record.valor = Decimal("2")

    def test_estoque_is_immutable(self):
        record = EstoqueTesouroDireto(
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-09",
            Decimal("1"),
            Decimal("1"),
            Decimal("10"),
        )
        with pytest.raises(AttributeError):
            record.mes = "2026-08"


class TestParsing:
    def test_recompra_has_no_pu(self):
        records = _recompras()

        assert records[0].tipo_resgate == "recompra"
        assert records[0].pu is None
        assert records[0].data_resgate == "2026-10-01"
        assert records[0].quantidade == Decimal("2.00")
        assert records[0].valor == Decimal("30000.00")

    def test_cupom_has_pu(self):
        records = _cupons()

        assert records[0].tipo_resgate == "cupom"
        assert records[0].pu == Decimal("3000.00")

    def test_estoque_month_is_converted(self):
        records = _estoque()

        assert records[0].mes == "2026-09"
        assert records[0].valor_estoque == Decimal("30000.00")
        assert records[0].vencimento == "2029-01-02"

    def test_rejects_invalid_redemption_type(self):
        with pytest.raises(TesouroDataError):
            parse_resgates(_csv(RECOMPRA_HEADER), "invalido")

    def test_missing_column(self):
        data = _csv(
            "Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade",
            "Tesouro Selic;02/01/2029;01/10/2026;1,00",
        )
        with pytest.raises(TesouroDataError, match="Valor"):
            parse_resgates(data, "recompra")

    def test_invalid_date_reports_line_and_column(self):
        data = _csv(
            RESGATE_HEADER,
            "Tesouro Selic;31/02/2029;01/10/2026;1,00;1,00;1,00",
        )
        with pytest.raises(TesouroDataError, match="Linha 2.*data inválida"):
            parse_resgates(data, "cupom")

    def test_invalid_month_reports_line_and_column(self):
        data = _csv(
            ESTOQUE_HEADER,
            "Tesouro Selic;02/01/2029;13/2026;1,00;1,00;1,00",
        )
        with pytest.raises(TesouroDataError, match="Linha 2.*mês inválido"):
            parse_estoque(data)

    def test_invalid_decimal_reports_line_and_column(self):
        data = _csv(
            RECOMPRA_HEADER,
            "Tesouro Selic;02/01/2029;01/10/2026;abc;1,00",
        )
        with pytest.raises(TesouroDataError, match="Linha 2.*Quantidade"):
            parse_resgates(data, "recompra")

    def test_empty_and_header_only_are_rejected(self):
        with pytest.raises(TesouroDataError):
            parse_estoque(b"")
        with pytest.raises(TesouroDataError, match="sem registros"):
            parse_estoque(ESTOQUE_HEADER.encode())

    def test_unknown_column_is_ignored(self):
        data = (
            RECOMPRA_HEADER
            + ";Extra\n"
            + "Tesouro Selic;02/01/2029;01/10/2026;1,00;10,00;x\n"
        ).encode()
        assert len(parse_resgates(data, "recompra")) == 1

    def test_accepts_latin1_accented_header(self):
        text = (
            "Tipo Título;Vencimento do Título;Data Resgate;Quantidade;Valor\n"
            "Tesouro Ação;02/01/2029;01/10/2026;1,00;10,00\n"
        )
        records = parse_resgates(text.encode("latin-1"), "recompra")
        assert records[0].tipo_titulo == "Tesouro Ação"


class TestResgatesProcessing:
    def test_filters(self):
        records = _recompras()
        assert len(filtrar_resgates_por_tipo(records, "recompra")) == 3
        assert filtrar_resgates_por_tipo(records, "cupom") == []
        assert len(filtrar_resgates_por_titulo(records, "ipca")) == 1
        assert len(
            filtrar_resgates_por_periodo(
                records, "2026-10-02", "2026-10-02"
            )
        ) == 1

    def test_default_and_partial_periods(self):
        records = _recompras()
        assert resolver_periodo_resgates(records, None, None) == (
            "2026-09-02",
            "2026-10-02",
        )
        assert resolver_periodo_resgates(records, None, "2026-10-02") == (
            "2026-09-02",
            "2026-10-02",
        )
        assert resolver_periodo_resgates(
            records, "2026-10-01", None
        ) == ("2026-10-01", "2026-10-02")

    def test_sorting(self):
        ordered = ordenar_resgates(_recompras())
        assert ordered[0].data_resgate == "2026-10-02"
        assert ordered[1].valor == Decimal("30000.00")

    def test_aggregation_of_recompras_has_no_pu(self):
        aggregated = agregar_resgates(_recompras())
        selic = next(item for item in aggregated if "Selic" in item.tipo_titulo)
        assert selic.quantidade == Decimal("5.00")
        assert selic.valor == Decimal("72000.00")
        assert selic.pu_medio is None

    def test_aggregation_of_cupons_uses_weighted_pu(self):
        aggregated = agregar_resgates(_cupons())
        assert aggregated[0].pu_medio == Decimal("7000.00") / Decimal("3.00")

    def test_empty_aggregation(self):
        assert agregar_resgates([]) == []


class TestEstoqueProcessing:
    def test_filters_and_default_month(self):
        records = _estoque()
        assert len(filtrar_estoque_por_titulo(records, "selic")) == 3
        assert len(filtrar_estoque_por_periodo(records, "2026-08", "2026-08")) == 1
        assert resolver_periodo_estoque(records, None, None, None) == (
            "2026-09",
            "2026-09",
        )
        assert resolver_periodo_estoque(records, None, None, "2026-08") == (
            "2026-08",
            "2026-08",
        )

    def test_sorting_and_months(self):
        ordered = ordenar_estoque(_estoque())
        assert ordered[0].mes == "2026-09"
        assert ordered[-1].mes == "2026-08"
        assert meses_presentes(ordered) == ["2026-08", "2026-09"]

    def test_aggregation_requires_single_month(self):
        with pytest.raises(PeriodoInvalidoError):
            agregar_estoque(_estoque())

    def test_aggregation_within_one_month(self):
        records = [
            item for item in _estoque() if item.mes == "2026-09"
        ]
        aggregated = agregar_estoque(records)
        assert aggregated[0].quantidade == Decimal("5.00")
        assert aggregated[0].valor_estoque == Decimal("72000.00")
        assert aggregated[0].pu_medio == Decimal("14400.00")
        assert agregar_estoque([]) == []

    @pytest.mark.parametrize("inicio,fim", [("2026-1", None), (None, "x")])
    def test_invalid_month(self, inicio, fim):
        with pytest.raises(PeriodoInvalidoError):
            validar_meses(inicio, fim)

    def test_inverted_months(self):
        with pytest.raises(PeriodoInvalidoError):
            validar_meses("2026-10", "2026-09")


class TestFormatting:
    def test_resgates_csv(self):
        content = format_resgates_csv(_recompras())
        lines = content.splitlines()
        assert lines[0] == (
            "TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;"
            "PU;QUANTIDADE;VALOR"
        )
        assert "recompra;Tesouro Selic 2029;2029-01-02;2026-10-01;;" in lines[1]

    def test_resgates_empty_and_aggregate_csv(self):
        assert format_resgates_csv([]).splitlines() == [
            "TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;"
            "PU;QUANTIDADE;VALOR"
        ]
        content = format_resgates_agregados_csv(agregar_resgates(_cupons()))
        assert content.splitlines()[0] == (
            "TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO"
        )

    def test_estoque_csv(self):
        content = format_estoque_csv(_estoque())
        assert content.splitlines()[0] == (
            "TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE"
        )
        assert "2026-09;15000.000000;2.00;30000.00" in content

    def test_estoque_empty_and_aggregate_csv(self):
        assert format_estoque_csv([]).splitlines() == [
            "TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE"
        ]
        records = [item for item in _estoque() if item.mes == "2026-09"]
        content = format_estoque_agregados_csv(agregar_estoque(records))
        assert content.splitlines()[0] == (
            "TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO"
        )

    def test_json_payloads(self):
        metadata = {
            "resource_id": "r1,r2,r3",
            "checked_at": "2026-10-20T00:00:00+00:00",
            "last_modified": "2026-10-16T10:29:05",
            "last_data_date": "2026-10-02",
        }
        periodo = {"inicio": "2026-10-01", "fim": "2026-10-02"}
        resgates = build_resgates_payload(_recompras(), metadata, periodo)
        agregados = build_resgates_agregados_payload(
            agregar_resgates(_recompras()),
            metadata,
            periodo,
            len(_recompras()),
        )

        assert resgates["dataset"] == "resgates"
        assert resgates["registros"][0]["tipo_resgate"] == "recompra"
        assert resgates["registros"][0]["pu"] is None
        assert "registros" not in agregados
        assert agregados["agregados"][0]["pu_medio"] == ""

    def test_estoque_json_payloads(self):
        metadata = {
            "resource_id": "r4",
            "checked_at": "2026-10-20T00:00:00+00:00",
            "last_modified": "2026-10-16T10:29:05",
            "last_data_date": "2026-09",
        }
        periodo = {"inicio": "2026-09", "fim": "2026-09", "mes": None}
        records = [item for item in _estoque() if item.mes == "2026-09"]
        payload = build_estoque_payload(records, metadata, periodo)
        aggregate = build_estoque_agregados_payload(
            agregar_estoque(records), metadata, periodo, len(records)
        )

        assert payload["dataset"] == "estoque"
        assert payload["registros"][0]["mes"] == "2026-09"
        assert payload["ultimo_mes"] == "2026-09"
        assert aggregate["total_agregados"] == 1

    def test_combine_metadata(self):
        combined = combine_metadata({
            "a": {"resource_id": "a", "checked_at": "2", "last_data_date": "1"},
            "b": {"resource_id": "b", "checked_at": "1", "last_data_date": "2"},
        })
        assert combined["checked_at"] == "2"
        assert combined["last_data_date"] == "2"
        assert combined["resource_id"] == "a,b"
