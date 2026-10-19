"""Testes headless dos serviços de aplicação compartilhados por GUI e CLI."""

from unittest import mock

import pytest

from b3_selic_pre.application.analyze import CurvaJurosConfig, EvolutionConfig
from b3_selic_pre.application.use_cases import (
    FutureQueryDateError,
    OldQueryDateError,
    build_export_text,
    build_rates_table,
    create_shortcut_with_message,
    days_ago,
    evolution_dates,
    nearest_business_day,
    rate_statistics,
    resolve_reference_date,
    validate_query_date,
)
from b3_selic_pre.domain.models import RateRecord


def _records(*rates):
    return [
        RateRecord(day252=i + 1, day360=(i + 1) * 30, rate=str(rate).replace(".", ","))
        for i, rate in enumerate(rates)
    ]


class TestQueryDateValidation:
    def test_accepts_valid_date(self):
        assert validate_query_date("2026-06-10", today="2026-06-17") == "2026-06-10"

    def test_rejects_invalid_format(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            validate_query_date("10/06/2026", today="2026-06-17")

    def test_rejects_future_date(self):
        with pytest.raises(FutureQueryDateError, match="Data futura"):
            validate_query_date("2026-06-18", today="2026-06-17")

    def test_rejects_date_older_than_window(self):
        with pytest.raises(OldQueryDateError, match="Data muito antiga"):
            validate_query_date("2026-05-01", today="2026-06-17")

    def test_accepts_boundary_of_window(self):
        assert validate_query_date("2026-05-18", today="2026-06-17") == "2026-05-18"


class TestCalendarHelpers:
    def test_nearest_business_day_retreats_from_weekend(self):
        assert nearest_business_day("2026-06-14") == "2026-06-12"

    def test_nearest_business_day_keeps_weekday(self):
        assert nearest_business_day("2026-06-15") == "2026-06-15"

    def test_nearest_business_day_rejects_invalid_date(self):
        with pytest.raises(ValueError):
            nearest_business_day("14/06/2026")

    def test_days_ago(self):
        assert days_ago("2026-06-17", 0) == "2026-06-17"
        assert days_ago("2026-06-17", 7) == "2026-06-10"
        assert days_ago("2026-06-17", 28) == "2026-05-20"

    def test_evolution_dates_uses_configured_window(self):
        assert evolution_dates("2026-06-17") == [
            "2026-05-20",
            "2026-05-27",
            "2026-06-03",
            "2026-06-10",
            "2026-06-17",
        ]


class TestRateStatistics:
    def test_empty_returns_none(self):
        assert rate_statistics([]) is None

    def test_min_and_max(self):
        stats = rate_statistics(_records(14.5, 15.25, 13.75))
        assert stats is not None
        assert stats.min_rate == 13.75
        assert stats.max_rate == 15.25


class TestExportServices:
    def test_rates_table_raw(self):
        text = build_rates_table(_records(14.5))
        assert text == 'DU252,DC365,TAXA\n1,30,"14,5"\n'

    def test_rates_table_yearly(self):
        text = build_rates_table(_records(14.5), yearly=True)
        assert text == "ANO,MENOR_TAXA,MAIOR_TAXA\n0,\"14,50\",\"14,50\"\n"

    def test_export_text_none_without_data(self):
        assert build_export_text([]) is None

    def test_export_text_raw(self):
        records = _records(14.5)
        assert build_export_text(records) == build_rates_table(records)

    def test_export_text_consolidated(self):
        records = _records(14.5)
        assert build_export_text(records, view_mode="consolidated") == build_rates_table(
            records, yearly=True
        )

    def test_export_text_evolution_uses_historical_data(self):
        records = _records(14.5)
        historical = {"2026-06-10": records, "2026-06-17": records}
        text = build_export_text(
            records,
            historical_data=historical,
            evolution_active=True,
        )
        assert text is not None
        assert text.startswith("DATA;ANO;TAXA_MEDIA\n")
        assert "2026-06-17;0;14.50" in text

    def test_export_text_evolution_without_history_falls_back(self):
        records = _records(14.5)
        assert build_export_text(
            records, historical_data=None, evolution_active=True
        ) == build_rates_table(records)


class TestReferenceDateResolution:
    def test_explicit_date(self):
        assert resolve_reference_date("2026-06-10") == "2026-06-10"

    def test_today_flag(self):
        with mock.patch(
            "b3_selic_pre.application.use_cases.default_reference_date",
            return_value="2026-06-17",
        ):
            assert resolve_reference_date(None, use_today=True) == "2026-06-17"

    def test_defaults_to_current_date(self):
        with mock.patch(
            "b3_selic_pre.application.use_cases.default_reference_date",
            return_value="2026-06-17",
        ):
            assert resolve_reference_date() == "2026-06-17"


class TestShortcutService:
    def test_calls_creator_and_returns_message(self):
        creator = mock.Mock()
        message = create_shortcut_with_message(creator)
        creator.assert_called_once_with()
        assert message == "Atalho criado em ~/Desktop/ e ~/.local/share/applications/."


class TestConfigFromMapping:
    def test_curva_juros_defaults(self):
        config = CurvaJurosConfig.from_mapping()
        assert config.expected_inflation == 3.0
        assert config.evolucao.movement_threshold_bps == 5.0

    def test_curva_juros_overrides(self):
        config = CurvaJurosConfig.from_mapping(
            {
                "expected_inflation": 4.0,
                "faixas_nominais": [5.0, 8.0, 10.0, 12.0],
                "stability_window": 3,
            },
            {"movement_threshold_bps": 10.0},
        )
        assert config.expected_inflation == 4.0
        assert config.faixas_nominais == [5.0, 8.0, 10.0, 12.0]
        assert config.stability_window == 3
        assert config.evolucao.movement_threshold_bps == 10.0

    def test_evolution_config_from_mapping(self):
        config = EvolutionConfig.from_mapping({"weak_max": 12.0})
        assert config.weak_max == 12.0
        assert config.moderate_max == 30.0
