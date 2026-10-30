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
    assert controller.error_context is None
    assert controller.view_model().status_kind == "warning"


def test_cache_read_failure_uses_cache_error_context():
    def loader(cache_only, force):
        raise OSError("disco indisponível")

    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE, loader=loader
    )

    controller.load(cache_only=True)

    view_model = controller.view_model()
    assert controller.error == "disco indisponível"
    assert controller.error_context == "ler o cache"
    assert view_model.status_text == (
        "Erro ao ler o cache: disco indisponível"
    )


def test_retry_hides_previous_error_while_loading():
    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE,
        loader=lambda cache_only, force: _data(),
    )
    controller.load(cache_only=True)

    def failing_refresh(cache_only, force):
        raise RuntimeError("falha anterior")

    controller.loader = failing_refresh
    controller.load(force=True)
    assert controller.error == "falha anterior"

    seen = []

    def retry(cache_only, force):
        view_model = controller.view_model()
        seen.append(
            (view_model.loading, view_model.error, view_model.status_text)
        )
        return _data()

    controller.loader = retry
    controller.load(force=True)

    assert seen == [(True, None, "Atualizando dados do Tesouro…")]
    assert controller.error is None


def test_begin_load_clears_previous_error():
    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE,
        loader=lambda cache_only, force: _data(),
    )
    controller.error = "falha anterior"
    controller.error_context = "ler o cache"

    controller.begin_load()

    view_model = controller.view_model()
    assert controller.loading
    assert controller.loading_origin == "network"
    assert controller.error is None
    assert controller.error_context is None
    assert "falha anterior" not in view_model.status_text
    assert view_model.status_kind == "info"


def test_note_cache_presence_only_requests_reload_on_absent_to_present():
    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE, loader=lambda cache_only, force: None
    )

    assert controller.note_cache_presence(False) is False
    assert controller.note_cache_presence(True) is True
    assert controller.note_cache_presence(True) is False


def test_note_cache_presence_ignores_loading_or_existing_data():
    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE, loader=lambda cache_only, force: _data()
    )
    controller.load(cache_only=True)

    assert controller.note_cache_presence(False) is False
    assert controller.note_cache_presence(True) is False

    other = TesouroAnaliseController(
        kind=KIND_ESTOQUE, loader=lambda cache_only, force: None
    )
    other.loading = True
    assert other.note_cache_presence(True) is False


def test_load_forwards_stage_callback_to_three_position_loader():
    stages = []

    def loader(cache_only, force, stage_callback=None):
        stage_callback("vendas")
        stage_callback("estoque")
        return _data()

    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE, loader=loader
    )

    controller.load(force=True, stage_callback=stages.append)

    assert stages == ["vendas", "estoque"]


def test_two_position_loader_remains_compatible_with_stage_callback():
    controller = TesouroAnaliseController(
        kind=KIND_ESTOQUE,
        loader=lambda cache_only, force: _data(),
    )

    data = controller.load(force=True, stage_callback=lambda stage: None)

    assert data is not None
    assert controller.error is None


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


class StubProvider:
    def __init__(self):
        self.calls = []

    def fetch(self, key, start, end, bucket):
        from b3_selic_pre.application.tesouro import (
            METRICA_FLUXO_LIQUIDO,
            SeriesPoint,
        )

        self.calls.append((key, start, end, bucket))
        if key.key == "SELIC":
            return [
                SeriesPoint(
                    "2026-10-02",
                    METRICA_FLUXO_LIQUIDO,
                    Decimal("55"),
                    Decimal("100"),
                    key.dimension,
                    key.key,
                )
            ]
        return []


def test_ready_provider_is_used_without_rebuilding():
    provider = StubProvider()

    def factory(**kwargs):
        raise AssertionError("factory não deveria ser chamada")

    controller = TesouroAnaliseController(
        kind=KIND_APETITE,
        loader=lambda cache_only, force: AnaliseData(
            provider=provider,
            titles=("Tesouro Selic 2029",),
            latest_data_date="2026-10-02",
            fluxo_latest_data_date="2026-10-02",
        ),
        provider_factory=factory,
    )
    controller.load(cache_only=True)

    view_model = controller.view_model()

    assert view_model.provider is provider
    assert view_model.titles == ("Tesouro Selic 2029",)
    assert "55.00" in (view_model.fluxo_liquido or "")


def test_window_change_does_not_call_the_loader_again():
    calls = []

    def loader(cache_only, force):
        calls.append((cache_only, force))
        return _data()

    controller = TesouroAnaliseController(kind=KIND_APETITE, loader=loader)
    controller.load(cache_only=True)
    controller.set_window("3m")
    controller.view_model().current_chart()

    assert calls == [(True, False)]
