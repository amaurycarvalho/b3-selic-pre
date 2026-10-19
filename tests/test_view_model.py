"""Testes headless do view-model da interface gráfica."""

from b3_selic_pre.application.use_cases import build_rates_table
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation.view_model import (
    ChartMode,
    GuiViewModel,
    historical_status,
)


def _records(*rates):
    return [
        RateRecord(day252=i + 1, day360=(i + 1) * 30, rate=str(rate).replace(".", ","))
        for i, rate in enumerate(rates)
    ]


class TestEmptyState:
    def test_controls_disabled(self):
        model = GuiViewModel()
        controls = model.controls
        assert not controls.copy_enabled
        assert not controls.view_enabled
        assert not controls.evolution_enabled
        assert not controls.analysis_enabled
        assert not controls.three_d_enabled

    def test_empty_texts_and_export(self):
        model = GuiViewModel(reference_date="2026-06-17")
        assert model.stats_text == ""
        assert model.export_text is None
        assert model.chart_mode == ChartMode.RAW


class TestLoadedState:
    def test_controls_enabled_with_records(self):
        model = GuiViewModel(records=_records(14.5, 15.0))
        controls = model.controls
        assert controls.copy_enabled
        assert controls.view_enabled
        assert controls.evolution_enabled
        assert controls.analysis_enabled
        assert not controls.three_d_enabled

    def test_stats_text(self):
        model = GuiViewModel(
            records=_records(14.5, 15.0),
            reference_date="2026-06-17",
        )
        assert model.stats_text == "Data: 2026-06-17 | Maior: 15.00% | Menor: 14.50%"

    def test_raw_export(self):
        records = _records(14.5)
        model = GuiViewModel(records=records)
        assert model.export_text == build_rates_table(records)

    def test_consolidated_export_and_chart(self):
        records = _records(14.5)
        model = GuiViewModel(records=records, view_mode="consolidated")
        assert model.export_text == build_rates_table(records, yearly=True)
        assert model.chart_mode == ChartMode.CONSOLIDATED

    def test_error_state_after_clearing_records(self):
        model = GuiViewModel(
            records=[],
            historical_data=None,
            view_mode="consolidated",
        )
        assert not model.controls.copy_enabled
        assert model.export_text is None
        assert model.chart_mode == ChartMode.CONSOLIDATED


class TestEvolutionState:
    def test_evolution_requires_records_for_view_controls(self):
        historical = {"2026-06-17": _records(14.5)}
        model = GuiViewModel(
            records=[],
            historical_data=historical,
            evolution_active=True,
        )
        assert model.controls.copy_enabled
        assert not model.controls.evolution_enabled
        assert model.controls.three_d_enabled

    def test_evolution_curve_mode(self):
        historical = {"2026-06-17": _records(14.5)}
        model = GuiViewModel(
            records=_records(14.5),
            historical_data=historical,
            evolution_active=True,
            view_mode="consolidated",
        )
        assert model.chart_mode == ChartMode.EVOLUTION_CURVE

    def test_evolution_detailed_mode(self):
        historical = {"2026-06-17": _records(14.5)}
        model = GuiViewModel(
            records=_records(14.5),
            historical_data=historical,
            evolution_active=True,
            view_mode="raw",
        )
        assert model.chart_mode == ChartMode.EVOLUTION_DETAILED

    def test_evolution_3d_consolidated_mode(self):
        historical = {"2026-06-17": _records(14.5)}
        model = GuiViewModel(
            records=_records(14.5),
            historical_data=historical,
            evolution_active=True,
            show_3d=True,
            view_mode="consolidated",
        )
        assert model.chart_mode == ChartMode.EVOLUTION_3D_CONSOLIDATED

    def test_evolution_3d_detailed_mode(self):
        historical = {"2026-06-17": _records(14.5)}
        model = GuiViewModel(
            records=_records(14.5),
            historical_data=historical,
            evolution_active=True,
            show_3d=True,
            view_mode="raw",
        )
        assert model.chart_mode == ChartMode.EVOLUTION_3D_DETAILED

    def test_evolution_without_history_falls_back_to_raw(self):
        model = GuiViewModel(
            records=_records(14.5),
            historical_data=None,
            evolution_active=True,
            show_3d=True,
        )
        assert model.chart_mode == ChartMode.RAW

    def test_evolution_export_uses_history(self):
        records = _records(14.5)
        historical = {"2026-06-10": records, "2026-06-17": records}
        model = GuiViewModel(
            records=records,
            historical_data=historical,
            evolution_active=True,
        )
        assert model.export_text is not None
        assert model.export_text.startswith("DATA;ANO;TAXA_MEDIA\n")


class TestEmptyHistoricalData:
    def test_all_empty_historical_lists_fall_back_to_base(self):
        model = GuiViewModel(
            records=_records(14.5),
            historical_data={"2026-06-17": [], "2026-06-10": []},
            evolution_active=True,
            view_mode="consolidated",
        )
        assert not model.has_historical
        assert model.chart_mode == ChartMode.CONSOLIDATED
        assert not model.controls.three_d_enabled

    def test_one_usable_date_keeps_evolution_mode(self):
        records = _records(14.5)
        model = GuiViewModel(
            records=records,
            historical_data={"2026-06-17": [], "2026-06-10": records},
            evolution_active=True,
            view_mode="raw",
        )
        assert model.has_historical
        assert model.chart_mode == ChartMode.EVOLUTION_DETAILED
        assert model.controls.three_d_enabled

    def test_export_falls_back_when_history_is_empty(self):
        records = _records(14.5)
        model = GuiViewModel(
            records=records,
            historical_data={"2026-06-17": []},
            evolution_active=True,
        )
        assert model.export_text == build_rates_table(records)


class TestHistoricalStatus:
    def test_all_dates_available(self):
        records = _records(14.5)
        message, msg_type = historical_status(
            {"2026-06-17": records}, "Histórico B3", "12:00:00"
        )
        assert msg_type == "success"
        assert "1 datas, 1 registros" in message
        assert "indisponíveis" not in message

    def test_missing_dates_are_reported(self):
        records = _records(14.5)
        message, msg_type = historical_status(
            {"2026-06-10": [], "2026-06-17": records},
            "Histórico B3",
            "12:00:00",
        )
        assert msg_type == "warning"
        assert "2026-06-10" in message
        assert "indisponíveis" in message

    def test_all_dates_empty_is_error(self):
        message, msg_type = historical_status(
            {"2026-06-10": [], "2026-06-17": []},
            "Histórico B3",
            "12:00:00",
        )
        assert msg_type == "error"
        assert "0 datas" in message
        assert "indisponíveis" in message
