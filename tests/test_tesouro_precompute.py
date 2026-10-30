from decimal import Decimal

from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)
from b3_selic_pre.presentation.tesouro_analise_controller import AnaliseData
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
)
from b3_selic_pre.presentation.tesouro_precompute import TesouroPrecompute


def _data(**overrides):
    values = {
        "vendas": (
            VendaTesouroDireto(
                "Tesouro Selic 2029",
                "2029-01-02",
                "2026-10-02",
                Decimal("1"),
                Decimal("1"),
                Decimal("100"),
            ),
        ),
        "resgates": (
            ResgateTesouroDireto(
                "recompra",
                "Tesouro Selic 2029",
                "2029-01-02",
                "2026-10-02",
                None,
                Decimal("1"),
                Decimal("20"),
            ),
        ),
        "estoque": (
            EstoqueTesouroDireto(
                "Tesouro Selic 2029",
                "2029-01-02",
                "2026-10",
                Decimal("1"),
                Decimal("1"),
                Decimal("100"),
            ),
        ),
        "source": "Cache",
        "extracted_at": "2026-10-20T00:00:00",
    }
    values.update(overrides)
    return AnaliseData(**values)


class FakeCache:
    def __init__(self):
        self.calls = []

    def expected_hashes(self, name):
        return {"source": "hash"}

    def update_if_changed(
        self, name, hashes, build, *, source, extracted_at
    ):
        self.calls.append((name, build(), source, extracted_at))
        return True


def test_estoque_refresh_builds_only_stock():
    cache = FakeCache()

    TesouroPrecompute(cache)(KIND_ESTOQUE, _data())

    assert [item[0] for item in cache.calls] == ["estoque"]


def test_apetite_refresh_builds_demand_and_flow():
    cache = FakeCache()

    TesouroPrecompute(cache)(KIND_APETITE, _data(estoque=()))

    assert [item[0] for item in cache.calls] == ["demanda", "fluxo"]


def test_visao_geral_refresh_builds_stock_and_demand():
    cache = FakeCache()

    TesouroPrecompute(cache)(KIND_VISAO_GERAL, _data(resgates=()))

    assert [item[0] for item in cache.calls] == ["estoque", "demanda"]


def test_missing_raw_source_skips_snapshot():
    class MissingCache(FakeCache):
        def expected_hashes(self, name):
            return None

    cache = MissingCache()

    TesouroPrecompute(cache)(KIND_ESTOQUE, _data())

    assert cache.calls == []


def test_failure_is_isolated():
    class BrokenCache(FakeCache):
        def update_if_changed(self, *args, **kwargs):
            raise RuntimeError("falha")

    TesouroPrecompute(BrokenCache())(KIND_ESTOQUE, _data())


def test_none_cache_or_data_is_a_noop():
    TesouroPrecompute(None)(KIND_ESTOQUE, _data())
    TesouroPrecompute(FakeCache())(KIND_ESTOQUE, None)


def test_launch_wires_cache_and_precompute():
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "b3_selic_pre"
        / "presentation"
        / "gui"
        / "launch.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    keywords = {
        keyword.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "GuiDependencies"
        for keyword in node.keywords
    }

    assert "tesouro_series_cache" in keywords
    assert "tesouro_precompute" in keywords
