import base64
from dataclasses import dataclass

import pytest

from b3_selic_pre.application import mcp_pagination, mcp_services
from b3_selic_pre.domain.models import RateRecord


def _records(*rates):
    return [
        RateRecord(day252=i + 1, day360=(i + 1) * 365, rate=str(rate))
        for i, rate in enumerate(rates)
    ]


def _historical():
    return {
        "2026-06-10": _records(10.0, 20.0),
        "2026-06-17": _records(12.0, 22.0),
        "2026-06-24": [],
    }


class TestPagination:
    def test_first_page_and_next_cursor(self):
        page, cursor = mcp_services.paginate([1, 2, 3], None, 2)
        assert page == [1, 2]
        assert cursor is not None
        assert mcp_pagination.decode_cursor(cursor) == 2

    def test_last_page_has_no_cursor(self):
        page, cursor = mcp_services.paginate([1, 2, 3], None, 3)
        assert page == [1, 2, 3]
        assert cursor is None

    def test_limit_is_clamped(self):
        page, _ = mcp_services.paginate(list(range(600)), None, 9999)
        assert len(page) == mcp_pagination.MAX_PAGE_SIZE

    @pytest.mark.parametrize("cursor", ["bad", "e30", base64.urlsafe_b64encode(b"[]").decode()])
    def test_invalid_cursor(self, cursor):
        with pytest.raises((ValueError, TypeError)):
            mcp_pagination.decode_cursor(cursor)

    def test_invalid_limit(self):
        with pytest.raises(ValueError):
            mcp_services.paginate([1], None, 0)


class TestCurvePayloads:
    def test_curta_items_are_numeric_and_keep_text(self):
        items = mcp_services.curve_items_curta([RateRecord(1, 30, "14,50")])
        assert items == [
            {"du252": 1, "dc365": 30, "taxa": 14.5, "taxa_texto": "14,50"}
        ]

    def test_longa_items_have_min_max_and_average(self):
        records = [
            RateRecord(1, 1, "10,00"),
            RateRecord(2, 2, "14,00"),
            RateRecord(3, 366, "20,00"),
            RateRecord(4, 367, "22,00"),
        ]
        items = mcp_services.curve_items_longa(records)
        assert items == [
            {
                "ano": 0,
                "menor_taxa": 10.0,
                "maior_taxa": 14.0,
                "taxa_media": 12.0,
            },
            {
                "ano": 1,
                "menor_taxa": 20.0,
                "maior_taxa": 22.0,
                "taxa_media": 21.0,
            },
        ]

    def test_curve_payload_paginates(self):
        records = _records(10.0, 11.0, 12.0)
        payload = mcp_services.curve_payload(
            records, "2026-06-10", "curta", None, 2
        )
        assert len(payload["itens"]) == 2
        assert "nextCursor" in payload

    def test_curve_payload_empty_raises(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            mcp_services.curve_payload([], "2026-06-10", "curta", None, None)
        assert exc.value.motivo == "sem_dados"


class TestExportPayloads:
    def test_curta_csv(self):
        payload = mcp_services.export_payload(
            _historical(), "2026-06-17", "curta"
        )
        assert payload["nome"] == "curva-curta.csv"
        assert payload["conteudo"].startswith("DATA;DU252;DC365;TAXA\n")
        assert payload["datas_indisponiveis"] == ["2026-06-24"]

    def test_longa_csv(self):
        payload = mcp_services.export_payload(
            _historical(), "2026-06-17", "longa"
        )
        assert payload["nome"] == "curva-longa.csv"
        assert "DATA;ANO;TAXA_MEDIA" in payload["conteudo"]

    def test_empty_export_raises(self):
        with pytest.raises(mcp_services.DomainError) as exc:
            mcp_services.export_payload({}, "2026-06-17", "curta")
        assert exc.value.motivo == "sem_dados"


class TestAnalysisPayload:
    def test_curta_analysis(self):
        historical = _historical()
        payload = mcp_services.analysis_payload(
            historical["2026-06-17"], historical, "2026-06-17", "curta"
        )
        assert payload["curva"] == "curta"
        assert "Análise da Curva" in payload["texto"]
        assert payload["datas_indisponiveis"] == ["2026-06-24"]

    def test_longa_analysis_uses_average(self):
        historical = {
            "2026-06-10": [
                RateRecord(1, 1, "10,00"),
                RateRecord(2, 2, "14,00"),
                RateRecord(3, 366, "20,00"),
                RateRecord(4, 367, "22,00"),
            ],
            "2026-06-17": [
                RateRecord(1, 1, "11,00"),
                RateRecord(2, 2, "15,00"),
                RateRecord(3, 366, "21,00"),
                RateRecord(4, 367, "23,00"),
            ],
        }
        payload = mcp_services.analysis_payload(
            historical["2026-06-17"], historical, "2026-06-17", "longa"
        )
        assert payload["curva"] == "longa"
        assert "Curva Longa" in payload["texto"]
        assert "13.00%" in payload["texto"] or "13,00%" in payload["texto"]

    def test_analysis_empty_raises(self):
        with pytest.raises(mcp_services.DomainError):
            mcp_services.analysis_payload([], {}, "2026-06-17", "curta")


class TestEvolutionAndStatistics:
    def test_evolution_items_and_missing_dates(self):
        payload = mcp_services.evolution_payload(
            _historical(), "2026-06-17", None, None
        )
        assert [item["data"] for item in payload["itens"]] == [
            "2026-06-10",
            "2026-06-17",
        ]
        assert payload["datas_indisponiveis"] == ["2026-06-24"]

    def test_evolution_paginates(self):
        payload = mcp_services.evolution_payload(
            _historical(), "2026-06-17", None, 1
        )
        assert len(payload["itens"]) == 1
        assert "nextCursor" in payload

    def test_evolution_empty_raises(self):
        with pytest.raises(mcp_services.DomainError):
            mcp_services.evolution_payload(
                {"2026-06-17": []}, "2026-06-17", None, None
            )

    def test_statistics(self):
        payload = mcp_services.statistics_payload(
            _records(10.0, 20.0), "2026-06-17"
        )
        assert payload["total_registros"] == 2
        assert payload["taxa_curta"] == 10.0
        assert payload["taxa_longa"] == 20.0
        assert payload["inclinacao_bps"] == 1000.0
        assert payload["juro_real"] == 7.0

    def test_statistics_empty_raises(self):
        with pytest.raises(mcp_services.DomainError):
            mcp_services.statistics_payload([], "2026-06-17")


@dataclass
class _Entry:
    date: str
    count: int
    cached_at: str | None
    source: str | None


class TestDatesAndReference:
    def test_dates_are_newest_first_and_paginated(self):
        entries = [
            _Entry("2026-06-10", 2, "a", "GetList"),
            _Entry("2026-06-17", 3, "b", "GetDownloadFile"),
        ]
        payload = mcp_services.dates_payload(entries, None, 1)
        assert payload["itens"][0]["data"] == "2026-06-17"
        assert "nextCursor" in payload

    def test_dates_empty_is_not_error(self):
        assert mcp_services.dates_payload([], None, None) == {"itens": []}

    def test_reference_payload(self):
        payload = mcp_services.reference_payload(
            "2026-06-17", "settings", True, cached_at="now"
        )
        assert payload == {
            "data_referencia": "2026-06-17",
            "origem": "settings",
            "disponivel": True,
            "cached_at": "now",
        }

    def test_domain_error_payload(self):
        error = mcp_services.DomainError("sem_dados", "detalhe", "dica")
        assert error.payload() == {
            "motivo": "sem_dados",
            "detalhe": "detalhe",
            "dica": "dica",
        }
