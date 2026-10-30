from decimal import Decimal

from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    VendaTesouroDireto,
)
from b3_selic_pre.presentation.tesouro_analise_controller import (
    AnaliseData,
    TesouroAnaliseController,
)
from b3_selic_pre.presentation.tesouro_analise_view_model import (
    KIND_APETITE,
    KIND_ESTOQUE,
)


def _data():
    return AnaliseData(
        vendas=(
            VendaTesouroDireto(
                "Tesouro Selic 2029", "2029-01-02", "2026-10-02",
                Decimal("1"), Decimal("1"), Decimal("100"),
            ),
        ),
        estoque=(
            EstoqueTesouroDireto(
                "Tesouro Selic 2029", "2029-01-02", "2026-10",
                Decimal("1"), Decimal("1"), Decimal("100"),
            ),
        ),
        latest_data_date="2026-10-02",
        source="Cache",
        extracted_at="2026-10-20T00:00:00+00:00",
    )


def test_cache_only_load_builds_view_model_without_force():
    calls = []

    def loader(cache_only, force):
        calls.append((cache_only, force))
        return _data()

    controller = TesouroAnaliseController(kind=KIND_ESTOQUE, loader=loader)
    controller.load(cache_only=True)

    assert calls == [(True, False)]
    assert controller.has_data
    assert controller.view_model().latest_data_date == "2026-10-02"


def test_refresh_failure_keeps_previous_data():
    calls = []

    def loader(cache_only, force):
        calls.append((cache_only, force))
        if not cache_only:
            raise RuntimeError("falha")
        return _data()

    controller = TesouroAnaliseController(kind=KIND_ESTOQUE, loader=loader)
    controller.load(cache_only=True)
    controller.load(force=True)

    assert calls == [(True, False), (False, True)]
    assert controller.has_data
    assert controller.error == "falha"


def test_cache_miss_is_not_an_error():
    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE, loader=lambda cache_only, force: None
    )

    controller.load(cache_only=True)

    assert not controller.has_data
    assert controller.error is None
    assert controller.view_model().status_kind == "warning"


def test_window_change_updates_view_model_and_rejects_invalid():
    controller = TesouroAnaliseController(
        kind=KIND_APETITE,
        loader=lambda cache_only, force: _data(),
    )
    controller.load(cache_only=True)

    controller.set_window("3m")

    assert controller.view_model().window == "3m"
    try:
        controller.set_window("2m")
    except ValueError:
        pass
    else:
        raise AssertionError("janela inválida aceita")


def test_apetite_exposes_net_flow_detail():
    controller = TesouroAnaliseController(
        kind=KIND_APETITE,
        loader=lambda cache_only, force: _data(),
    )
    controller.load(cache_only=True)

    view_model = controller.view_model()

    assert view_model.fluxo_liquido is not None
    assert "100.00" in view_model.fluxo_liquido
