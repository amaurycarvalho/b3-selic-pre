"""Testes dos adaptadores, caches e housekeeping de mercado."""

import io
import json
import math
from datetime import UTC, date, datetime, timedelta

import pytest

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.domain.market import (
    ATIVO_USD,
    UNIDADE_USD,
    MarketQuote,
)
from b3_selic_pre.infrastructure.market import (
    MarketServices,
    build_market_services,
)
from b3_selic_pre.infrastructure.market.b3_client import (
    B3MarketClient,
    normalize_dol,
    parse_dol,
    parse_historical_exchange,
)
from b3_selic_pre.infrastructure.market.bcb_client import (
    BcbFocusClient,
    BcbSgsClient,
    parse_focus,
    parse_sgs,
)
from b3_selic_pre.infrastructure.market.factory import build_market_services as factory
from b3_selic_pre.infrastructure.market.gold_client import (
    GoldUsdClient,
    parse_yahoo,
)
from b3_selic_pre.infrastructure.market.housekeeping import (
    expired,
    run_housekeeping,
    run_precompute_housekeeping,
    run_raw_housekeeping,
)
from b3_selic_pre.infrastructure.market.precompute_cache import (
    MarketPrecomputeCache,
)
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache


class FakeOpener:
    def __init__(self, body=b"", error=None):
        self.body = body
        self.error = error
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append((request, timeout))
        if self.error is not None:
            raise self.error
        return io.BytesIO(self.body)


def _quote(data="2026-10-30", valor=5.42, **overrides):
    values = {
        "data": data,
        "ativo": ATIVO_USD,
        "valor": valor,
        "unidade": UNIDADE_USD,
        "origem": "teste",
        "metodo": "oficial",
        "extraido_em": "2026-10-30T12:00:00+00:00",
    }
    values.update(overrides)
    return MarketQuote(**values)


def test_parse_sgs_and_client_fetch():
    body = json.dumps(
        [
            {"data": "29/10/2026", "valor": "5,40"},
            {"data": "30/10/2026", "valor": "5,42"},
        ]
    ).encode()
    opener = FakeOpener(body)

    quotes = BcbSgsClient(opener=opener).fetch_series(
        "2026-10-29", "2026-10-30"
    )

    assert [quote.valor for quote in quotes] == [5.40, 5.42]
    assert quotes[0].data == "2026-10-29"
    assert "dataInicial=29%2F10%2F2026" in opener.requests[0][0].full_url


def test_parse_sgs_ignores_invalid_rows():
    payload = json.dumps(
        [
            {"data": "30/10/2026", "valor": "x"},
            {"data": "invalida", "valor": "1"},
            "not-a-row",
            {"data": "30/10/2026", "valor": "5,1"},
        ]
    )

    assert len(parse_sgs(payload)) == 1
    assert parse_sgs(b"not-json") == []


def test_sgs_client_uses_bcdata_endpoint_and_series_code():
    opener = FakeOpener(b'[{"data":"30/10/2026","valor":"5,42"}]')

    BcbSgsClient(opener=opener, codigo=13621).fetch_series(
        "2026-10-01", "2026-10-30"
    )

    url = opener.requests[0][0].full_url
    assert "/dados/serie/bcdata.sgs.13621/dados" in url
    assert "dataInicial=01%2F10%2F2026" in url


def test_focus_client_builds_odata_query_without_encoded_dollar():
    body = json.dumps(
        {"value": [{"DataReferencia": "2027", "Mediana": 5.5, "Data": "2026-10-30"}]}
    ).encode()
    opener = FakeOpener(body)

    expectations = BcbFocusClient(opener=opener).fetch_expectations()

    url = opener.requests[0][0].full_url
    assert "%24filter" not in url
    assert "$filter=" in url
    assert "$orderby=Data%20desc" in url
    assert "$top=100" in url
    assert expectations[0].ano == 2027


def test_parse_focus_keeps_latest_row_per_year():
    payload = {
        "value": [
            {
                "Ano": "2027",
                "Mediana": "5.5",
                "Minimo": "5.0",
                "Maximo": "6.0",
                "Data": "2026-10-01",
            },
            {
                "Ano": "2027",
                "Mediana": "5.7",
                "Minimo": "5.1",
                "Maximo": "6.2",
                "Data": "2026-10-30",
            },
            {"Ano": None, "Mediana": "1"},
        ]
    }

    expectations = parse_focus(json.dumps(payload))

    assert len(expectations) == 1
    assert expectations[0].mediana == 5.7
    assert expectations[0].minimo == 5.1


def test_focus_client_fetch():
    body = json.dumps(
        {"value": [{"Ano": 2027, "Mediana": 5.5, "Data": "2026-10-30"}]}
    ).encode()

    expectations = BcbFocusClient(opener=FakeOpener(body)).fetch_expectations()

    assert expectations[0].ano == 2027


def test_b3_normalization_and_parsers():
    assert normalize_dol(5420.0) == pytest.approx(5.42)

    payload = json.dumps(
        [
            {"data": "30/10/2026", "valor": "5,42"},
            {"data": "2026-10-31T00:00:00", "valor": 5.5},
        ]
    )
    history = parse_historical_exchange(payload)

    assert [quote.data for quote in history] == ["2026-10-30", "2026-10-31"]

    dol = parse_dol(json.dumps([{"data": "2026-10-30", "valor": 5420}]))
    assert dol[0].valor == pytest.approx(5.42)


def test_b3_client_fetches_history_and_dol():
    body = json.dumps([{"data": "2026-10-30", "valor": 5420}]).encode()

    history = B3MarketClient(opener=FakeOpener(body)).fetch_historical_exchange(
        "2026-10-01", "2026-10-30"
    )
    dol = B3MarketClient(opener=FakeOpener(body)).fetch_dol(
        "DOLZ26", "2026-10-01", "2026-10-30"
    )

    assert history[0].valor == 5420
    assert dol[0].valor == pytest.approx(5.42)


def test_parse_yahoo_and_failure_returns_empty():
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1761696000, 1761782400],
                    "indicators": {"quote": [{"close": [2000.5, None]}]},
                }
            ]
        }
    }

    quotes = parse_yahoo(json.dumps(payload))

    assert len(quotes) == 1
    assert quotes[0].valor == 2000.5
    assert parse_yahoo(b"not-json") == []


def test_gold_client_network_failure_returns_empty():
    opener = FakeOpener(error=OSError("sem rede"))

    assert GoldUsdClient(opener=opener).fetch_series() == []


def test_gold_client_sets_user_agent():
    body = json.dumps(
        {
            "chart": {
                "result": [
                    {
                        "timestamp": [1761696000],
                        "indicators": {"quote": [{"close": [2000.0]}]},
                    }
                ]
            }
        }
    ).encode()
    opener = FakeOpener(body)

    quotes = GoldUsdClient(opener=opener).fetch_series()

    assert quotes
    assert opener.requests[0][0].get_header("User-agent")


def test_raw_cache_write_read_and_provenance(tmp_path):
    cache = MarketRawCache(tmp_path)
    quote = _quote()

    assert cache.write_quote("bcb_sgs_1", quote)
    payload = cache.read("bcb_sgs_1", "2026-10-30")

    assert payload["fonte"] == "bcb_sgs_1"
    assert payload["unidade"] == UNIDADE_USD
    assert payload["hash"]
    assert cache.read_quote("bcb_sgs_1", "2026-10-30") == quote


def test_raw_cache_never_writes_empty_or_invalid(tmp_path):
    cache = MarketRawCache(tmp_path)

    assert not cache.write_quote("fonte", _quote(valor=math.nan))
    assert not cache.write_quote("fonte", _quote(data="invalida"))
    assert cache.read_series("fonte") == []


def test_raw_cache_ttl_by_recency(tmp_path):
    cache = MarketRawCache(tmp_path, MarketConfig())
    reference = "2026-10-30"

    assert cache.ttl_minutes("2026-10-30", reference) == 20
    assert cache.ttl_minutes("2026-10-20", reference) == 20
    assert cache.ttl_minutes("2026-10-01", reference) == 180
    assert cache.ttl_minutes("2026-08-01", reference) is None
    assert cache.ttl_minutes("2026-08-01", "2027-10-30") is None


def test_raw_cache_freshness_respects_ttl_and_immutability(tmp_path):
    cache = MarketRawCache(tmp_path)
    cache.write_quote("fonte", _quote("2026-10-30", 5.0))
    assert cache.is_fresh("fonte", "2026-10-30", "2026-10-30")

    old = cache.path("fonte", "2026-10-30")
    data = json.loads(old.read_text())
    data["cached_at"] = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    old.write_text(json.dumps(data))
    assert not cache.is_fresh("fonte", "2026-10-30", "2026-10-30")

    cache.write_quote("fonte", _quote("2026-06-30", 5.0))
    old = cache.path("fonte", "2026-06-30")
    data = json.loads(old.read_text())
    data["cached_at"] = "2000-01-01T00:00:00+00:00"
    old.write_text(json.dumps(data))
    assert cache.is_fresh("fonte", "2026-06-30", "2026-10-30")


def test_raw_cache_missing_dates_and_corruption(tmp_path):
    cache = MarketRawCache(tmp_path)
    cache.write_quote("fonte", _quote("2026-10-26", 5.0))
    corrupt = cache.path("fonte", "2026-10-27")
    corrupt.write_text("{corrompido")
    (cache.raw_dir / "fonte" / "not-a-date.json").write_text("{}")

    missing = cache.missing_dates("fonte", "2026-10-24", "2026-10-29")

    assert missing == ["2026-10-28", "2026-10-29"]
    assert cache.read("fonte", "2026-10-27") is None
    assert cache.last_date("fonte") == "2026-10-27"
    assert [quote.data for quote in cache.read_series("fonte")] == [
        "2026-10-26"
    ]


def test_raw_cache_read_only_does_not_modify(tmp_path):
    cache = MarketRawCache(tmp_path)
    cache.write_quote("fonte", _quote("2026-10-26", 5.0))
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert cache.read("fonte", "2026-10-26") is not None
    assert cache.read_series("fonte")
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert before == after


def test_precompute_reuse_invalidation_and_failure(tmp_path):
    cache = MarketPrecomputeCache(tmp_path)
    calls = []

    def build():
        calls.append("build")
        return {"valor": 1}

    assert cache.update_if_changed("a", {"s": "1"}, "2026-10-30", build)
    assert not cache.update_if_changed("a", {"s": "1"}, "2026-10-30", build)
    assert calls == ["build"]
    assert cache.read_artifact("a") == {"valor": 1}

    assert cache.update_if_changed("b", {"s": "2"}, "2026-10-31", build)

    def fail():
        raise RuntimeError("falha")

    assert not cache.update_if_changed("c", {"s": "3"}, "2026-11-01", fail)
    assert cache.read_artifact("a") == {"valor": 1}
    assert cache.read_artifact("b") == {"valor": 1}

    assert not cache.update_if_changed("d", {"s": "4"}, "2026-11-01", lambda: None)


def test_precompute_derived_and_manifest(tmp_path):
    cache = MarketPrecomputeCache(tmp_path)
    cache.write_derived("k", {"buckets": []}, {"s": "1"}, "2026-10-30")

    assert cache.read_derived("k") == {"buckets": []}
    manifest = cache.load_manifest()
    assert manifest["latest_data_date"] == "2026-10-30"
    assert "k" in manifest["keys"]
    assert cache.stale_keys("other") == ["k"]


def test_housekeeping_removes_old_and_keeps_recent(tmp_path):
    cache = MarketRawCache(tmp_path)
    for day in ("2019-01-01", "2026-10-30"):
        cache.write_quote("fonte", _quote(day, 5.0))
    corrupt = cache.raw_dir / "fonte" / "corrompida.json"
    corrupt.write_text("{}")

    removed = run_raw_housekeeping(cache, "2026-10-30")

    assert any("2019-01-01" in item for item in removed)
    assert cache.read("fonte", "2026-10-30") is not None
    assert corrupt.exists()


def test_housekeeping_precompute_and_relative_reference(tmp_path):
    cache = MarketPrecomputeCache(tmp_path)
    cache.write_artifact("old", {}, {"s": "1"}, "2019-01-01")
    cache.write_artifact("new", {}, {"s": "1"}, "2026-10-30")

    removed = run_precompute_housekeeping(cache, "2026-10-30")

    assert removed == ["old"]
    assert cache.read_artifact("new") == {}
    assert cache.read_artifact("old") is None


def test_housekeeping_expired_and_shift_year(tmp_path):
    assert expired("2019-01-01", "2026-10-30")
    assert not expired("2026-10-30", "2026-10-30")
    assert not expired("invalida", "2026-10-30")
    assert not expired("2019-01-01", "invalida")
    result = run_housekeeping(tmp_path, "2026-10-30")
    assert set(result) == {"raw", "precomputed"}


def test_factory_wires_fake_adapters_without_network(tmp_path):
    services = build_market_services(
        tmp_path,
        sgs=object(),
        focus=object(),
        b3=object(),
        gold=object(),
    )

    assert isinstance(services, MarketServices)
    assert services.raw.cache_dir == tmp_path
    assert services.precompute.cache_dir == tmp_path
    assert factory(tmp_path).raw.cache_dir == tmp_path


def test_factory_default_adapters_are_offline_safe():
    services = build_market_services("/tmp/nao-usado")
    assert services.sgs is not None
    assert services.focus is not None
    assert services.b3 is not None
    assert services.gold is not None
