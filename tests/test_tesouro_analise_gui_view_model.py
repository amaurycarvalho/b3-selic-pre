from decimal import Decimal

from b3_selic_pre.application.tesouro import TesouroSeriesProvider
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)
from b3_selic_pre.presentation.tesouro_analise_view_model import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
    ComparisonChart,
    EvolutionChart,
    GapChart,
    ShareChart,
    TesouroAnaliseViewModel,
)


def _estoque(titulo, mes, valor, vencimento="2029-01-02"):
    return EstoqueTesouroDireto(
        titulo, vencimento, mes, Decimal("1"), Decimal("1"), Decimal(valor)
    )


def _venda(titulo, data, valor, vencimento="2029-01-02"):
    return VendaTesouroDireto(
        titulo, vencimento, data, Decimal("1"), Decimal("1"), Decimal(valor)
    )


def _provider():
    return TesouroSeriesProvider(
        vendas=[
            _venda("Tesouro Selic 2029", "2026-10-02", "60"),
            _venda("Tesouro IPCA+ 2035", "2026-10-02", "40"),
            _venda("Tesouro Selic 2029", "2026-08-03", "10"),
        ],
        resgates=[
            ResgateTesouroDireto(
                "recompra", "Tesouro Selic 2029", "2029-01-02",
                "2026-10-02", None, Decimal("1"), Decimal("5"),
            )
        ],
        estoque=[
            _estoque("Tesouro Selic 2029", "2026-09", "60"),
            _estoque("Tesouro IPCA+ 2035", "2026-09", "40"),
            _estoque("Tesouro Selic 2029", "2026-10", "70"),
            _estoque("Tesouro IPCA+ 2035", "2026-10", "30"),
        ],
    )


def _view_model(kind, window="14d", latest="2026-10-02"):
    return TesouroAnaliseViewModel(
        kind=kind,
        window=window,
        provider=_provider(),
        titles=("Tesouro Selic 2029", "Tesouro IPCA+ 2035"),
        latest_data_date=latest,
        has_data=True,
    )


def test_estoque_current_share_uses_latest_month_and_sums_100():
    chart = _view_model(KIND_ESTOQUE).current_chart()

    assert isinstance(chart, ShareChart)
    assert chart.families == ("SELIC", "IPCA")
    assert chart.totals["SELIC"] == 70
    assert chart.totals["IPCA"] == 30
    assert chart.segments["SELIC"]["Tesouro Selic 2029"] == 70


def test_estoque_evolution_is_monthly_and_sums_100():
    chart = _view_model(KIND_ESTOQUE, window="12m").evolution_chart()

    assert isinstance(chart, EvolutionChart)
    assert "2026-10" in chart.periods
    index = chart.periods.index("2026-10")
    total = sum(series[index] for series in chart.series.values())
    assert total == 100


def test_apetite_current_aggregates_window():
    chart = _view_model(KIND_APETITE).current_chart()

    assert isinstance(chart, ShareChart)
    assert chart.totals["SELIC"] == 60
    assert chart.totals["IPCA"] == 40


def test_visao_geral_compares_stock_and_appetite():
    chart = _view_model(KIND_VISAO_GERAL).current_chart()

    assert isinstance(chart, ComparisonChart)
    assert chart.families == ("SELIC", "IPCA")
    assert chart.estoque == (70, 30)
    assert chart.apetite == (60, 40)


def test_visao_geral_gap_is_appetite_minus_stock():
    chart = _view_model(KIND_VISAO_GERAL, window="12m").evolution_chart()

    assert isinstance(chart, GapChart)
    index = chart.periods.index("2026-10")
    assert chart.series["SELIC"][index] == -10
    assert chart.series["IPCA"][index] == 10


def test_window_is_anchored_on_latest_date_and_has_no_future_periods():
    view_model = _view_model(KIND_APETITE, window="3a")

    chart = view_model.evolution_chart()

    assert isinstance(chart, EvolutionChart)
    assert max(chart.periods) <= "2026-10"


def test_status_and_controls_reflect_loading_and_cache():
    view_model = _view_model(KIND_ESTOQUE)
    view_model.source = "Cache"
    view_model.extracted_at = "2026-10-20T00:00:00+00:00"

    assert "Fonte: Cache" in view_model.status_text
    assert "2026-10" in view_model.status_text
    assert view_model.can_refresh

    view_model.loading = True
    assert not view_model.can_refresh
    assert view_model.status_kind == "info"


def test_empty_state_guides_refresh_and_has_no_charts():
    view_model = TesouroAnaliseViewModel(kind=KIND_ESTOQUE, has_data=False)

    assert "Atualizar" in view_model.empty_message
    assert view_model.status_kind == "warning"
    assert view_model.current_chart() is None
    assert view_model.evolution_chart() is None


def test_visao_geral_titles_use_the_new_wording():
    current = _view_model(KIND_VISAO_GERAL).current_chart()
    evolution = _view_model(KIND_VISAO_GERAL).evolution_chart()

    assert current.title.startswith("Estoque vs Apetite do mercado (")
    assert evolution.title.startswith("Gap Apetite menos Estoque (")


def test_estoque_and_apetite_evolution_enable_vertical_grid():
    estoque = _view_model(KIND_ESTOQUE, window="12m").evolution_chart()
    apetite = _view_model(KIND_APETITE, window="3m").evolution_chart()

    assert estoque.vertical_grid is True
    assert apetite.vertical_grid is True


def test_placeholder_guides_refresh_without_cache():
    view_model = TesouroAnaliseViewModel(kind=KIND_ESTOQUE, has_data=False)
    view_model.loading = True

    assert view_model.placeholder_message == view_model.empty_message
    assert "Pressione Atualizar" in view_model.status_text
    assert view_model.status_kind == "warning"


def test_placeholder_reports_loading_when_cache_exists():
    view_model = TesouroAnaliseViewModel(
        kind=KIND_ESTOQUE, has_data=False, cache_available=True
    )
    view_model.loading = True

    assert view_model.placeholder_message == "Carregando dados do Tesouro…"
    assert view_model.status_text == "Carregando dados do Tesouro…"
    assert view_model.status_kind == "info"


def test_placeholder_disappears_when_data_exists():
    view_model = _view_model(KIND_ESTOQUE)

    assert view_model.placeholder_message is None
