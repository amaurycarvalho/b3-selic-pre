"""Testes dos adaptadores, snapshot, cache e housekeeping de reservas."""

import io
import json
from datetime import UTC, datetime, timedelta

from b3_selic_pre.application.reserves.config import ReservesConfig
from b3_selic_pre.application.reserves.series import (
    points_hash,
    snapshot_hash,
)
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import FONTE_RESERVAS, UNIDADE_RESERVAS
from b3_selic_pre.infrastructure.market.precompute_cache import (
    MarketPrecomputeCache,
)
from b3_selic_pre.infrastructure.market.raw_cache import MarketRawCache
from b3_selic_pre.infrastructure.reserves import build_reserves_services
from b3_selic_pre.infrastructure.reserves.adapter import BcbReservesClient
from b3_selic_pre.infrastructure.reserves.factory import RESERVES_NAMESPACE

SOURCE = "bcb_sgs_13621"


class FakeOpener:
    def __init__(self, body=b""):
        self.body = body
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append((request, timeout))
        return io.BytesIO(self.body)


def _quote(day: str, value: float, extraido="2026-10-30T12:00:00+00:00"):
    return MarketQuote(
        data=day,
        ativo="reservas",
        valor=value,
        unidade=UNIDADE_RESERVAS,
        origem=FONTE_RESERVAS,
        metodo="oficial",
        extraido_em=extraido,
    )


def test_reserves_client_uses_sgs_13621_and_parses_fixture():
    body = json.dumps(
        [
            {"data": "29/10/2026", "valor": "364540,0"},
            {"data": "30/10/2026", "valor": "365000,0"},
        ]
    ).encode()
    opener = FakeOpener(body)

    quotes = BcbReservesClient(
        opener=opener, sleep=lambda _: None
    ).fetch_series("2026-10-29", "2026-10-30")

    url = opener.requests[0][0].full_url
    assert "/bcdata.sgs.13621/dados" in url
    assert "dataInicial=29%2F10%2F2026" in url
    assert [quote.valor for quote in quotes] == [364540.0, 365000.0]
    assert quotes[0].unidade == UNIDADE_RESERVAS
    assert quotes[0].origem == FONTE_RESERVAS


def test_snapshot_roundtrip_and_no_unnecessary_rewrite(tmp_path):
    cache = MarketRawCache(tmp_path)
    points = [_quote("2026-10-29", 1.0), _quote("2026-10-30", 2.0)]

    assert cache.write_snapshot(SOURCE, points, source=FONTE_RESERVAS)
    assert not cache.write_snapshot(SOURCE, points, source=FONTE_RESERVAS)
    assert cache.snapshot_last_date(SOURCE) == "2026-10-30"

    payload = cache.read_snapshot(SOURCE)
    assert payload["source"] == FONTE_RESERVAS
    assert payload["unit"] == UNIDADE_RESERVAS
    assert payload["hash"] == points_hash(points)
    assert payload["points"][-1] == {"date": "2026-10-30", "value": 2.0}
    assert [point.valor for point in cache.read_snapshot_points(SOURCE)] == [
        1.0,
        2.0,
    ]


def test_snapshot_rewrites_only_when_pairs_change(tmp_path):
    cache = MarketRawCache(tmp_path)
    first = [_quote("2026-10-30", 1.0)]
    cache.write_snapshot(SOURCE, first, source=FONTE_RESERVAS)

    same = [_quote("2026-10-30", 1.0, extraido="2026-10-31T00:00:00+00:00")]
    assert not cache.write_snapshot(SOURCE, same, source=FONTE_RESERVAS)

    revised = [_quote("2026-10-30", 1.5)]
    assert cache.write_snapshot(SOURCE, revised, source=FONTE_RESERVAS)
    assert cache.read_snapshot_points(SOURCE)[0].valor == 1.5


def test_snapshot_ttl_and_freshness_by_recency(tmp_path):
    cache = MarketRawCache(tmp_path, ReservesConfig())
    cache.write_snapshot(
        SOURCE,
        [_quote("2026-10-30", 1.0)],
        source=FONTE_RESERVAS,
    )

    assert cache.snapshot_ttl_minutes(SOURCE, "2026-10-30") == 20
    assert cache.snapshot_ttl_minutes(SOURCE, "2026-12-30") is None
    assert cache.is_snapshot_fresh(SOURCE, "2026-10-30")

    target = cache.snapshot_path(SOURCE)
    data = json.loads(target.read_text())
    data["cached_at"] = (
        datetime.now(UTC) - timedelta(hours=2)
    ).isoformat()
    target.write_text(json.dumps(data))
    assert not cache.is_snapshot_fresh(SOURCE, "2026-10-30")


def test_prune_snapshot_removes_only_old_points(tmp_path):
    cache = MarketRawCache(tmp_path)
    cache.write_snapshot(
        SOURCE,
        [_quote("2019-01-01", 1.0), _quote("2026-10-30", 2.0)],
        source=FONTE_RESERVAS,
    )
    config = ReservesConfig()
    before = snapshot_hash(
        cache.read_snapshot_points(SOURCE), config, reference="2026-10-30"
    )

    removed = cache.prune_snapshot(SOURCE, "2026-10-30", 3)

    assert removed == ["2019-01-01"]
    assert [point.data for point in cache.read_snapshot_points(SOURCE)] == [
        "2026-10-30"
    ]
    assert (
        snapshot_hash(
            cache.read_snapshot_points(SOURCE),
            config,
            reference="2026-10-30",
        )
        == before
    )


def test_prune_snapshot_ignores_corruption(tmp_path):
    cache = MarketRawCache(tmp_path)
    target = cache.snapshot_path(SOURCE)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{corrompido")

    assert cache.prune_snapshot(SOURCE, "2026-10-30") == []
    assert cache.read_snapshot(SOURCE) is None


def test_precompute_namespace_paths_and_reuse(tmp_path):
    cache = MarketPrecomputeCache(tmp_path, namespace=RESERVES_NAMESPACE)
    calls = []

    def build():
        calls.append(1)
        return {"valor": 1}

    assert cache.update_if_changed("k", {"s": "1"}, "2026-10-30", build)
    assert not cache.update_if_changed("k", {"s": "1"}, "2026-10-30", build)
    assert calls == [1]
    assert RESERVES_NAMESPACE in str(cache.artifact_path("k"))
    assert cache.manifest_path == tmp_path / RESERVES_NAMESPACE / "manifest.json"
    assert cache.read_artifact("k") == {"valor": 1}


def test_factory_wires_fake_source_without_network(tmp_path):
    source = object()
    services = build_reserves_services(tmp_path, source=source)

    assert services.source is source
    assert services.raw.cache_dir == tmp_path
    assert services.precompute.namespace == RESERVES_NAMESPACE
    assert services.precompute.cache_dir == tmp_path


def test_factory_default_adapters_are_offline_safe():
    services = build_reserves_services("/tmp/nao-usado-reservas")

    assert services.source is not None
    assert services.raw is not None
    assert services.precompute is not None
