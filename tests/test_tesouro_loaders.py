from decimal import Decimal

from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    VendaTesouroDireto,
)
from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
)
from b3_selic_pre.presentation.tesouro_loaders import (
    cache_available,
    make_loader,
)


def _stock():
    return (
        [
            EstoqueTesouroDireto(
                "Tesouro Selic 2029", "2029-01-02", "2026-10",
                Decimal("1"), Decimal("1"), Decimal("100"),
            )
        ],
        {"last_data_date": "2026-10", "checked_at": "2026-10-20T00:00:00"},
        "cache",
    )


def _sales():
    return (
        [
            VendaTesouroDireto(
                "Tesouro Selic 2029", "2029-01-02", "2026-10-02",
                Decimal("1"), Decimal("1"), Decimal("100"),
            )
        ],
        {"last_data_date": "2026-10-02", "checked_at": "2026-10-20T00:00:00"},
        "cache",
    )


class FakeClient:
    def __init__(self, has_stock=True, has_sales=True):
        self.calls = []
        self.has_stock = has_stock
        self.has_sales = has_sales

    def has_cached_estoque(self):
        return self.has_stock

    def has_cached_vendas(self):
        return self.has_sales

    def read_cached_estoque(self):
        self.calls.append("estoque")
        return _stock()

    def read_cached_vendas(self):
        self.calls.append("vendas")
        return _sales()

    def read_cached_resgates(self):
        self.calls.append("resgates")
        return [], {}, "cache"


class FakeNetworkClient:
    def __init__(self):
        self.calls = []

    def fetch_vendas(self, force=False):
        self.calls.append("vendas")
        return [], {}, "network"

    def fetch_resgates(self, force=False):
        self.calls.append("resgates")
        return [], {}, "network"

    def fetch_estoque(self, force=False):
        self.calls.append("estoque")
        return [], {}, "network"


def test_visao_geral_reads_only_stock_and_sales_from_cache():
    client = FakeClient()

    data = make_loader(client, KIND_VISAO_GERAL)(True, False)

    assert data is not None
    assert client.calls == ["estoque", "vendas"]
    assert data.resgates == ()


def test_estoque_reads_only_the_stock_cache():
    client = FakeClient()

    data = make_loader(client, KIND_ESTOQUE)(True, False)

    assert data is not None
    assert client.calls == ["estoque"]


def test_apetite_reads_sales_and_redemptions_from_cache():
    client = FakeClient()

    data = make_loader(client, KIND_APETITE)(True, False)

    assert data is not None
    assert client.calls == ["vendas", "resgates"]


def test_cache_miss_returns_none():
    client = FakeClient()
    client.read_cached_estoque = lambda: None

    assert make_loader(client, KIND_ESTOQUE)(True, False) is None


def test_cache_available_is_scoped_by_sub_tab():
    client = FakeClient(has_stock=True, has_sales=False)

    assert cache_available(client, KIND_ESTOQUE) is True
    assert cache_available(client, KIND_APETITE) is False
    assert cache_available(client, KIND_VISAO_GERAL) is False


def test_cache_available_without_client_is_false():
    assert cache_available(None, KIND_ESTOQUE) is False


def test_refresh_loader_emits_stages_before_each_network_call():
    stages = []
    client = FakeNetworkClient()

    make_loader(client, KIND_APETITE)(False, False, stages.append)

    assert stages == ["vendas", "resgates"]
    assert client.calls == ["vendas", "resgates"]


def test_estoque_refresh_loader_emits_only_the_stock_stage():
    stages = []
    client = FakeNetworkClient()

    make_loader(client, KIND_ESTOQUE)(False, False, stages.append)

    assert stages == ["estoque"]
    assert client.calls == ["estoque"]


def test_visao_geral_refresh_loader_emits_sales_then_stock_stages():
    stages = []
    client = FakeNetworkClient()

    make_loader(client, KIND_VISAO_GERAL)(False, False, stages.append)

    assert stages == ["vendas", "estoque"]
    assert client.calls == ["vendas", "estoque"]


def test_cache_only_loader_does_not_emit_network_stages():
    stages = []
    client = FakeClient()

    make_loader(client, KIND_ESTOQUE)(True, False, stages.append)

    assert stages == []


from b3_selic_pre.application.tesouro import (
    DIMENSAO_FAMILIA,
    METRICA_DEMANDA_PCT,
    SELIC,
    SeriesPoint,
)
from b3_selic_pre.infrastructure.tesouro_series_cache import StoredSeries


def _stored(name, latest):
    return StoredSeries(
        name=name,
        points=(
            SeriesPoint(
                latest,
                METRICA_DEMANDA_PCT,
                Decimal("100"),
                Decimal("100"),
                DIMENSAO_FAMILIA,
                SELIC,
            ),
        ),
        latest_data_date=latest,
        source="Cache",
        extracted_at="2026-10-20T00:00:00",
        titles=("Tesouro Selic 2029",),
        source_hashes={},
    )


class FakeSeriesCache:
    def __init__(self, payloads=None):
        self.payloads = payloads or {}

    def expected_hashes(self, name):
        return {"source": "hash"} if name in self.payloads else None

    def read(self, name, expected_hashes=None):
        return self.payloads.get(name)

    def has(self, name):
        return name in self.payloads


def test_loader_reads_snapshots_without_touching_raw_cache():
    client = FakeClient()
    cache = FakeSeriesCache(
        {
            "demanda": _stored("demanda", "2026-10-02"),
            "fluxo": _stored("fluxo", "2026-10-02"),
        }
    )

    data = make_loader(client, KIND_APETITE, series_cache=cache)(True, False)

    assert data is not None
    assert data.provider is not None
    assert data.latest_data_date == "2026-10-02"
    assert client.calls == []


def test_loader_falls_back_to_raw_cache_and_precomputes():
    client = FakeClient()
    cache = FakeSeriesCache()
    calls = []

    data = make_loader(
        client,
        KIND_ESTOQUE,
        series_cache=cache,
        precompute=lambda kind, payload: calls.append((kind, payload)),
    )(True, False)

    assert data is not None
    assert client.calls == ["estoque"]
    assert calls and calls[0][0] == KIND_ESTOQUE


def test_loader_without_any_cache_returns_none():
    client = FakeClient()
    client.read_cached_estoque = lambda: None
    calls = []

    data = make_loader(
        client,
        KIND_ESTOQUE,
        series_cache=FakeSeriesCache(),
        precompute=lambda kind, payload: calls.append(kind),
    )(True, False)

    assert data is None
    assert calls == []


def test_series_available_checks_every_needed_snapshot():
    from b3_selic_pre.presentation.tesouro_series_loader import series_available

    complete = FakeSeriesCache(
        {
            "estoque": _stored("estoque", "2026-10"),
            "demanda": _stored("demanda", "2026-10-02"),
        }
    )
    partial = FakeSeriesCache({"estoque": _stored("estoque", "2026-10")})

    assert series_available(complete, KIND_VISAO_GERAL) is True
    assert series_available(partial, KIND_VISAO_GERAL) is False
    assert series_available(None, KIND_ESTOQUE) is False
