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
